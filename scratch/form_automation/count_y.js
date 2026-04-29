const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');

async function getGoogleSheetsClient() {
    const credPath = path.join(__dirname, 'google_credentials.json');
    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    return google.sheets({ version: 'v4', auth });
}

async function main() {
    const spreadsheetId = '1cBraHQGD5xAYTX-ljt8JaekiqshlMqZ2GTFGSLJKodE';
    const sheetName = '260311(260202copy) ';
    
    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range: sheetName,
    });
    const values = response.data.values || [];
    if (values.length === 0) return;
    const headers = values[0];
    const rows = values.slice(1);
    
    const dateCol = headers.indexOf('送信日');
    const statusCol = headers.indexOf('送信○×');
    
    let count = 0;
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const dateVal = row[dateCol] ? row[dateCol].trim() : '';
        const statusVal = row[statusCol] ? row[statusCol].trim() : '';
        
        // y（送信済み）の条件: 送信日が今日のいずれかのフォーマット、かつ送信○×が「〇」
        if ((dateVal === '2026/04/13' || dateVal === '2026/4/13') && statusVal === '〇') {
            count++;
        }
    }
    console.log(`__RESULT__:${count}`);
}

main().catch(console.error);
