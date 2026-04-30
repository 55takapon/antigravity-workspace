const { getGoogleSheetsClient } = require('./sheets_writer');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング_名古屋';

(async () => {
    const sheets = await getGoogleSheetsClient();
    const updates = [
        { range: `${TARGET_SHEET}!H15:I15`, values: [['✕', '【自動判定】社名・URL不一致']] },
        { range: `${TARGET_SHEET}!H59:I59`, values: [['✕', '【自動判定】社名・URL不一致']] },
        { range: `${TARGET_SHEET}!H82:I82`, values: [['✕', '【自動判定】社名・URL不一致']] },
    ];
    
    await sheets.spreadsheets.values.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        requestBody: {
            valueInputOption: 'USER_ENTERED',
            data: updates
        }
    });
    console.log('✅ 3件を送信不可（✕）に更新しました');
    
    // 再度並べ替えを実行
    console.log('\n=== ' + TARGET_SHEET + ' の並び替え再実行 ===');
    const res = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: TARGET_SHEET });
    const allRows = res.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);
    
    const sendable = [], notSendable = [];
    for (const row of dataRows) {
        const colI = (row[8] || '').trim();
        if (colI === '') sendable.push(row); else notSendable.push(row);
    }
    
    const sortedRows = [header, ...sendable, ...notSendable];
    const maxCols = sortedRows.reduce((max, row) => Math.max(max, row.length), 0);
    const paddedRows = sortedRows.map(row => { const r = [...row]; while (r.length < maxCols) r.push(''); return r; });
    
    await sheets.spreadsheets.values.update({ 
        spreadsheetId: SPREADSHEET_ID, 
        range: TARGET_SHEET + '!A1', 
        valueInputOption: 'USER_ENTERED', 
        requestBody: { values: paddedRows } 
    });
    console.log('✅ 並び替え完了！上から ' + sendable.length + '行: 送信対象 / 下から ' + notSendable.length + '行: 送信不可');
})().catch(e => console.error(e));
