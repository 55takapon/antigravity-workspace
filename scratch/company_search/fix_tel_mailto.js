const { getGoogleSheetsClient } = require('./sheets_writer');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング';

(async () => {
    console.log(`=== ${TARGET_SHEET} の tel:/mailto: エラー修正開始 ===`);
    const sheets = await getGoogleSheetsClient();
    
    // シート全体を取得
    const res = await sheets.spreadsheets.values.get({ 
        spreadsheetId: SPREADSHEET_ID, 
        range: TARGET_SHEET 
    });
    
    const allRows = res.data.values || [];
    const updates = [];
    
    for (let i = 1; i < allRows.length; i++) {
        const row = allRows[i];
        while (row.length < 10) row.push('');
        
        const formUrl = (row[5] || '').trim(); // F列: 問い合わせURL
        if (formUrl.startsWith('tel:') || formUrl.startsWith('mailto:')) {
            const rowNum = i + 1;
            const currentH = (row[7] || '').trim();
            const currentI = (row[8] || '').trim();
            
            let newReason = '【自動判定】フォーム未検出（tel/mailto）';
            if (currentI && !currentI.includes('フォーム未検出')) {
                newReason = `${currentI} / ${newReason}`;
            }
            
            updates.push({
                range: `${TARGET_SHEET}!H${rowNum}:I${rowNum}`,
                values: [['✕', newReason]]
            });
            console.log(`行${rowNum} を更新対象に追加 (${formUrl})`);
        }
    }
    
    if (updates.length > 0) {
        await sheets.spreadsheets.values.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: {
                valueInputOption: 'USER_ENTERED',
                data: updates
            }
        });
        console.log(`✅ ${updates.length}件を「送信不可（✕）」に更新しました`);
    } else {
        console.log('更新対象は見つかりませんでした');
    }
    
    console.log('\n並び替えスクリプト (sort_by_category.js) を実行して移動を完了させてください。');
})().catch(e => console.error(e));
