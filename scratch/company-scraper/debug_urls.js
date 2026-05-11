const { google } = require('googleapis');
const path = require('path');

async function main() {
  const auth = new google.auth.GoogleAuth({
    keyFile: path.join(__dirname, 'google_credentials.json'),
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });
  const client = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: client });
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY',
    range: 'シート1!C183:E200',
  });
  const rows = res.data.values || [];
  rows.forEach((r, i) => {
    console.log('行' + (183 + i) + ': ' + (r[0] || '') + ' | ' + (r[2] || ''));
  });
}
main().catch(e => console.error(e.message));
