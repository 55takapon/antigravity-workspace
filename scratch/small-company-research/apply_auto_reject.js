/**
 * apply_auto_reject.js
 * 静的チェック: 資本金・従業員数・キーワード・業種に基づく自動NG判定
 *
 * 【鉄則】I列（送信不可理由）が空欄の行にのみ書き込む。
 *         既に値がある行は絶対にスキップする。消去機能は存在しない。
 *
 * Usage:
 *   node apply_auto_reject.js                  # 全シート対象
 *   node apply_auto_reject.js --dry-run        # テスト（書き込みなし）
 *   node apply_auto_reject.js --sheet Webマーケティング
 */

'use strict';

const {
    SPREADSHEET_ID, TARGET_SHEETS, COL, NG_PREFIX,
    isWritable, getGoogleSheetsClient, parseCapital,
} = require('./schema');

const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const sheetIdx = args.indexOf('--sheet');
const targetSheets = sheetIdx !== -1 ? [args[sheetIdx + 1]] : TARGET_SHEETS;

async function processSheet(sheets, sheetName) {
    console.log(`\n=== シート: ${sheetName} の静的チェック開始 ===`);

    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });
    const allRows = res.data.values || [];
    if (allRows.length <= 1) {
        console.log('データがありません');
        return;
    }

    const updates = [];

    for (let i = 1; i < allRows.length; i++) {
        const row = allRows[i];
        while (row.length < 16) row.push('');

        const currentI = (row[COL.REJECT_REASON] || '').trim();

        // ★ 鉄則: I列が空欄でなければスキップ
        if (!isWritable(currentI)) continue;

        const rawEmp  = (row[COL.EMPLOYEES] || '').trim();
        const rawCap  = (row[COL.CAPITAL] || '').trim();
        const kwHit   = (row[COL.KW_HIT] || '').trim();
        const colO    = (row[COL.CATEGORY] || '').trim();
        const name    = (row[COL.COMPANY_NAME] || '').trim();

        const empCount = (rawEmp && rawEmp !== '不明') ? parseInt(rawEmp.replace(/,/g, ''), 10) : null;
        const capNum = parseCapital(rawCap);

        let reason = '';

        // 判定1: キーワードHITなし
        if (kwHit === '×') {
            reason = `${NG_PREFIX.STATIC}キーワード未検出（Webマーケ非該当の可能性）`;
        }
        // 判定2: 業種違い
        else if (colO === '業種違い') {
            reason = `${NG_PREFIX.STATIC}業種違い`;
        }
        // 判定3: 従業員20名以上
        else if (empCount !== null && !isNaN(empCount) && empCount >= 20) {
            reason = `${NG_PREFIX.STATIC}従業員${empCount}名（20名以上）`;
        }
        // 判定4: 資本金1000万円以上
        else if (capNum >= 10000000) {
            reason = `${NG_PREFIX.STATIC}資本金${rawCap}（1000万円以上）`;
        }

        if (!reason) continue;

        const rowNum = i + 1;
        updates.push({
            range: `${sheetName}!H${rowNum}:I${rowNum}`,
            values: [['✕', reason]],
            name,
            reason,
        });
    }

    console.log(`更新対象: ${updates.length}件`);
    if (updates.length === 0) return;

    for (const u of updates) {
        console.log(`  [${isDryRun ? 'DRY' : '更新'}] ${u.name} → ${u.reason}`);
    }

    if (!isDryRun) {
        await sheets.spreadsheets.values.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: {
                valueInputOption: 'USER_ENTERED',
                data: updates.map(u => ({ range: u.range, values: u.values })),
            },
        });
        console.log(`✅ シート ${sheetName} の静的チェック完了（${updates.length}件書き込み）`);
    }
}

async function main() {
    console.log('========================================');
    console.log('  静的チェック（apply_auto_reject）');
    console.log(`  モード: ${isDryRun ? 'ドライラン' : '本番'}`);
    console.log(`  対象: ${targetSheets.join(', ')}`);
    console.log('========================================');

    const sheets = await getGoogleSheetsClient();
    for (const sheetName of targetSheets) {
        await processSheet(sheets, sheetName);
    }
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
