const fs = require('fs');
const { google } = require('googleapis');
async function main() {
    const credPath = 'google_credentials.json';
    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({
        credentials, scopes: ['https://www.googleapis.com/auth/spreadsheets']
    });
    const sheets = google.sheets({ version: 'v4', auth });
    const res = await sheets.spreadsheets.get({ spreadsheetId: '1cBraHQGD5xAYTX-ljt8JaekiqshlMqZ2GTFGSLJKodE' });
    res.data.sheets.forEach(s => console.log('SHEET NAME:', s.properties.title));
}
main().catch(console.error);
