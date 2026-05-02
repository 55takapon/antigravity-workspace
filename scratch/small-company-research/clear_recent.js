const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング';

async function clearRecent() {
    let credPath = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
    if (!fs.existsSync(credPath)) credPath = path.join(__dirname, 'google_credentials.json');
    
    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({ credentials, scopes: ['https://www.googleapis.com/auth/spreadsheets'] });
    const sheets = google.sheets({ version: 'v4', auth });

    await sheets.spreadsheets.values.clear({
        spreadsheetId: SPREADSHEET_ID,
        range: `${TARGET_SHEET}!A1077:Z`,
    });

    console.log('1077行目以降のデータをクリアしました。');
}

clearRecent().catch(console.error);
