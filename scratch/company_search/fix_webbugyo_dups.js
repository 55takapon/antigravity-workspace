const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const CREDENTIALS_PATH = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

async function fixDuplicates() {
    const auth = new google.auth.GoogleAuth({
        keyFile: CREDENTIALS_PATH,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    const sheets = google.sheets({ version: 'v4', auth });
    
    const sheetName = 'Web奉行';
    
    // Get sheetId
    const meta = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    const sheetObj = meta.data.sheets.find(s => s.properties.title === sheetName);
    if (!sheetObj) {
        console.error('Sheet not found');
        return;
    }
    const sheetId = sheetObj.properties.sheetId;
    
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A:Z`,
    });
    
    const rows = res.data.values || [];
    
    const seenNames = new Map();
    const seenUrls = new Map();
    const deleteRequests = [];
    let dupCount = 0;
    
    // Process backwards to delete without messing up indices
    for (let i = rows.length - 1; i >= 1; i--) {
        const row = rows[i];
        const name = (row[2] || '').trim().replace(/[\s　]/g, '').replace(/株式会社|合同会社|有限会社/g, '');
        const url = (row[4] || '').trim();
        
        let isDuplicate = false;
        
        if (name && seenNames.has(name)) {
            isDuplicate = true;
        } else if (url && seenUrls.has(url)) {
            isDuplicate = true;
        }
        
        if (isDuplicate) {
            dupCount++;
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
            if (name) seenNames.set(name, true);
            if (url) seenUrls.set(url, true);
        }
    }
    
    console.log(`Found ${dupCount} duplicates in ${sheetName}. Deleting...`);
    
    if (deleteRequests.length > 0) {
        await sheets.spreadsheets.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            resource: {
                requests: deleteRequests
            }
        });
        console.log(`Successfully deleted ${deleteRequests.length} duplicate rows from ${sheetName}.`);
    } else {
        console.log('No duplicates found.');
    }
}

fixDuplicates().catch(console.error);
