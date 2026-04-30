const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_NAME = 'シート1';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const CANDIDATES_CSV = 'web_kanji_missing_0429_duplicate_candidates.csv';
const DUPLICATE_LABEL = '重複';
const NG_MARK = '×';

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

function consecutiveGroups(numbers) {
  const sorted = [...numbers].sort((a, b) => a - b);
  const groups = [];
  for (const n of sorted) {
    const last = groups[groups.length - 1];
    if (last && last.end + 1 === n) {
      last.end = n;
    } else {
      groups.push({ start: n, end: n });
    }
  }
  return groups;
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

  const targetRows = new Set();
  for (const row of csvRows) {
    const rowNumber = Number(row[rowIndex]);
    if (!Number.isInteger(rowNumber) || rowNumber < 7316) {
      throw new Error(`Unexpected target row: ${row[rowIndex]}`);
    }
    targetRows.add(rowNumber);
  }

  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, '?fields=properties.title,sheets.properties.title');
  const sheet = metadata.sheets.find((s) => s.properties.title === SHEET_NAME);
  if (!sheet) throw new Error(`Sheet not found: ${SHEET_NAME}`);

  const quoted = quoteSheetName(SHEET_NAME);
  const data = consecutiveGroups(targetRows).map(({ start, end }) => ({
    range: `${quoted}!H${start}:I${end}`,
    values: Array.from({ length: end - start + 1 }, () => [NG_MARK, DUPLICATE_LABEL]),
  }));

  await sheetsFetch(token, '/values:batchUpdate', {
    method: 'POST',
    body: JSON.stringify({
      valueInputOption: 'RAW',
      data,
    }),
  });

  const verify = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoted}!H${Math.min(...targetRows)}:I${Math.max(...targetRows)}`)}`);
  const verifiedMarked = (verify.values || []).filter((row) => row[0] === NG_MARK && row[1] === DUPLICATE_LABEL).length;

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.properties.title,
    sheetName: SHEET_NAME,
    uniqueTargetRows: targetRows.size,
    updateRanges: data.length,
    firstTargetRow: Math.min(...targetRows),
    lastTargetRow: Math.max(...targetRows),
    verifiedMarkedWithinSpan: verifiedMarked,
    preservedTimestampColumn: 'G',
    markedColumns: 'H:I',
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
