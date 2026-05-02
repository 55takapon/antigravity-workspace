const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const CREDENTIALS_PATH = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

async function checkDuplicates() {
    const auth = new google.auth.GoogleAuth({
        keyFile: CREDENTIALS_PATH,
        scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });
    const sheets = google.sheets({ version: 'v4', auth });
    
    const sheetName = 'Webマーケティング';
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A:Z`,
    });
    
    const rows = res.data.values || [];
    
    // index 2 is company_name, index 4 is official_url
    const seenNames = new Map();
    const seenUrls = new Map();
    const duplicates = [];
    
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const name = (row[2] || '').trim().replace(/[\s　]/g, '').replace(/株式会社|合同会社|有限会社/g, '');
        const url = (row[4] || '').trim();
        
        let dupReason = null;
        let dupSource = null;
        
        if (name && seenNames.has(name)) {
            dupReason = 'Name match';
            dupSource = seenNames.get(name).rowNum;
        } else if (url && seenUrls.has(url)) {
            dupReason = 'URL match';
            dupSource = seenUrls.get(url).rowNum;
        }
        
        if (dupReason) {
            duplicates.push({ rowNum: i + 1, name: row[2], url: url, reason: dupReason, originalRow: dupSource });
        } else {
            if (name) seenNames.set(name, { rowNum: i + 1, name, url });
            if (url) seenUrls.set(url, { rowNum: i + 1, name, url });
        }
    }
    
    console.log(`Found ${duplicates.length} duplicates in ${sheetName}.`);
    // Output the last 20 duplicates
    console.log(JSON.stringify(duplicates.slice(-20), null, 2));
}

checkDuplicates().catch(console.error);
