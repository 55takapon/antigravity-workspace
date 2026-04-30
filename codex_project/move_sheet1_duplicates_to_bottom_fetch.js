const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_NAME = 'シート1';
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

async function main() {
  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, '?fields=properties.title,sheets.properties.title');
  if (!metadata.sheets.some((sheet) => sheet.properties.title === SHEET_NAME)) {
    throw new Error(`Sheet not found: ${SHEET_NAME}`);
  }

  const quoted = quoteSheetName(SHEET_NAME);
  const current = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!A2:I`)}`);
  const rows = (current.values || []).map((row) => padRow(row, WIDTH));

  const nonDuplicates = [];
  const duplicates = [];
  for (const row of rows) {
    if (row[6] === DUPLICATE_LABEL) duplicates.push(row);
    else nonDuplicates.push(row);
  }

  const sorted = [...nonDuplicates, ...duplicates];
  await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!A2:I${sorted.length + 1}`)}?valueInputOption=RAW`, {
    method: 'PUT',
    body: JSON.stringify({ values: sorted }),
  });

  const verifyStart = nonDuplicates.length + 2;
  const verify = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!G${verifyStart}:G${sorted.length + 1}`)}`);
  const verifiedDuplicateRows = (verify.values || []).filter((row) => row[0] === DUPLICATE_LABEL).length;

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.properties.title,
    sheetName: SHEET_NAME,
    totalRows: rows.length,
    nonDuplicateRows: nonDuplicates.length,
    duplicateRows: duplicates.length,
    firstDuplicateOutputRow: verifyStart,
    lastDuplicateOutputRow: sorted.length + 1,
    verifiedDuplicateRowsAtBottom: verifiedDuplicateRows,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
