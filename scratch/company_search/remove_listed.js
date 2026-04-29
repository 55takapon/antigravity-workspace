const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング_大阪';

// fill_employees.jsで検出された上場企業29社
const LISTED_COMPANIES = [
    'Eパートナーズ', 'オプト', 'マインドフリー', 'ベンチャーコード', 'じげん',
    'SBヒューマンキャピタル', 'CROSS', 'ダイトロン', 'ディーエムソリューションズ', 'ベクトル',
    'Fulfill', 'ニューラルマーケティング', 'アール・エム', 'Zenken', 'フリースクエア',
    'Method', 'イード', 'SUNSHINE', 'ヘリオス', 'ライフスケープ',
    'メディアリーチ', 'ジオコード', 'デジタリフト', 'フルスピード', 'マーケティングデザイン',
    'AIx', 'イルグルム', 'Aqua', 'ドンマイ'
];

async function main() {
    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    
    const allRows = response.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);
    
    // 逆順で削除リクエストを作成（行番号のズレを防ぐため）
    const deleteRequests = [];
    let deletedCount = 0;
    
    for (let i = dataRows.length - 1; i >= 0; i--) {
        const name = (dataRows[i][2] || '').trim();
        // 部分一致で上場企業リストに含まれるか判定
        const isListed = LISTED_COMPANIES.some(lc => name.includes(lc));
        
        if (isListed) {
            console.log(`[削除] 上場企業: ${name}`);
            const sheetRowIndex = i + 1; // 0-indexed for API (header is row 0)
            
            deleteRequests.push({
                deleteDimension: {
                    range: {
                        sheetId: 2110756779, // Webマーケティング_大阪のsheetId
                        dimension: "ROWS",
                        startIndex: sheetRowIndex,
                        endIndex: sheetRowIndex + 1
                    }
                }
            });
            deletedCount++;
        }
    }
    
    if (deleteRequests.length > 0) {
        // sheetIdを動的に取得
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
        const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
        const sheetId = sheet.properties.sheetId;
        
        // requestのsheetIdを更新
        deleteRequests.forEach(req => {
            req.deleteDimension.range.sheetId = sheetId;
        });

        await sheets.spreadsheets.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: { requests: deleteRequests }
        });
        console.log(`\n合計 ${deletedCount} 社（上場企業）をシートから削除しました。`);
    } else {
        console.log('削除対象の企業は見つかりませんでした。');
    }
}

main().catch(console.error);
