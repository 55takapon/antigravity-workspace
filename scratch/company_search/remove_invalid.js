const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング_大阪';

// URLと企業名が乖離している代表的なドメイン（制作会社のサブドメイン等）
const INVALID_DOMAINS = [
    'hp.f-creation.co.jp', 
    'f-creation.co.jp'
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
    
    const formIdx = header.indexOf('問い合わせフォームURL');
    if (formIdx < 0) { console.error('問い合わせフォームURL列が見つかりません'); return; }

    const deleteRequests = [];
    let deletedForm = 0;
    let deletedMismatch = 0;
    
    // 逆順で処理
    for (let i = dataRows.length - 1; i >= 0; i--) {
        const name = (dataRows[i][2] || '').trim();
        const url = (dataRows[i][4] || '').trim();
        const formUrl = (dataRows[i][formIdx] || '').trim();
        
        let shouldDelete = false;
        let reason = '';

        // 1. フォームURLなし
        if (!formUrl) {
            shouldDelete = true;
            reason = 'フォームURLなし';
            deletedForm++;
        } 
        // 2. 特殊な無効ドメイン（企業名との乖離）
        else {
            try {
                const u = new URL(url);
                if (INVALID_DOMAINS.includes(u.hostname) || u.hostname.startsWith('hp.')) {
                    shouldDelete = true;
                    reason = '企業名-URL乖離（サブドメイン間借り）';
                    deletedMismatch++;
                }
            } catch { }
            // 手動指定（スリードット）
            if (name.includes('スリードット')) {
                shouldDelete = true;
                reason = '指定除外';
            }
        }

        if (shouldDelete) {
            console.log(`[削除] ${name} | ${url} (${reason})`);
            const sheetRowIndex = i + 1;
            deleteRequests.push({
                deleteDimension: {
                    range: {
                        sheetId: 2110756779,
                        dimension: "ROWS",
                        startIndex: sheetRowIndex,
                        endIndex: sheetRowIndex + 1
                    }
                }
            });
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
        console.log(`\n合計 ${deleteRequests.length} 件を削除しました。`);
        console.log(` - フォームなし: ${deletedForm}件`);
        console.log(` - URL乖離: ${deletedMismatch}件`);
    } else {
        console.log('削除対象はありませんでした。');
    }
}

main().catch(console.error);
