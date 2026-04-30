const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SOURCE_SHEET = 'シート1';
const DUPLICATE_SHEET = '重複分';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const DUPLICATE_LABEL = '重複';
const WIDTH = 9;

function base64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

function padRow(row, width) {
  const next = row ? [...row] : [];
  while (next.length < width) next.push('');
  return next.slice(0, width);
}

async function getAccessToken() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const now = Math.floor(Date.now() / 1000);
  const signingInput = `${base64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }))}.${base64url(JSON.stringify({
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
  }))}`;
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

async function updateValues(token, sheetName, rows) {
  const quoted = quoteSheetName(sheetName);
  await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!A1:I${rows.length}`)}?valueInputOption=RAW`, {
    method: 'PUT',
    body: JSON.stringify({ values: rows }),
  });
}

async function clearTail(token, sheetName, startRow, endRow) {
  if (startRow > endRow) return;
  const quoted = quoteSheetName(sheetName);
  await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!A${startRow}:I${endRow}`)}:clear`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

async function main() {
  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, '?fields=properties.title,sheets.properties');
  const source = metadata.sheets.find((sheet) => sheet.properties.title === SOURCE_SHEET);
  const duplicate = metadata.sheets.find((sheet) => sheet.properties.title === DUPLICATE_SHEET);
  if (!source) throw new Error(`Sheet not found: ${SOURCE_SHEET}`);
  if (!duplicate) throw new Error(`Sheet not found: ${DUPLICATE_SHEET}`);

  const sourceQuoted = quoteSheetName(SOURCE_SHEET);
  const current = await sheetsFetch(token, `/values/${encodeURIComponent(`${sourceQuoted}!A1:I`)}`);
  const allRows = current.values || [];
  if (allRows.length < 2) throw new Error(`${SOURCE_SHEET} has no data rows`);

  const header = padRow(allRows[0], WIDTH);
  const dataRows = allRows.slice(1).map((row) => padRow(row, WIDTH));
  const nonDuplicateRows = [];
  const duplicateRows = [];
  for (const row of dataRows) {
    if (row[6] === DUPLICATE_LABEL) duplicateRows.push(row);
    else nonDuplicateRows.push(row);
  }

  const sourceRows = [header, ...nonDuplicateRows];
  const duplicateSheetRows = [header, ...duplicateRows];
  const originalRows = allRows.length;

  await updateValues(token, SOURCE_SHEET, sourceRows);
  await clearTail(token, SOURCE_SHEET, sourceRows.length + 1, originalRows);

  await updateValues(token, DUPLICATE_SHEET, duplicateSheetRows);
  await clearTail(token, DUPLICATE_SHEET, duplicateSheetRows.length + 1, originalRows);

  await sheetsFetch(token, ':batchUpdate', {
    method: 'POST',
    body: JSON.stringify({
      requests: [
        {
          updateSheetProperties: {
            properties: {
              sheetId: source.properties.sheetId,
              gridProperties: { rowCount: Math.max(sourceRows.length, 1) },
            },
            fields: 'gridProperties.rowCount',
          },
        },
        {
          updateSheetProperties: {
            properties: {
              sheetId: duplicate.properties.sheetId,
              gridProperties: { rowCount: Math.max(duplicateSheetRows.length, 1) },
            },
            fields: 'gridProperties.rowCount',
          },
        },
      ],
    }),
  });

  const verifySource = await sheetsFetch(token, `/values/${encodeURIComponent(`${sourceQuoted}!G2:G${sourceRows.length}`)}`);
  const duplicateQuoted = quoteSheetName(DUPLICATE_SHEET);
  const verifyDuplicate = await sheetsFetch(token, `/values/${encodeURIComponent(`${duplicateQuoted}!G2:G${duplicateSheetRows.length}`)}`);
  const sourceDuplicateCount = (verifySource.values || []).filter((row) => row[0] === DUPLICATE_LABEL).length;
  const duplicateSheetDuplicateCount = (verifyDuplicate.values || []).filter((row) => row[0] === DUPLICATE_LABEL).length;

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.properties.title,
    sourceSheet: SOURCE_SHEET,
    duplicateSheet: DUPLICATE_SHEET,
    originalDataRows: dataRows.length,
    sourceRemainingDataRows: nonDuplicateRows.length,
    duplicateSheetDataRows: duplicateRows.length,
    sourceTotalRowsWithHeader: sourceRows.length,
    duplicateTotalRowsWithHeader: duplicateSheetRows.length,
    sourceDuplicateRowsAfterSplit: sourceDuplicateCount,
    duplicateRowsVerified: duplicateSheetDuplicateCount,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
