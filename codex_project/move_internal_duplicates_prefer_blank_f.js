const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const SOURCE_SHEET_NAME = '\u30b7\u30fc\u30c81';
const DUPLICATE_SHEET_NAME = '\u91cd\u8907\u5206';
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

function normText(value) {
  return (value || '').trim().replace(/\s+/g, '').toLowerCase();
}

function normUrl(value) {
  return (value || '').trim().replace(/\/+$/, '').toLowerCase();
}

function hasHttpUrl(value) {
  return /https?:\/\//i.test(value || '');
}

function fRank(row) {
  const f = (row[5] || '').trim();
  if (hasHttpUrl(f)) return 0;
  if (f !== '') return 1;
  return 2;
}

function buildDuplicatePlan(values) {
  const groups = new Map();
  values.forEach((row, index) => {
    const rowNumber = index + 1;
    if (rowNumber === 1) return;
    const company = normText(row[2]);
    const url = normUrl(row[4]);
    if (!company || !url) return;
    const key = `${company}\u0000${url}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({ rowNumber, row });
  });

  const duplicateGroups = [...groups.values()].filter((group) => group.length > 1);
  const moveRows = [];
  const keepRows = [];
  duplicateGroups.forEach((group) => {
    const sorted = group.slice().sort((a, b) => {
      const rankDiff = fRank(a.row) - fRank(b.row);
      if (rankDiff !== 0) return rankDiff;
      return a.rowNumber - b.rowNumber;
    });
    keepRows.push(sorted[0].rowNumber);
    sorted.slice(1).forEach((entry) => moveRows.push(entry.rowNumber));
  });

  return {
    duplicateGroups,
    keepRows,
    moveRows: moveRows.sort((a, b) => a - b),
  };
}

async function getMetadata(token) {
  return sheetsFetch(token, '?fields=properties.title,sheets.properties');
}

async function getValues(token, sheetName) {
  const range = `${quoteSheetName(sheetName)}!A:AC`;
  const data = await sheetsFetch(token, `/values/${encodeURIComponent(range)}`);
  return data.values || [];
}

async function getLastDataRow(token, sheetName) {
  return (await getValues(token, sheetName)).length;
}

async function main() {
  const token = await getAccessToken();
  let metadata = await getMetadata(token);
  const source = metadata.sheets.find((sheet) => sheet.properties.title === SOURCE_SHEET_NAME);
  if (!source) throw new Error(`Source sheet not found: ${SOURCE_SHEET_NAME}`);
  let duplicate = metadata.sheets.find((sheet) => sheet.properties.title === DUPLICATE_SHEET_NAME);
  if (!duplicate) throw new Error(`Duplicate sheet not found: ${DUPLICATE_SHEET_NAME}`);

  const values = await getValues(token, SOURCE_SHEET_NAME);
  const plan = buildDuplicatePlan(values);
  const blankFMoveRows = plan.moveRows.filter((rowNumber) => ((values[rowNumber - 1] || [])[5] || '').trim() === '');
  const nonUrlFMoveRows = plan.moveRows.filter((rowNumber) => {
    const f = ((values[rowNumber - 1] || [])[5] || '').trim();
    return f !== '' && !hasHttpUrl(f);
  });
  const urlFMoveRows = plan.moveRows.filter((rowNumber) => hasHttpUrl(((values[rowNumber - 1] || [])[5] || '').trim()));

  if (DRY_RUN) {
    console.log(JSON.stringify({
      mode: 'dry-run',
      spreadsheetTitle: metadata.properties.title,
      sourceSheet: SOURCE_SHEET_NAME,
      sourceRows: values.length,
      duplicateGroups: plan.duplicateGroups.length,
      rowsToMove: plan.moveRows.length,
      blankFToMove: blankFMoveRows.length,
      nonUrlFToMove: nonUrlFMoveRows.length,
      urlFToMove: urlFMoveRows.length,
      firstRowsToMove: plan.moveRows.slice(0, 20),
      lastRowsToMove: plan.moveRows.slice(-20),
      samples: plan.moveRows.slice(0, 20).map((rowNumber) => {
        const row = values[rowNumber - 1] || [];
        return { row: rowNumber, company: row[2] || '', url: row[4] || '', f: row[5] || '' };
      }),
    }, null, 2));
    return;
  }

  if (plan.moveRows.length === 0) {
    console.log(JSON.stringify({ mode: 'applied', movedRows: 0 }, null, 2));
    return;
  }

  const sourceSheetId = source.properties.sheetId;
  const duplicateSheetId = duplicate.properties.sheetId;
  const columnCount = source.properties.gridProperties.columnCount || 29;
  const duplicateLastRow = await getLastDataRow(token, DUPLICATE_SHEET_NAME);
  const requiredDuplicateRows = duplicateLastRow + plan.moveRows.length;
  const duplicateGridRows = duplicate.properties.gridProperties.rowCount || 0;
  const requests = [];

  if (duplicateGridRows < requiredDuplicateRows) {
    requests.push({
      updateSheetProperties: {
        properties: {
          sheetId: duplicateSheetId,
          gridProperties: { rowCount: requiredDuplicateRows },
        },
        fields: 'gridProperties.rowCount',
      },
    });
  }

  plan.moveRows.forEach((rowNumber, index) => {
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

  plan.moveRows.slice().sort((a, b) => b - a).forEach((rowNumber) => {
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
  const afterPlan = buildDuplicatePlan(afterValues);
  const afterDuplicateLastRow = await getLastDataRow(token, DUPLICATE_SHEET_NAME);

  console.log(JSON.stringify({
    mode: 'applied',
    movedRows: plan.moveRows.length,
    blankFToMove: blankFMoveRows.length,
    nonUrlFToMove: nonUrlFMoveRows.length,
    urlFToMove: urlFMoveRows.length,
    sourceRowsBefore: values.length,
    sourceRowsAfter: afterValues.length,
    duplicateRowsBefore: duplicateLastRow,
    duplicateRowsAfter: afterDuplicateLastRow,
    remainingDuplicateGroupsByCompanyUrl: afterPlan.duplicateGroups.length,
    remainingRowsToMoveByCompanyUrl: afterPlan.moveRows.length,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
