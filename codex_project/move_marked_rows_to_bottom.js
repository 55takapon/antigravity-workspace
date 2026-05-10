const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const SHEET_NAME = '\u30b7\u30fc\u30c81';
const DRY_RUN = process.argv.includes('--dry-run');

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

function isMarked(row) {
  const h = (row[7] || '').trim();
  const i = (row[8] || '').trim();
  return (h === '\u2715' || h === '\u00d7') && i !== '';
}

async function main() {
  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, '?fields=properties.title,sheets.properties');
  const sheet = metadata.sheets.find((entry) => entry.properties.title === SHEET_NAME);
  if (!sheet) throw new Error(`Sheet not found: ${SHEET_NAME}`);

  const sheetId = sheet.properties.sheetId;
  const columnCount = sheet.properties.gridProperties.columnCount || 29;
  const data = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoteSheetName(SHEET_NAME)}!A:AC`)}`);
  const values = data.values || [];
  const lastDataRow = values.length;
  const markedRows = [];
  const unmarkedRows = [];

  values.forEach((row, index) => {
    const rowNumber = index + 1;
    if (rowNumber === 1) return;
    if (isMarked(row)) {
      markedRows.push(rowNumber);
    } else {
      unmarkedRows.push(rowNumber);
    }
  });

  if (DRY_RUN) {
    console.log(JSON.stringify({
      mode: 'dry-run',
      spreadsheetTitle: metadata.properties.title,
      sheet: SHEET_NAME,
      lastDataRow,
      targetRows: markedRows.length,
      rowsRemainingAbove: unmarkedRows.length,
      firstTargetRows: markedRows.slice(0, 10),
      lastTargetRows: markedRows.slice(-10),
    }, null, 2));
    return;
  }

  if (markedRows.length === 0) {
    console.log(JSON.stringify({ mode: 'applied', movedRows: 0 }, null, 2));
    return;
  }

  const requiredRows = lastDataRow + markedRows.length;
  const gridRows = sheet.properties.gridProperties.rowCount || 0;
  const requests = [];

  if (gridRows < requiredRows) {
    requests.push({
      updateSheetProperties: {
        properties: {
          sheetId,
          gridProperties: { rowCount: requiredRows },
        },
        fields: 'gridProperties.rowCount',
      },
    });
  }

  markedRows.forEach((rowNumber, index) => {
    const destinationRowIndex = lastDataRow + index;
    requests.push({
      copyPaste: {
        source: {
          sheetId,
          startRowIndex: rowNumber - 1,
          endRowIndex: rowNumber,
          startColumnIndex: 0,
          endColumnIndex: columnCount,
        },
        destination: {
          sheetId,
          startRowIndex: destinationRowIndex,
          endRowIndex: destinationRowIndex + 1,
          startColumnIndex: 0,
          endColumnIndex: columnCount,
        },
        pasteType: 'PASTE_NORMAL',
      },
    });
  });

  markedRows.slice().sort((a, b) => b - a).forEach((rowNumber) => {
    requests.push({
      deleteDimension: {
        range: {
          sheetId,
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

  const verify = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoteSheetName(SHEET_NAME)}!A:AC`)}`);
  const verifyValues = verify.values || [];
  const afterLastDataRow = verifyValues.length;
  const boundary = afterLastDataRow - markedRows.length;
  const markedAboveBoundary = [];
  const unmarkedInBottomBlock = [];

  verifyValues.forEach((row, index) => {
    const rowNumber = index + 1;
    if (rowNumber === 1) return;
    if (rowNumber <= boundary && isMarked(row)) markedAboveBoundary.push(rowNumber);
    if (rowNumber > boundary && !isMarked(row)) unmarkedInBottomBlock.push(rowNumber);
  });

  console.log(JSON.stringify({
    mode: 'applied',
    movedRows: markedRows.length,
    lastDataRowBefore: lastDataRow,
    lastDataRowAfter: afterLastDataRow,
    bottomBlockStartRow: boundary + 1,
    markedAboveBoundary: markedAboveBoundary.slice(0, 20),
    markedAboveBoundaryCount: markedAboveBoundary.length,
    unmarkedInBottomBlock: unmarkedInBottomBlock.slice(0, 20),
    unmarkedInBottomBlockCount: unmarkedInBottomBlock.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
