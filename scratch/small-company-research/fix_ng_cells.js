'use strict';

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

const CREDENTIALS_PATH = path.join(__dirname, 'google_credentials.json');
const SPREADSHEET_ID = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';
const SHEET_NAME = 'シート1';

async function main() {
    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    const authClient = await auth.getClient();
    const sheets = google.sheets({ version: 'v4', auth: authClient });

    const updates = [
        // 行3870 グライナー: 営業NG文言（サイトに記載されていた実際の文言）
        {
            range: `'${SHEET_NAME}'!I3870`,
            value: '売り込みは一切必要ないので、メール・電話などしないでください',
        },
        // 行3875 GOAT: 業種違い
        {
            range: `'${SHEET_NAME}'!I3875`,
            value: '業種違い',
        },
    ];

    for (const u of updates) {
        await sheets.spreadsheets.values.update({
            spreadsheetId: SPREADSHEET_ID,
            range: u.range,
            valueInputOption: 'RAW',
            requestBody: { values: [[u.value]] },
        });
        console.log(`✅ ${u.range} → "${u.value}"`);
    }

    console.log('完了');
}

main().catch(e => { console.error(e); process.exit(1); });
