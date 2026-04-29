const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_NAME = 'シート1';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const TSV_PATH = path.join(__dirname, 'web_kanji_all_available_ordered_rows2.tsv');

function parseTsv(text) {
  return text
    .replace(/^\uFEFF/, '')
    .trimEnd()
    .split(/\r?\n/)
    .map((line) => line.split('\t'));
}

async function main() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  const values = parseTsv(fs.readFileSync(TSV_PATH, 'utf8'));

  const metadata = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const sheet = metadata.data.sheets.find((s) => s.properties.title === SHEET_NAME);
  if (!sheet) {
    throw new Error(`Sheet not found: ${SHEET_NAME}`);
  }

  const requiredRows = values.length + 1;
  if ((sheet.properties.gridProperties.rowCount || 0) < requiredRows) {
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SPREADSHEET_ID,
      requestBody: {
        requests: [{
          updateSheetProperties: {
            properties: {
              sheetId: sheet.properties.sheetId,
              gridProperties: { rowCount: requiredRows },
            },
            fields: 'gridProperties.rowCount',
          },
        }],
      },
    });
  }

  await sheets.spreadsheets.values.clear({
    spreadsheetId: SPREADSHEET_ID,
    range: `${SHEET_NAME}!A2:I`,
  });

  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `${SHEET_NAME}!A2`,
    valueInputOption: 'RAW',
    requestBody: { values },
  });

  const verify = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: `${SHEET_NAME}!A2:I${requiredRows}`,
  });

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.data.properties.title,
    sheet: SHEET_NAME,
    writtenRows: values.length,
    writtenDataRows: values.length,
    verifiedRows: verify.data.values ? verify.data.values.length : 0,
    firstCompany: values[0] ? values[0][2] : null,
    lastCompany: values[values.length - 1] ? values[values.length - 1][2] : null,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.response?.data || error.message || error);
  process.exit(1);
});
