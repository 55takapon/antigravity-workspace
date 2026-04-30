/**
 * sort_by_category.js
 * 「送信対象」の行について、列O（index=14）の値を基準に
 * 1. web_production
 * 2. hybrid
 * 3. web_marketing
 * 4. その他（空欄など）
 * の順に並び替え、その下に「送信不可」の行を配置する。
 */
const { getGoogleSheetsClient } = require('./sheets_writer');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEETS = ['Webマーケティング', 'Webマーケティング_名古屋'];

function sortRows(dataRows) {
    const sendable = [];
    const notSendable = [];

    // まず送信可否で分割
    for (const row of dataRows) {
        const colI = (row[8] || '').trim();
        if (colI === '') {
            sendable.push(row);
        } else {
            notSendable.push(row);
        }
    }

    // 送信対象をカテゴリ別に分類
    const production = [];
    const hybrid = [];
    const marketing = [];
    const others = [];

    for (const row of sendable) {
        const colO = (row[14] || '').trim();
        if (colO === 'web_production') {
            production.push(row);
        } else if (colO === 'hybrid') {
            hybrid.push(row);
        } else if (colO === 'web_marketing') {
            marketing.push(row);
        } else {
            others.push(row);
        }
    }

    // 指定の順序で結合
    const sortedSendable = [...production, ...hybrid, ...marketing, ...others];
    
    return { sortedSendable, notSendable, counts: {
        production: production.length,
        hybrid: hybrid.length,
        marketing: marketing.length,
        others: others.length,
        ng: notSendable.length
    }};
}

async function processSheet(sheets, sheetName) {
    console.log(`\n=== ${sheetName} の並び替え開始 ===`);
    const res = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: sheetName });
    const allRows = res.data.values || [];
    if (allRows.length <= 1) {
        console.log('データなし');
        return;
    }

    const header = allRows[0];
    const dataRows = allRows.slice(1);

    const { sortedSendable, notSendable, counts } = sortRows(dataRows);

    console.log(`✅ 送信対象: ${sortedSendable.length}件`);
    console.log(`  - web_production: ${counts.production}件`);
    console.log(`  - hybrid:         ${counts.hybrid}件`);
    console.log(`  - web_marketing:  ${counts.marketing}件`);
    console.log(`  - その他(空欄等): ${counts.others}件`);
    console.log(`❌ 送信不可: ${counts.ng}件`);

    const sortedRows = [header, ...sortedSendable, ...notSendable];
    const maxCols = sortedRows.reduce((max, row) => Math.max(max, row.length), 0);
    const paddedRows = sortedRows.map(row => {
        const r = [...row];
        while (r.length < maxCols) r.push('');
        return r;
    });

    await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: `${sheetName}!A1`,
        valueInputOption: 'USER_ENTERED',
        requestBody: { values: paddedRows }
    });
    console.log(`✅ ${sheetName} の並び替え完了！`);
}

async function main() {
    const sheets = await getGoogleSheetsClient();
    for (const sheetName of TARGET_SHEETS) {
        await processSheet(sheets, sheetName);
    }
}

main().catch(e => console.error('エラー:', e.message));
