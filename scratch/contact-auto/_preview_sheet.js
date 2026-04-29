const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function main() {
    const credPath = path.join(__dirname, 'google_credentials.json');
    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({ credentials, scopes: ['https://www.googleapis.com/auth/spreadsheets'] });
    const sheets = google.sheets({ version: 'v4', auth });
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk',
        range: "'260325test'!A1:Z5"
    });
    const rows = res.data.values || [];
    rows.forEach((row, i) => {
        console.log('行' + (i+1) + ':');
        row.forEach((cell, j) => {
            console.log('  [' + j + ']', cell);
        });
    });
}
main().catch(e => console.error('Error:', e.message));
