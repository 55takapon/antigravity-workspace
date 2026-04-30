/**
 * apply_gyoshu_chigai.js
 * 列O（index=14）が「業種違い」の行に対して
 * 列H → ✕、列I → 【自動判定】業種違い を適用する
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEETS = ['Webマーケティング', 'Webマーケティング_名古屋'];

async function applyGyoshuChigai(sheets, sheetName) {
    console.log(`\n=== シート: ${sheetName} の業種違い適用開始 ===`);

    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });

    const allRows = res.data.values || [];
    if (allRows.length <= 1) { console.log('データなし'); return; }

    const updates = [];

    for (let i = 1; i < allRows.length; i++) {
        const row = allRows[i];
        while (row.length < 15) row.push('');

        const currentH = (row[7]  || '').trim(); // 列H
        const currentI = (row[8]  || '').trim(); // 列I
        const colO     = (row[14] || '').trim(); // 列O

        // 列O が「業種違い」でない場合はスキップ
        if (colO !== '業種違い') continue;

        // すでに業種違い判定済みの場合はスキップ
        if (currentH === '✕' && currentI.includes('業種違い')) continue;

        let finalReason = '【自動判定】業種違い';
        // 既存の理由がある場合は追記
        if (currentI && !currentI.includes('業種違い')) {
            finalReason = `${currentI} / 【自動判定】業種違い`;
        }

        const rowNum = i + 1;
        updates.push({
            range: `${sheetName}!H${rowNum}:I${rowNum}`,
            values: [['✕', finalReason]],
            name: row[2] || '不明',
            reason: finalReason,
        });
    }

    console.log(`更新対象: ${updates.length}件`);
    if (updates.length === 0) return;

    for (const u of updates) {
        console.log(`  [更新] ${u.name} -> ${u.reason}`);
    }

    await sheets.spreadsheets.values.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        requestBody: {
            valueInputOption: 'USER_ENTERED',
            data: updates.map(u => ({ range: u.range, values: u.values })),
        },
    });

    console.log(`シート ${sheetName} の業種違い適用完了`);
}

async function main() {
    const sheets = await getGoogleSheetsClient();
    for (const sheetName of TARGET_SHEETS) {
        await applyGyoshuChigai(sheets, sheetName);
    }
    console.log('\n=== 全シート処理完了 ===');
}

main().catch(e => console.error('エラー:', e.message));
