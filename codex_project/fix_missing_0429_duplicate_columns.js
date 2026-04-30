const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_NAME = 'シート1';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const CANDIDATES_CSV = 'web_kanji_missing_0429_duplicate_candidates.csv';
const START_ROW = 7316;
const END_ROW = 8657;
const DUPLICATE_LABEL = '重複';
const NG_MARK = '✕';

function base64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  text = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      row.push(field);
      field = '';
    } else if (ch === '\n') {
      row.push(field);
      rows.push(row);
      row = [];
      field = '';
    } else if (ch !== '\r') {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
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
  const csvRows = parseCsv(fs.readFileSync(CANDIDATES_CSV, 'utf8'));
  const header = csvRows.shift();
  const rowIndex = header.indexOf('kanji_sheet_row');
  if (rowIndex === -1) throw new Error('kanji_sheet_row column not found');

  const duplicateRows = new Set();
  for (const row of csvRows) {
    const rowNumber = Number(row[rowIndex]);
    if (!Number.isInteger(rowNumber) || rowNumber < START_ROW || rowNumber > END_ROW) {
      throw new Error(`Unexpected target row: ${row[rowIndex]}`);
    }
    duplicateRows.add(rowNumber);
  }

  const values = [];
  for (let rowNumber = START_ROW; rowNumber <= END_ROW; rowNumber += 1) {
    values.push(duplicateRows.has(rowNumber) ? [DUPLICATE_LABEL, NG_MARK, DUPLICATE_LABEL] : ['', '', '']);
  }

  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, '?fields=properties.title,sheets.properties.title');
  if (!metadata.sheets.some((sheet) => sheet.properties.title === SHEET_NAME)) {
    throw new Error(`Sheet not found: ${SHEET_NAME}`);
  }

  const quoted = quoteSheetName(SHEET_NAME);
  await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!G${START_ROW}:I${END_ROW}`)}?valueInputOption=RAW`, {
    method: 'PUT',
    body: JSON.stringify({ values }),
  });

  const verify = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!G${START_ROW}:I${END_ROW}`)}`);
  const verifiedRows = verify.values || [];
  const marked = verifiedRows.filter((row) => row[0] === DUPLICATE_LABEL && row[1] === NG_MARK && row[2] === DUPLICATE_LABEL).length;
  const remainingDates = verifiedRows.filter((row) => row.some((cell) => String(cell || '').includes('2026/04/29'))).length;

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.properties.title,
    sheetName: SHEET_NAME,
    updatedRange: `G${START_ROW}:I${END_ROW}`,
    totalRowsUpdated: values.length,
    duplicateRows: duplicateRows.size,
    verifiedDuplicateRows: marked,
    remainingTimestampRowsInGI: remainingDates,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
