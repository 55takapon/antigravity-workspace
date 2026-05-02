const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

const CREDENTIALS_PATH = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');

async function checkCounts() {
    const auth = new google.auth.GoogleAuth({
        keyFile: CREDENTIALS_PATH,
        scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });
    const sheets = google.sheets({ version: 'v4', auth });

    const book1 = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
    const book2 = '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ';

    let totalRows = 0;
    
    async function countBook(bookId, bookName) {
        console.log(`\n--- ${bookName} ---`);
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: bookId });
        const sheetNames = spreadsheet.data.sheets.map(s => s.properties.title);
        
        let bookRows = 0;
        for (const sheetName of sheetNames) {
            if (sheetName === '260325test' || sheetName === 'list-format') continue; // exclude test
            
            const res = await sheets.spreadsheets.values.get({
                spreadsheetId: bookId,
                range: `${sheetName}!A:E`,
            });
            const rows = res.data.values || [];
            if (rows.length > 1) {
                const count = rows.length - 1; // exclude header
                console.log(`Sheet "${sheetName}": ${count} rows`);
                bookRows += count;
            }
        }
        console.log(`${bookName} Total Rows: ${bookRows}`);
        totalRows += bookRows;
    }

    await countBook(book1, 'Book1 (1kTO...)');
    await countBook(book2, 'Book2 (1ted...)');

    console.log(`\nGrand Total Rows: ${totalRows}`);
}

checkCounts().catch(console.error);
