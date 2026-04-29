/**
 * apply_auto_reject.js
 * 既存のシートに対して「従業員20名以上」「資本金1000万円以上」の自動判定ルールを遡及適用する
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEETS = ['Webマーケティング', 'Webマーケティング_名古屋', 'クリニック専門支援'];

// 資本金を数値（円）に変換するヘルパー
const parseCapital = (raw) => {
    if (!raw || raw === '不明') return 0;
    const str = String(raw).replace(/,/g, '').replace(/\s/g, '');
    let num = parseFloat(str) || 0;
    if (str.includes('億')) num *= 100000000;
    else if (str.includes('万')) num *= 10000;
    return num;
};

async function applyAutoReject(sheets, sheetName) {
    console.log(`\n=== シート: ${sheetName} の遡及適用を開始 ===`);
    try {
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
        
        // ヘッダー行をスキップしてループ
        for (let i = 1; i < allRows.length; i++) {
            const row = allRows[i];
            
            // 行データが不足している場合はパディング
            while (row.length < 14) row.push('');

            const currentH  = (row[7]  || '').trim();
            const currentI  = (row[8]  || '').trim();
            const rawEmp    = (row[9]  || '').trim();
            const rawCap    = (row[10] || '').trim();
            const kwHit     = (row[11] || '').trim(); // L列: キーワードHIT（なし/あり）

            // すでに自動判定済みの場合はスキップ
            if (currentH === '✕' && currentI.includes('自動判定')) continue;

            const empCount = (rawEmp && rawEmp !== '不明') ? parseInt(rawEmp.replace(/,/g, ''), 10) : null;
            const capNum = parseCapital(rawCap);

            let autoEvaluation = '';
            let autoReason = '';

            // === ポジティブフィルター（キーワードHIT必須） ===
            // Webマーケ系キーワードがHP上に存在しない = 業種が違う可能性が高い
            // 業種NGキーワードリストに頼らず、「Webマーケ会社である証拠がない」で弾く
            if (kwHit === '×') {
                autoEvaluation = '✕';
                autoReason = '【自動判定】キーワード未検出（Webマーケ非該当の可能性）';
            }
            // === 規模判定 ===
            else if ((empCount !== null && !isNaN(empCount) && empCount >= 20) || capNum >= 10000000) {
                autoEvaluation = '✕';
                if (empCount !== null && !isNaN(empCount) && empCount >= 20) {
                    autoReason = '【自動判定】従業員20名以上';
                } else {
                    autoReason = '【自動判定】資本金1000万円以上';
                }
            }

            if (!autoEvaluation) continue;

            // 現在の値と異なる場合のみ更新リストに追加
            if (currentH !== autoEvaluation || !currentI.includes('自動判定')) {
                let finalReason = autoReason;
                if (currentI && !currentI.includes('自動判定')) {
                    finalReason = `${currentI} / ${autoReason}`;
                }

                const rowNum = i + 1;
                updates.push({
                    range: `${sheetName}!H${rowNum}:I${rowNum}`,
                    values: [[autoEvaluation, finalReason]],
                    name: row[2] || '不明',
                    reason: finalReason
                });
            }
        }

        console.log(`更新対象: ${updates.length}件`);
        if (updates.length === 0) return;

        // ログ出力
        for (const u of updates) {
            console.log(`  [更新] ${u.name} -> ${u.reason}`);
        }

        // バッチアップデート
        const data = updates.map(u => ({ range: u.range, values: u.values }));
        await sheets.spreadsheets.values.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: {
                valueInputOption: 'USER_ENTERED',
                data: data
            }
        });
        console.log(`シート ${sheetName} の自動判定適用完了`);
    } catch (e) {
        console.error(`シート ${sheetName} の処理中にエラー: ${e.message}`);
    }
}

async function main() {
    const sheets = await getGoogleSheetsClient();
    for (const sheetName of TARGET_SHEETS) {
        await applyAutoReject(sheets, sheetName);
    }
}

main().catch(e => console.error(e.message));
