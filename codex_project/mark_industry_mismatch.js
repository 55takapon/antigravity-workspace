const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const SHEET_NAME = '\u30b7\u30fc\u30c81';
const TARGET_LABEL = '\u696d\u7a2e\u9055\u3044';
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

async function main() {
  const token = await getAccessToken();
  const range = `${quoteSheetName(SHEET_NAME)}!A:O`;
  const data = await sheetsFetch(token, `/values/${encodeURIComponent(range)}`);
  const values = data.values || [];
  const targetRows = [];

  values.forEach((row, index) => {
    const rowNumber = index + 1;
    if (rowNumber === 1) return;
    const columnO = (row[14] || '').trim();
    if (columnO === TARGET_LABEL) {
      targetRows.push(rowNumber);
    }
  });

  if (DRY_RUN) {
    console.log(JSON.stringify({
      mode: 'dry-run',
      sheet: SHEET_NAME,
      scannedRows: values.length,
      targetRows: targetRows.length,
      firstRows: targetRows.slice(0, 10),
      lastRows: targetRows.slice(-10),
    }, null, 2));
    return;
  }

  if (targetRows.length === 0) {
    console.log(JSON.stringify({ mode: 'applied', updatedRows: 0 }, null, 2));
    return;
  }

  const batchData = targetRows.map((rowNumber) => ({
    range: `${quoteSheetName(SHEET_NAME)}!H${rowNumber}:I${rowNumber}`,
    values: [['\u2715', TARGET_LABEL]],
  }));

  const result = await sheetsFetch(token, '/values:batchUpdate', {
    method: 'POST',
    body: JSON.stringify({
      valueInputOption: 'RAW',
      data: batchData,
    }),
  });

  const verify = await sheetsFetch(token, `/values/${encodeURIComponent(range)}`);
  const verifyValues = verify.values || [];
  const incompleteRows = targetRows.filter((rowNumber) => {
    const row = verifyValues[rowNumber - 1] || [];
    return row[7] !== '\u2715' || row[8] !== TARGET_LABEL;
  });

  console.log(JSON.stringify({
    mode: 'applied',
    targetRows: targetRows.length,
    updatedCells: result.totalUpdatedCells,
    incompleteRows,
    firstRows: targetRows.slice(0, 10),
    lastRows: targetRows.slice(-10),
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
