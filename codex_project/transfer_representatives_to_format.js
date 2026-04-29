const fs = require('fs');
const { google } = require('googleapis');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const CANDIDATES_CSV = 'representative_transfer_candidates.csv';
const SHEET_NAME_FIXES = new Map([
  ['Web???????', '\u0057\u0065\u0062\u30de\u30fc\u30b1\u30c6\u30a3\u30f3\u30b0'],
  ['Web???????_???', '\u0057\u0065\u0062\u30de\u30fc\u30b1\u30c6\u30a3\u30f3\u30b0_\u540d\u53e4\u5c4b'],
  ['?????????', '\u30af\u30ea\u30cb\u30c3\u30af\u5c02\u9580\u652f\u63f4'],
]);

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

function pickRepresentative(row, header) {
  const decision = row[header.decision];
  const candidateRep = row[header.candidate_rep];
  if (decision === 'confident') return candidateRep;

  const targetDomain = row[header.target_domain];
  const refs = row[header.kanji_refs].split(' | ');
  const domainMatch = refs.find((ref) => ref.endsWith(`:${targetDomain}`));
  if (!domainMatch) {
    throw new Error(`No domain-matched representative for ${row[header.target_sheet]} row ${row[header.target_row]}`);
  }
  const parts = domainMatch.split(':');
  if (parts.length < 4) {
    throw new Error(`Unexpected ref format: ${domainMatch}`);
  }
  return parts[2];
}

async function main() {
  const csvRows = parseCsv(fs.readFileSync(CANDIDATES_CSV, 'utf8'));
  const headerRow = csvRows.shift();
  const header = Object.fromEntries(headerRow.map((name, index) => [name, index]));

  const updates = csvRows.map((row) => ({
    sheetName: SHEET_NAME_FIXES.get(row[header.target_sheet]) || row[header.target_sheet],
    rowNumber: Number(row[header.target_row]),
    representative: pickRepresentative(row, header),
    decision: row[header.decision],
  }));

  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  const metadata = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const existingSheets = new Set(metadata.data.sheets.map((sheet) => sheet.properties.title));
  for (const update of updates) {
    if (!existingSheets.has(update.sheetName)) {
      throw new Error(`Sheet not found: ${update.sheetName}`);
    }
  }

  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId: SPREADSHEET_ID,
    requestBody: {
      valueInputOption: 'RAW',
      data: updates.map((update) => ({
        range: `${quoteSheetName(update.sheetName)}!D${update.rowNumber}:D${update.rowNumber}`,
        values: [[update.representative]],
      })),
    },
  });

  const counts = updates.reduce((acc, update) => {
    acc[update.decision] = (acc[update.decision] || 0) + 1;
    return acc;
  }, {});

  console.log(JSON.stringify({
    spreadsheetTitle: metadata.data.properties.title,
    updatedRows: updates.length,
    counts,
    ambiguousDomainPriority: updates.filter((update) => update.decision === 'ambiguous').map((update) => ({
      sheetName: update.sheetName,
      rowNumber: update.rowNumber,
      representative: update.representative,
    })),
  }, null, 2));
}

main().catch((error) => {
  console.error(error.response?.data || error.message || error);
  process.exit(1);
});
