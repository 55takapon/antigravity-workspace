const fs = require('fs');
const crypto = require('crypto');

const FORMAT_SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const NEW_ROWS_TSV = 'web_kanji_missing_0429_rows.tsv';
const OUTPUT_CSV = 'web_kanji_missing_0429_duplicate_candidates.csv';
const EXCLUDED_SHEETS = new Set(['260325test']);

const SHARED_HOSTS = new Set([
  'peraichi.com', 'studio.site', 'wixsite.com', 'jimdo.com', 'amebaownd.com',
  'thebase.in', 'stores.jp', 'note.com', 'facebook.com', 'instagram.com',
  'x.com', 'twitter.com', 'linkedin.com', 'wantedly.com', 'job-gear.net',
  'main.jp',
]);

function base64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

function parseTsv(text) {
  return text.replace(/^\uFEFF/, '').replace(/\r?\n$/, '').split(/\r?\n/).map((line) => line.split('\t'));
}

function csvEscape(value) {
  const text = String(value || '');
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function normalizeText(value) {
  return String(value || '').trim().replace(/[\s\u3000]+/g, ' ');
}

function normalizeDomain(value) {
  let url = String(value || '').trim().replace(/[\s\u3000]+/g, '');
  if (!url) return '';
  if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(url)) url = `http://${url}`;
  try {
    const host = new URL(url).hostname.toLowerCase().replace(/\.$/, '');
    return host.startsWith('www.') ? host.slice(4) : host;
  } catch {
    return '';
  }
}

function isSharedHost(domain) {
  return Array.from(SHARED_HOSTS).some((host) => domain === host || domain.endsWith(`.${host}`));
}

async function getAccessToken() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const now = Math.floor(Date.now() / 1000);
  const signingInput = `${base64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }))}.${base64url(JSON.stringify({
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets.readonly',
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

async function sheetsFetch(token, spreadsheetId, path) {
  const response = await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${spreadsheetId}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(data));
  return data;
}

async function main() {
  const newRows = parseTsv(fs.readFileSync(NEW_ROWS_TSV, 'utf8')).map((row, index) => ({
    kanjiRow: 7316 + index,
    number: row[0],
    prefecture: row[1],
    company: normalizeText(row[2]),
    representative: normalizeText(row[3]),
    url: row[4] || '',
    domain: normalizeDomain(row[4]),
  }));

  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, FORMAT_SPREADSHEET_ID, '?fields=properties.title,sheets.properties.title');
  const sheetNames = metadata.sheets
    .map((sheet) => sheet.properties.title)
    .filter((name) => !EXCLUDED_SHEETS.has(name));

  const byDomain = new Map();
  const byCompany = new Map();

  for (const sheetName of sheetNames) {
    const range = `${quoteSheetName(sheetName)}!A2:I`;
    const data = await sheetsFetch(token, FORMAT_SPREADSHEET_ID, `/values/${encodeURIComponent(range)}`);
    for (const [idx, row] of (data.values || []).entries()) {
      const rowNumber = idx + 2;
      const company = normalizeText(row[2]);
      const representative = normalizeText(row[3]);
      const url = row[4] || '';
      const domain = normalizeDomain(url);
      const record = { sheetName, rowNumber, company, representative, url, domain };
      if (domain && !isSharedHost(domain)) {
        if (!byDomain.has(domain)) byDomain.set(domain, []);
        byDomain.get(domain).push(record);
      }
      if (company) {
        if (!byCompany.has(company)) byCompany.set(company, []);
        byCompany.get(company).push(record);
      }
    }
  }

  const outputRows = [];
  for (const row of newRows) {
    const matches = [];
    if (row.domain && !isSharedHost(row.domain) && byDomain.has(row.domain)) {
      for (const match of byDomain.get(row.domain)) matches.push({ ...match, matchBy: 'domain' });
    }
    if (row.company && byCompany.has(row.company)) {
      for (const match of byCompany.get(row.company)) {
        if (!matches.some((existing) => existing.sheetName === match.sheetName && existing.rowNumber === match.rowNumber)) {
          matches.push({ ...match, matchBy: 'company' });
        }
      }
    }
    for (const match of matches) {
      outputRows.push([
        row.kanjiRow,
        row.number,
        row.prefecture,
        row.company,
        row.representative,
        row.domain,
        row.url,
        match.matchBy,
        match.sheetName,
        match.rowNumber,
        match.company,
        match.representative,
        match.domain,
        match.url,
      ]);
    }
  }

  const header = [
    'kanji_sheet_row', 'kanji_number', 'prefecture', 'kanji_company', 'kanji_representative',
    'kanji_domain', 'kanji_url', 'match_by', 'format_sheet', 'format_row',
    'format_company', 'format_representative', 'format_domain', 'format_url',
  ];
  fs.writeFileSync(
    OUTPUT_CSV,
    [header, ...outputRows].map((row) => row.map(csvEscape).join(',')).join('\n') + '\n',
    'utf8',
  );

  const uniqueKanjiRows = new Set(outputRows.map((row) => row[0]));
  const byMatchType = outputRows.reduce((acc, row) => {
    acc[row[7]] = (acc[row[7]] || 0) + 1;
    return acc;
  }, {});

  console.log(JSON.stringify({
    formatSpreadsheetTitle: metadata.properties.title,
    checkedSheets: sheetNames.length,
    excludedSheets: Array.from(EXCLUDED_SHEETS),
    checkedNewRows: newRows.length,
    duplicateCandidateRows: outputRows.length,
    uniqueKanjiRowsWithCandidates: uniqueKanjiRows.size,
    byMatchType,
    outputCsv: OUTPUT_CSV,
    firstCandidates: outputRows.slice(0, 5),
  }, null, 2));
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
