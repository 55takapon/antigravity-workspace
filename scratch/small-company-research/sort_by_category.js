/**
 * sort_by_category.js
 * 送信対象/送信不可の並び替え + カテゴリ別ソート
 *
 * 【判定基準】schema.js の isSendable() に完全に依拠する。
 *   - I列が空欄 → 送信対象
 *   - I列が「OK」or「【手動承認】*」→ 送信対象
 *   - I列がそれ以外（【静的NG】, 【動的NG】, 【営業NG】, 【自動判定】等）→ 送信不可
 *
 * Usage:
 *   node sort_by_category.js
 *   node sort_by_category.js --sheet Webマーケティング
 */

'use strict';

const {
    SPREADSHEET_ID, TARGET_SHEETS, COL,
    isSendable, getGoogleSheetsClient,
} = require('./schema');

const args = process.argv.slice(2);
const sheetIdx = args.indexOf('--sheet');
const targetSheets = sheetIdx !== -1 ? [args[sheetIdx + 1]] : TARGET_SHEETS;

function sortRows(dataRows) {
    const sendable = [];
    const notSendable = [];

    for (const row of dataRows) {
        const colI = (row[COL.REJECT_REASON] || '').trim();
        if (isSendable(colI)) {
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
        const colO = (row[COL.CATEGORY] || '').trim();
        if (colO === 'web_production') production.push(row);
        else if (colO === 'hybrid') hybrid.push(row);
        else if (colO === 'web_marketing') marketing.push(row);
        else others.push(row);
    }

    const sortedSendable = [...production, ...hybrid, ...marketing, ...others];

    return {
        sortedSendable, notSendable,
        counts: {
            production: production.length,
            hybrid: hybrid.length,
            marketing: marketing.length,
            others: others.length,
            ng: notSendable.length,
        },
    };
}

async function processSheet(sheets, sheetName) {
    console.log(`\n=== ${sheetName} の並び替え開始 ===`);
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });
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
        requestBody: { values: paddedRows },
    });
    console.log(`✅ ${sheetName} の並び替え完了！`);
}

async function main() {
    console.log('========================================');
    console.log('  カテゴリ別並び替え');
    console.log(`  対象: ${targetSheets.join(', ')}`);
    console.log('========================================');

    const sheets = await getGoogleSheetsClient();
    for (const sheetName of targetSheets) {
        await processSheet(sheets, sheetName);
    }
}

main().catch(e => { console.error('エラー:', e.message); process.exit(1); });
