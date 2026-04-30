/**
 * _check_col_o.js
 * Webマーケティングシートの列O（index=14）の値を集計して表示
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング';

async function main() {
    const sheets = await getGoogleSheetsClient();
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET,
    });

    const allRows = res.data.values || [];
    if (allRows.length <= 1) { console.log('データなし'); return; }

    const header = allRows[0];
    console.log(`列O ヘッダー: "${header[14] || '(空)'}"`);
    console.log(`総データ行数: ${allRows.length - 1}`);
    console.log('');

    // 列Oの値を集計
    const countMap = {};
    const examples = {}; // 各値の例（最初の3社名）

    for (let i = 1; i < allRows.length; i++) {
        const row = allRows[i];
        const colO = (row[14] || '').trim();
        const company = (row[2] || '').trim(); // 列C=社名

        if (!countMap[colO]) {
            countMap[colO] = 0;
            examples[colO] = [];
        }
        countMap[colO]++;
        if (examples[colO].length < 3) examples[colO].push(company);
    }

    // 多い順にソート
    const sorted = Object.entries(countMap).sort((a, b) => b[1] - a[1]);

    console.log('=== 列O の値一覧（多い順） ===');
    for (const [val, count] of sorted) {
        const label = val === '' ? '(空欄)' : val;
        const ex = examples[val].join(', ');
        console.log(`  "${label}": ${count}件  例: ${ex}`);
    }
}

main().catch(e => console.error('エラー:', e.message));
