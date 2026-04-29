const fs = require('fs');
const { google } = require('googleapis');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_ID = 1266092372;
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const DUPLICATE_LABEL = '\u91cd\u8907';

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

function padRow(row, width) {
  const next = row ? [...row] : [];
  while (next.length < width) next.push('');
  return next.slice(0, width);
}

async function main() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  const metadata = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const sheet = metadata.data.sheets.find((s) => s.properties.sheetId === SHEET_ID);
  if (!sheet) throw new Error(`Sheet not found for sheetId: ${SHEET_ID}`);

  const sheetName = sheet.properties.title;
  const quotedName = quoteSheetName(sheetName);

  const current = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: `${quotedName}!A2:I`,
  });

  const rows = (current.data.values || []).map((row) => padRow(row, 9));
  const nonDuplicates = [];
  const duplicates = [];
  for (const row of rows) {
    if (row[6] === DUPLICATE_LABEL) duplicates.push(row);
    else nonDuplicates.push(row);
  }

  const sorted = [...nonDuplicates, ...duplicates];

  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `${quotedName}!A2:I${sorted.length + 1}`,
    valueInputOption: 'RAW',
    requestBody: { values: sorted },
  });

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.data.properties.title,
    sheetName,
    totalRows: rows.length,
    nonDuplicateRows: nonDuplicates.length,
    duplicateRows: duplicates.length,
    firstDuplicateOutputRow: nonDuplicates.length + 2,
    lastDuplicateOutputRow: sorted.length + 1,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.response?.data || error.message || error);
  process.exit(1);
});
