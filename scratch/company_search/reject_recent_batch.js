/**
 * reject_recent_batch.js
 * N列（取得日時）が2026/4/30 or 2026/5/1 の行を全件送信不可にする
 */
const { getGoogleSheetsClient } = require('./sheets_writer');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング';

(async () => {
    const sheets = await getGoogleSheetsClient();
    console.log(`=== ${TARGET_SHEET}: 直近バッチ（4/30・5/1取得分）→ 全件送信不可処理 ===\n`);

    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET
    });
    const allRows = res.data.values || [];
    const header = allRows[0];
    
    // N列のインデックスを特定
    const nIdx = header.indexOf('取得日時');
    const hIdx = header.indexOf('送信○×');
    const iIdx = header.indexOf('送信不可理由');
    console.log(`N列（取得日時）: 列インデックス ${nIdx}`);
    console.log(`H列（送信○×）: 列インデックス ${hIdx}`);
    console.log(`I列（送信不可理由）: 列インデックス ${iIdx}\n`);

    const updates = [];
    let matched = 0;
    let alreadyRejected = 0;
    
    for (let i = 1; i < allRows.length; i++) {
        const row = allRows[i];
        const timestamp = (row[nIdx] || '').trim();
        const currentH = (row[hIdx] || '').trim();
        
        // 2026/4/30 or 2026/5/1 の取得分
        const isRecent = timestamp.startsWith('2026/4/30') || 
                         timestamp.startsWith('2026/5/1') ||
                         timestamp.startsWith('2026/04/30') ||
                         timestamp.startsWith('2026/05/01');
        
        if (!isRecent) continue;
        matched++;
        
        // 既に✕の場合もコメント追記
        if (currentH === '✕') {
            alreadyRejected++;
        }
        
        const rowNum = i + 1;
        const companyName = row[2] || '';
        console.log(`  行${rowNum}: ${companyName} (取得: ${timestamp})`);
        
        updates.push({
            range: `${TARGET_SHEET}!H${rowNum}:I${rowNum}`,
            values: [['✕', '【品質不足】company_search直近バッチ（4/30-5/1）全件廃棄']]
        });
    }
    
    console.log(`\n対象: ${matched}件（うち既に✕: ${alreadyRejected}件）`);
    
    if (updates.length > 0) {
        // 100件ずつ分割してAPIリクエスト
        const CHUNK = 100;
        for (let i = 0; i < updates.length; i += CHUNK) {
            const chunk = updates.slice(i, i + CHUNK);
            await sheets.spreadsheets.values.batchUpdate({
                spreadsheetId: SPREADSHEET_ID,
                requestBody: {
                    valueInputOption: 'USER_ENTERED',
                    data: chunk
                }
            });
            console.log(`  ${i + chunk.length}/${updates.length}件 更新完了`);
        }
        console.log(`\n✅ 合計 ${updates.length}件を送信不可（✕）に更新しました`);
    } else {
        console.log('対象データが見つかりませんでした。');
        console.log('タイムスタンプ形式を確認してください。');
        // サンプル表示
        console.log('\nN列サンプル（行2-6）:');
        for (let i = 1; i <= Math.min(5, allRows.length - 1); i++) {
            console.log(`  行${i+1}: "${allRows[i][nIdx] || '(空)'}"`);
        }
        // 末尾サンプル
        console.log('\nN列サンプル（末尾5行）:');
        for (let i = Math.max(1, allRows.length - 5); i < allRows.length; i++) {
            console.log(`  行${i+1}: "${allRows[i][nIdx] || '(空)'}"`);
        }
    }
})().catch(e => console.error(e));
