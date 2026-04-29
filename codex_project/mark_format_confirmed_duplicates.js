const fs = require('fs');
const { google } = require('googleapis');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const DUPLICATE_LABEL = '\u91cd\u8907';
const NG_MARK = '\u2715';

const TARGETS = [
  { sheetName: '\u0057\u0065\u0062\u30de\u30fc\u30b1\u30c6\u30a3\u30f3\u30b0_\u540d\u53e4\u5c4b', row: 124 },
  { sheetName: '251127', row: 973 },
];

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

async function main() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  const metadata = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const existingSheets = new Set(metadata.data.sheets.map((sheet) => sheet.properties.title));
  for (const target of TARGETS) {
    if (!existingSheets.has(target.sheetName)) {
      throw new Error(`Sheet not found: ${target.sheetName}`);
    }
  }

  const data = TARGETS.map((target) => ({
    range: `${quoteSheetName(target.sheetName)}!G${target.row}:I${target.row}`,
    values: [[DUPLICATE_LABEL, NG_MARK, DUPLICATE_LABEL]],
  }));

  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId: SPREADSHEET_ID,
    requestBody: {
      valueInputOption: 'RAW',
      data,
    },
  });

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.data.properties.title,
    updated: TARGETS,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.response?.data || error.message || error);
  process.exit(1);
});
