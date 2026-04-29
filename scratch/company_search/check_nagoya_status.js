/**
 * check_nagoya_status.js - 名古屋シートの現在の状態を確認
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

async function main() {
    const sheets = await getGoogleSheetsClient();

    // 1. 全シート一覧
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    console.log('=== シート一覧 ===');
    for (const s of spreadsheet.data.sheets) {
        const title = s.properties.title;
        const rows = s.properties.gridProperties.rowCount;
        const cols = s.properties.gridProperties.columnCount;
        console.log(`  - ${title} (${rows}行 x ${cols}列)`);
    }

    // 2. 名古屋シートのデータ確認
    const NAGOYA_CANDIDATES = ['Webマーケティング_名古屋', 'Webマーケティング'];
    
    for (const sheetName of NAGOYA_CANDIDATES) {
        try {
            const response = await sheets.spreadsheets.values.get({
                spreadsheetId: SPREADSHEET_ID,
                range: sheetName,
            });
            const allRows = response.data.values || [];
            if (allRows.length <= 1) {
                console.log(`\n=== ${sheetName}: データなし ===`);
                continue;
            }
            const header = allRows[0];
            const dataRows = allRows.slice(1);
            
            console.log(`\n=== ${sheetName} ===`);
            console.log(`ヘッダー: ${header.join(' | ')}`);
            console.log(`データ行: ${dataRows.length}件`);
            
            // 先頭5件
            console.log('\n[先頭5件]');
            for (let i = 0; i < Math.min(5, dataRows.length); i++) {
                const row = dataRows[i];
                console.log(`  #${i+1}: ${(row[2]||'').trim()} | ${(row[4]||'').substring(0,50)} | 代表:${(row[3]||'').trim()} | form:${(row[5]||'').substring(0,40)}`);
            }
            
            // 末尾5件
            console.log('\n[末尾5件]');
            for (let i = Math.max(0, dataRows.length-5); i < dataRows.length; i++) {
                const row = dataRows[i];
                console.log(`  #${i+1}: ${(row[2]||'').trim()} | ${(row[4]||'').substring(0,50)} | 代表:${(row[3]||'').trim()} | form:${(row[5]||'').substring(0,40)}`);
            }
            
            // 統計
            let empKnown = 0, empUnknown = 0, formYes = 0, formNo = 0, repName = 0, repDefault = 0;
            let ngReasonCount = 0;
            for (const row of dataRows) {
                const emp = (row[9] || '').trim();
                const form = (row[5] || '').trim();
                const rep = (row[3] || '').trim();
                const ngReason = (row[8] || '').trim();
                if (emp && emp !== '不明' && emp !== 'null') empKnown++; else empUnknown++;
                if (form) formYes++; else formNo++;
                if (rep && rep !== 'ご担当者') repName++; else repDefault++;
                if (ngReason) ngReasonCount++;
            }
            console.log(`\n[統計]`);
            console.log(`  従業員数: 取得${empKnown} / 不明${empUnknown}`);
            console.log(`  フォームURL: あり${formYes} / なし${formNo}`);
            console.log(`  代表者名: フルネーム${repName} / ご担当者${repDefault}`);
            console.log(`  送信不可理由: ${ngReasonCount}件記入済み`);
        } catch (err) {
            console.log(`\n=== ${sheetName}: エラー (${err.message.substring(0, 80)}) ===`);
        }
    }
}

main().catch(err => { console.error(err.message); process.exit(1); });
