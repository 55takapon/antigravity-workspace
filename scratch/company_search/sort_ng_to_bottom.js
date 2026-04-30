/**
 * sort_ng_to_bottom.js
 * 「Webマーケティング」シートの行を並び替える
 * 列I（送信不可理由）が空 → 上（送信対象）
 * 列I（送信不可理由）に文字あり → 下（送信不可）
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング';

async function main() {
    console.log(`=== ${TARGET_SHEET} の並び替え開始 ===`);
    const sheets = await getGoogleSheetsClient();

    // シート全体取得
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET,
    });

    const allRows = res.data.values || [];
    if (allRows.length <= 1) {
        console.log('データがありません');
        return;
    }

    const header = allRows[0];
    const dataRows = allRows.slice(1);

    console.log(`総データ行数: ${dataRows.length}`);

    // 列I（index=8）が空かどうかで分類
    const sendable = [];    // 送信対象（列I が空）
    const notSendable = []; // 送信不可（列I に文字あり）

    for (const row of dataRows) {
        const colI = (row[8] || '').trim();
        if (colI === '') {
            sendable.push(row);
        } else {
            notSendable.push(row);
        }
    }

    console.log(`✅ 送信対象: ${sendable.length}件`);
    console.log(`❌ 送信不可: ${notSendable.length}件`);

    // 並び替え後の全データ（ヘッダー＋送信対象＋送信不可）
    const sortedRows = [header, ...sendable, ...notSendable];

    // 全列数を確認（最大列数）
    const maxCols = sortedRows.reduce((max, row) => Math.max(max, row.length), 0);

    // 各行を最大列数に揃える（短い行は空文字でパディング）
    const paddedRows = sortedRows.map(row => {
        const r = [...row];
        while (r.length < maxCols) r.push('');
        return r;
    });

    // シートに書き戻す
    await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: `${TARGET_SHEET}!A1`,
        valueInputOption: 'USER_ENTERED',
        requestBody: {
            values: paddedRows,
        },
    });

    console.log(`\n✅ 並び替え完了！`);
    console.log(`  上から ${sendable.length}行: 送信対象（列I が空）`);
    console.log(`  下から ${notSendable.length}行: 送信不可（列I に文字あり）`);
}

main().catch(e => console.error('エラー:', e.message));
