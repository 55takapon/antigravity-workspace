const fs = require('fs');
const { google } = require('googleapis');

const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_ID = 1266092372;
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const CANDIDATES_CSV = 'exclude_candidates_from_duplicates.csv';
const SHEET_CSV = 'csv_book2_1266092372.csv';
const DUPLICATE_LABEL = '\u91cd\u8907';
const NG_MARK = '\u2715';

const SHARED_HOSTS = new Set([
  'peraichi.com', 'studio.site', 'wixsite.com', 'jimdo.com', 'amebaownd.com',
  'thebase.in', 'stores.jp', 'note.com', 'facebook.com', 'instagram.com',
  'x.com', 'twitter.com', 'linkedin.com', 'wantedly.com', 'job-gear.net',
  'main.jp',
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

function normalizeText(value) {
  return (value || '').trim().replace(/[\s\u3000]+/g, ' ');
}

function normalizeDomain(value) {
  let url = (value || '').trim().replace(/[\s\u3000]+/g, '');
  if (!url) return '';
  if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(url)) {
    url = `http://${url}`;
  }
  let host = '';
  try {
    host = new URL(url).hostname.toLowerCase().replace(/\.$/, '');
  } catch {
    return '';
  }
  return host.startsWith('www.') ? host.slice(4) : host;
}

function isSharedHost(domain) {
  return Array.from(SHARED_HOSTS).some((host) => domain === host || domain.endsWith(`.${host}`));
}

function keyFor(company, domain) {
  if (domain && !isSharedHost(domain)) return `domain\t${domain}`;
  return `company\t${company}`;
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

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

async function main() {
  const candidateRows = parseCsv(fs.readFileSync(CANDIDATES_CSV, 'utf8'));
  const candidateHeader = candidateRows.shift();
  const keyTypeIndex = candidateHeader.indexOf('exclude_key_type');
  const keyIndex = candidateHeader.indexOf('exclude_key');
  const candidateKeys = new Set(candidateRows.map((row) => `${row[keyTypeIndex]}\t${row[keyIndex]}`));

  const sheetRows = parseCsv(fs.readFileSync(SHEET_CSV, 'utf8'));
  sheetRows.shift();

  const targetRows = [];
  sheetRows.forEach((row, index) => {
    const rowNumber = index + 2;
    const company = normalizeText(row[2]);
    const domain = normalizeDomain(row[4]);
    if (candidateKeys.has(keyFor(company, domain))) {
      targetRows.push(rowNumber);
    }
  });

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

  const data = consecutiveGroups(targetRows).map(({ start, end }) => ({
    range: `${quotedName}!G${start}:I${end}`,
    values: Array.from({ length: end - start + 1 }, () => [DUPLICATE_LABEL, NG_MARK, DUPLICATE_LABEL]),
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
    sheetName,
    targetRows: targetRows.length,
    updateRanges: data.length,
    firstTargetRow: Math.min(...targetRows),
    lastTargetRow: Math.max(...targetRows),
  }, null, 2));
}

main().catch((error) => {
  console.error(error.response?.data || error.message || error);
  process.exit(1);
});
