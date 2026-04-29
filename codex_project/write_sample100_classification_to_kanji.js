const fs = require('fs');
const { google } = require('googleapis');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_ID = 1266092372;
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const RESULT_CSV = 'web_company_classification_sample100.csv';

const LABELS = {
  web_production: 'Web制作',
  web_marketing: 'Webマーケ',
  hybrid: 'ハイブリッド',
  unknown: '判定不可',
};

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

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

async function main() {
  const rows = parseCsv(fs.readFileSync(RESULT_CSV, 'utf8'));
  const header = rows.shift();
  const classificationIndex = header.indexOf('classification');
  if (classificationIndex === -1) throw new Error('classification column not found');

  const values = rows.map((row) => [LABELS[row[classificationIndex]] || row[classificationIndex] || '判定不可']);
  if (values.length !== 100) {
    throw new Error(`Expected 100 result rows, got ${values.length}`);
  }

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

  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `${quoteSheetName(sheetName)}!O2:O101`,
    valueInputOption: 'RAW',
    requestBody: { values },
  });

  const counts = values.reduce((acc, [label]) => {
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {});

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.data.properties.title,
    sheetName,
    range: 'O2:O101',
    writtenRows: values.length,
    counts,
  }, null, 2));
}

main().catch((error) => {
  console.error(error.response?.data || error.message || error);
  process.exit(1);
});
