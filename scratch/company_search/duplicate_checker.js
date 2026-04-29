const { google } = require('googleapis');
const path = require('path');

const CREDENTIALS_PATH = path.join(__dirname, '../form_automation/google_credentials.json');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

const TARGET_SHEETS = [
  'Webマーケティング',
  'Webマーケティング_名古屋',
  'Webマーケティング_名古屋_テスト',
  'クリニック専門支援'
];

async function main() {
  const auth = new google.auth.GoogleAuth({
    keyFile: CREDENTIALS_PATH,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  const sheets = google.sheets({ version: 'v4', auth });

  // 1. Get all sheets
  const spreadsheet = await sheets.spreadsheets.get({
    spreadsheetId: SPREADSHEET_ID,
  });

  const allSheetNames = spreadsheet.data.sheets.map(s => s.properties.title);
  const baseSheets = allSheetNames.filter(name => !TARGET_SHEETS.includes(name));

  console.log(`Base sheets: ${baseSheets.join(', ')}`);
  console.log(`Target sheets: ${TARGET_SHEETS.join(', ')}`);

  const seenNames = new Map(); // normalized_name -> sheet_name
  const seenDomains = new Map(); // domain -> sheet_name

  const normalizeName = (name) => {
    if (!name) return '';
    return name.replace(/[\s　]/g, '').replace(/[（(].*?[)）]/g, '').toLowerCase();
  };

  const extractDomain = (url) => {
    if (!url) return '';
    try {
      let hostname = new URL(url).hostname;
      hostname = hostname.replace(/^www\./, '');
      return hostname;
    } catch (e) {
      return '';
    }
  };

  // 2. Read base sheets
  for (const sheetName of baseSheets) {
    try {
      const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A:E`,
      });
      const rows = res.data.values || [];
      // Assuming row 0 is header
      for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const name = normalizeName(row[2]);
        const domain = extractDomain(row[4]);
        if (name) seenNames.set(name, sheetName);
        if (domain) seenDomains.set(domain, sheetName);
      }
    } catch (e) {
      console.error(`Error reading base sheet ${sheetName}:`, e.message);
    }
  }

  console.log(`Loaded ${seenNames.size} unique names and ${seenDomains.size} unique domains from base sheets.`);

  // 3. Process target sheets
  const report = {};
  const deleteRequests = [];

  for (const sheetName of TARGET_SHEETS) {
    if (!allSheetNames.includes(sheetName)) {
      console.log(`Target sheet ${sheetName} not found.`);
      continue;
    }

    const sheetId = spreadsheet.data.sheets.find(s => s.properties.title === sheetName).properties.sheetId;

    report[sheetName] = {
      total: 0,
      duplicates: [],
    };

    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `${sheetName}!A:E`,
    });
    
    const rows = res.data.values || [];
    report[sheetName].total = rows.length <= 1 ? 0 : rows.length - 1;

    // Process backwards to delete rows without messing up indices
    for (let i = rows.length - 1; i >= 1; i--) {
      const row = rows[i];
      const name = normalizeName(row[2]);
      const domain = extractDomain(row[4]);

      let isDuplicate = false;
      let dupSource = '';

      if (name && seenNames.has(name)) {
        isDuplicate = true;
        dupSource = seenNames.get(name);
      } else if (domain && seenDomains.has(domain)) {
        isDuplicate = true;
        dupSource = seenDomains.get(domain);
      }

      if (isDuplicate) {
        report[sheetName].duplicates.push({ row: i + 1, name: row[2], reason: `Duplicate of ${dupSource}` });
        
        deleteRequests.push({
          deleteDimension: {
            range: {
              sheetId: sheetId,
              dimension: 'ROWS',
              startIndex: i,
              endIndex: i + 1
            }
          }
        });
      } else {
        if (name) seenNames.set(name, sheetName);
        if (domain) seenDomains.set(domain, sheetName);
      }
    }
  }

  // Generate Report
  console.log('\n--- Duplicate Report ---');
  let totalDups = 0;
  for (const sheetName of TARGET_SHEETS) {
    if (!report[sheetName]) continue;
    const stats = report[sheetName];
    console.log(`\nSheet: ${sheetName}`);
    console.log(`Total rows (excluding header): ${stats.total}`);
    console.log(`Duplicates found: ${stats.duplicates.length}`);
    totalDups += stats.duplicates.length;
    stats.duplicates.forEach(d => console.log(`  - Row ${d.row}: ${d.name} (${d.reason})`));
  }

  console.log(`\nTotal duplicates to remove across target sheets: ${totalDups}`);

  if (process.argv.includes('--execute')) {
    if (deleteRequests.length > 0) {
      console.log(`Executing ${deleteRequests.length} deletion requests...`);
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        resource: {
          requests: deleteRequests
        }
      });
      console.log('Deletion completed.');
    } else {
      console.log('No duplicates to delete.');
    }
  } else {
    console.log('\nRun with --execute to actually delete the rows.');
  }
}

main().catch(console.error);
