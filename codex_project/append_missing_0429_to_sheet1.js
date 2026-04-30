const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_NAME = 'シート1';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const TSV_PATH = 'web_kanji_missing_0429_rows.tsv';
const START_ROW = 7316;
const WIDTH = 9;

function base64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

function parseTsv(text) {
  return text.replace(/^\uFEFF/, '').replace(/\r?\n$/, '').split(/\r?\n/).map((line) => line.split('\t'));
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
  if (!response.ok) {
    throw new Error(JSON.stringify(data));
  }
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
  if (!response.ok) {
    throw new Error(JSON.stringify(data));
  }
  return data;
}

async function main() {
  const values = parseTsv(fs.readFileSync(TSV_PATH, 'utf8'));
  for (const [index, row] of values.entries()) {
    if (row.length !== WIDTH) throw new Error(`Unexpected width at TSV row ${index + 1}: ${row.length}`);
  }

  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, '?fields=properties.title,sheets.properties');
  const sheet = metadata.sheets.find((s) => s.properties.title === SHEET_NAME);
  if (!sheet) throw new Error(`Sheet not found: ${SHEET_NAME}`);

  const quoted = quoteSheetName(SHEET_NAME);
  const requiredRows = START_ROW + values.length - 1;
  const currentRows = sheet.properties.gridProperties.rowCount || 0;
  if (currentRows >= START_ROW) {
    const checkEndRow = Math.min(currentRows, START_ROW + values.length + 25);
    const tail = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!A${START_ROW}:I${checkEndRow}`)}`);
    const occupied = (tail.values || []).some((row) => row.some((cell) => String(cell || '').trim() !== ''));
    if (occupied) {
      throw new Error(`Refusing to write: ${SHEET_NAME}!A${START_ROW}:I${checkEndRow} is not empty`);
    }
  }

  if (currentRows < requiredRows) {
    await sheetsFetch(token, ':batchUpdate', {
      method: 'POST',
      body: JSON.stringify({
        requests: [{
          updateSheetProperties: {
            properties: {
              sheetId: sheet.properties.sheetId,
              gridProperties: { rowCount: requiredRows },
            },
            fields: 'gridProperties.rowCount',
          },
        }],
      }),
    });
  }

  await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!A${START_ROW}`)}?valueInputOption=RAW`, {
    method: 'PUT',
    body: JSON.stringify({ values }),
  });

  const verify = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!A${START_ROW}:I${requiredRows}`)}`);
  console.log(JSON.stringify({
    spreadsheetTitle: metadata.properties.title,
    sheetName: SHEET_NAME,
    startRow: START_ROW,
    endRow: requiredRows,
    writtenRows: values.length,
    verifiedRows: verify.values ? verify.values.length : 0,
    first: values[0],
    last: values[values.length - 1],
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
