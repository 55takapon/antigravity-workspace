const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function main() {
    const credPath = path.join(__dirname, 'google_credentials.json');
    const creds = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    console.log('サービスアカウント:', creds.client_email);

    const auth = new google.auth.GoogleAuth({
        credentials: creds,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    const sheets = google.sheets({ version: 'v4', auth });

    const spreadsheetId = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
    const sheetName = '260325test';

    console.log('スプレッドシートへ接続中...');
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range: `${sheetName}!A1:I5`,
    });

    const rows = res.data.values || [];
    console.log(`SUCCESS - ${rows.length}行読み込み完了`);
    rows.forEach((row, i) => console.log(`  Row ${i}:`, row.slice(0, 9).join(' | ')));
}

main().catch(err => {
    console.error('ERROR:', err.message);
    process.exit(1);
});
