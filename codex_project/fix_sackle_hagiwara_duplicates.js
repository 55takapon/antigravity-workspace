const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const SOURCE_SHEET_NAME = '\u30b7\u30fc\u30c81';
const DUPLICATE_SHEET_NAME = '\u91cd\u8907\u5206';
const DRY_RUN = process.argv.includes('--dry-run');

const fixes = [
  { row: 631, company: '\u682a\u5f0f\u4f1a\u793e\u30b5\u30c3\u30af\u30eb', url: 'https://sackle.co.jp/' },
  { row: 655, company: '\u8429\u539f\u5370\u5237\u682a\u5f0f\u4f1a\u793e', url: 'http://www.hg-prt.co.jp/' },
];
const duplicateRows = [2160, 2784];

function base64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

async function getAccessToken() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'RS256', typ: 'JWT' };
  const claim = {
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
  };
  const signingInput = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(claim))}`;
  const signature = crypto.sign('RSA-SHA256', Buffer.from(signingInput), credentials.private_key);
  const assertion = `${signingInput}.${base64url(signature)}`;
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion,
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(data));
  return data.access_token;
}

async function sheetsFetch(token, path, options = {}) {
  const response = await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(data));
  return data;
}

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

async function getValues(token, sheetName) {
  const range = `${quoteSheetName(sheetName)}!A:AC`;
  const data = await sheetsFetch(token, `/values/${encodeURIComponent(range)}`);
  return data.values || [];
}

async function getMetadata(token) {
  return sheetsFetch(token, '?fields=properties.title,sheets.properties');
}

async function main() {
  const token = await getAccessToken();
  let metadata = await getMetadata(token);
  const source = metadata.sheets.find((sheet) => sheet.properties.title === SOURCE_SHEET_NAME);
  const duplicate = metadata.sheets.find((sheet) => sheet.properties.title === DUPLICATE_SHEET_NAME);
  if (!source) throw new Error(`Source sheet not found: ${SOURCE_SHEET_NAME}`);
  if (!duplicate) throw new Error(`Duplicate sheet not found: ${DUPLICATE_SHEET_NAME}`);

  const values = await getValues(token, SOURCE_SHEET_NAME);
  const before = [...fixes.map((fix) => fix.row), ...duplicateRows].map((rowNumber) => {
    const row = values[rowNumber - 1] || [];
    return {
      row: rowNumber,
      company: row[2] || '',
      url: row[4] || '',
      formUrl: row[5] || '',
    };
  });

  fixes.forEach((fix) => {
    const row = values[fix.row - 1] || [];
    if ((row[2] || '') !== fix.company) {
      throw new Error(`Unexpected company at row ${fix.row}: ${row[2] || ''}`);
    }
  });

  if (DRY_RUN) {
    console.log(JSON.stringify({
      mode: 'dry-run',
      spreadsheetTitle: metadata.properties.title,
      before,
      fixes,
      duplicateRows,
    }, null, 2));
    return;
  }

  await sheetsFetch(token, '/values:batchUpdate', {
    method: 'POST',
    body: JSON.stringify({
      valueInputOption: 'RAW',
      data: fixes.map((fix) => ({
        range: `${quoteSheetName(SOURCE_SHEET_NAME)}!E${fix.row}`,
        values: [[fix.url]],
      })),
    }),
  });

  const sourceSheetId = source.properties.sheetId;
  const duplicateSheetId = duplicate.properties.sheetId;
  const columnCount = source.properties.gridProperties.columnCount || 29;
  const duplicateLastRow = (await getValues(token, DUPLICATE_SHEET_NAME)).length;
  const duplicateGridRows = duplicate.properties.gridProperties.rowCount || 0;
  const requests = [];

  if (duplicateGridRows < duplicateLastRow + duplicateRows.length) {
    requests.push({
      updateSheetProperties: {
        properties: {
          sheetId: duplicateSheetId,
          gridProperties: { rowCount: duplicateLastRow + duplicateRows.length },
        },
        fields: 'gridProperties.rowCount',
      },
    });
  }

  duplicateRows.slice().sort((a, b) => a - b).forEach((rowNumber, index) => {
    const destinationRow = duplicateLastRow + index;
    requests.push({
      copyPaste: {
        source: {
          sheetId: sourceSheetId,
          startRowIndex: rowNumber - 1,
          endRowIndex: rowNumber,
          startColumnIndex: 0,
          endColumnIndex: columnCount,
        },
        destination: {
          sheetId: duplicateSheetId,
          startRowIndex: destinationRow,
          endRowIndex: destinationRow + 1,
          startColumnIndex: 0,
          endColumnIndex: columnCount,
        },
        pasteType: 'PASTE_NORMAL',
      },
    });
  });

  duplicateRows.slice().sort((a, b) => b - a).forEach((rowNumber) => {
    requests.push({
      deleteDimension: {
        range: {
          sheetId: sourceSheetId,
          dimension: 'ROWS',
          startIndex: rowNumber - 1,
          endIndex: rowNumber,
        },
      },
    });
  });

  await sheetsFetch(token, ':batchUpdate', {
    method: 'POST',
    body: JSON.stringify({ requests }),
  });

  const afterValues = await getValues(token, SOURCE_SHEET_NAME);
  const afterDuplicateRows = (await getValues(token, DUPLICATE_SHEET_NAME)).length;
  const after = fixes.map((fix) => {
    const row = afterValues[fix.row - 1] || [];
    return {
      row: fix.row,
      company: row[2] || '',
      url: row[4] || '',
      formUrl: row[5] || '',
    };
  });

  console.log(JSON.stringify({
    mode: 'applied',
    before,
    after,
    movedRows: duplicateRows,
    sourceRowsBefore: values.length,
    sourceRowsAfter: afterValues.length,
    duplicateRowsBefore: duplicateLastRow,
    duplicateRowsAfter: afterDuplicateRows,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
