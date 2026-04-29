/**
 * fix_header.js - 大阪シートにK列「資本金」を挿入
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング_大阪';

async function main() {
    const sheets = await getGoogleSheetsClient();

    // シートIDを取得
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
    const sheetId = sheet.properties.sheetId;

    // 現在のヘッダーを取得
    const resp = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!1:1`,
    });
    const currentHeaders = resp.data.values?.[0] || [];
    console.log('現在のヘッダー:', currentHeaders.join(' | '));

    // K列(10列目, 0-indexed)が既に「資本金」かチェック
    if (currentHeaders[10] === '資本金') {
        console.log('K列は既に「資本金」です。変更不要。');
        return;
    }

    // K列に列を挿入（既存データを右にシフト）
    console.log('\nK列（11列目）に「資本金」列を挿入します...');
    await sheets.spreadsheets.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        requestBody: {
            requests: [{
                insertDimension: {
                    range: {
                        sheetId,
                        dimension: 'COLUMNS',
                        startIndex: 10,  // K列(0-indexed = 10)
                        endIndex: 11,
                    },
                    inheritFromBefore: false,
                },
            }],
        },
    });

    // K1に「資本金」ヘッダーを書き込み
    await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!K1`,
        valueInputOption: 'USER_ENTERED',
        requestBody: { values: [['資本金']] },
    });

    // 確認
    const finalResp = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!1:1`,
    });
    console.log('\n修正後ヘッダー:', finalResp.data.values?.[0].join(' | '));
    console.log('\n完了');
}

main().catch(err => { console.error(err); process.exit(1); });
