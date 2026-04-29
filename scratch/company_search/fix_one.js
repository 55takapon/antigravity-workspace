/**
 * fix_one.js - #100「株式会社コーポレートサイト」を削除
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング_大阪';

async function main() {
    const sheets = await getGoogleSheetsClient();

    // 現在のデータを読み取り
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const dataRows = allRows.slice(1);

    // 「コーポレートサイト」を含む行を特定
    let targetIdx = -1;
    for (let i = 0; i < dataRows.length; i++) {
        const name = (dataRows[i][2] || '').trim();
        if (name.includes('コーポレートサイト') || name.includes('サイト') && !name.includes('フリースクエア')) {
            console.log(`検出: 行${i + 2}: "${name}"`);
            if (name.includes('コーポレートサイト')) targetIdx = i;
        }
    }

    if (targetIdx >= 0) {
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
        const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
        const sheetId = sheet.properties.sheetId;

        await sheets.spreadsheets.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: {
                requests: [{
                    deleteDimension: {
                        range: {
                            sheetId,
                            dimension: 'ROWS',
                            startIndex: targetIdx + 1,
                            endIndex: targetIdx + 2,
                        },
                    },
                }],
            },
        });
        console.log(`削除完了: 行${targetIdx + 2}`);
    } else {
        console.log('対象行が見つかりません');
    }

    // 最終確認
    const final = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const finalData = final.data.values.slice(1);
    console.log(`\n最終件数: ${finalData.length}件`);

    // 全件名を出力して最終確認
    console.log('\n=== 全企業名一覧（最終） ===');
    for (let i = 0; i < finalData.length; i++) {
        const name = (finalData[i][2] || '').trim();
        const url = (finalData[i][4] || '').trim();
        const emp = (finalData[i][9] || '').trim();
        console.log(`#${String(i+1).padStart(3)}: ${name} | ${url} | 従業員:${emp || '不明'}`);
    }
}

main().catch(err => { console.error(err); process.exit(1); });
