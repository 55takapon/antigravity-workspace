/**
 * duplicate_checker.js
 * シート内およびシート間の重複チェックと削除
 *
 * 【識別キー】ドメイン（schema.js の normalizeDomain）
 *
 * Usage:
 *   node duplicate_checker.js                # レポートのみ
 *   node duplicate_checker.js --execute      # 実際に削除
 */

'use strict';

const {
    SPREADSHEET_ID, TARGET_SHEETS, COL,
    normalizeDomain, getGoogleSheetsClient,
} = require('./schema');

async function main() {
    console.log('========================================');
    console.log('  重複チェッカー');
    console.log('========================================\n');

    const sheets = await getGoogleSheetsClient();

    // スプレッドシート情報取得
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    const allSheetNames = spreadsheet.data.sheets.map(s => s.properties.title);
    const baseSheets = allSheetNames.filter(name => !TARGET_SHEETS.includes(name));

    console.log(`ベースシート: ${baseSheets.join(', ')}`);
    console.log(`ターゲットシート: ${TARGET_SHEETS.join(', ')}\n`);

    const seenNames = new Map();   // normalized_name -> sheet_name
    const seenDomains = new Map(); // domain -> sheet_name

    const normalizeName = (name) => {
        if (!name) return '';
        return name.replace(/[\s　]/g, '').replace(/[（(].*?[)）]/g, '').toLowerCase();
    };

    // ベースシート読み込み
    for (const sheetName of baseSheets) {
        try {
            const res = await sheets.spreadsheets.values.get({
                spreadsheetId: SPREADSHEET_ID,
                range: `${sheetName}!A:E`,
            });
            const rows = res.data.values || [];
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const name = normalizeName(row[COL.COMPANY_NAME]);
                const domain = normalizeDomain(row[COL.URL]);
                if (name) seenNames.set(name, sheetName);
                if (domain) seenDomains.set(domain, sheetName);
            }
        } catch (e) {
            console.error(`ベースシート ${sheetName} 読み込みエラー: ${e.message}`);
        }
    }

    console.log(`ベースデータ: ${seenNames.size}社名 / ${seenDomains.size}ドメイン\n`);

    // ターゲットシート処理
    const report = {};
    const deleteRequests = [];

    for (const sheetName of TARGET_SHEETS) {
        if (!allSheetNames.includes(sheetName)) {
            console.log(`シート ${sheetName} が見つかりません。スキップ。`);
            continue;
        }

        const sheetId = spreadsheet.data.sheets
            .find(s => s.properties.title === sheetName).properties.sheetId;

        report[sheetName] = { total: 0, duplicates: [] };

        const res = await sheets.spreadsheets.values.get({
            spreadsheetId: SPREADSHEET_ID,
            range: `${sheetName}!A:E`,
        });

        const rows = res.data.values || [];
        report[sheetName].total = rows.length <= 1 ? 0 : rows.length - 1;

        // 後ろから処理（削除時のインデックスずれ防止）
        for (let i = rows.length - 1; i >= 1; i--) {
            const row = rows[i];
            const name = normalizeName(row[COL.COMPANY_NAME]);
            const domain = normalizeDomain(row[COL.URL]);

            let isDuplicate = false;
            let dupSource = '';

            if (name && seenNames.has(name)) {
                isDuplicate = true;
                dupSource = seenNames.get(name);
            } else if (domain && seenDomains.has(domain)) {
                isDuplicate = true;
                dupSource = seenDomains.get(domain);
            }

            if (isDuplicate) {
                report[sheetName].duplicates.push({
                    row: i + 1,
                    name: row[COL.COMPANY_NAME],
                    reason: `重複: ${dupSource}`,
                });
                deleteRequests.push({
                    deleteDimension: {
                        range: {
                            sheetId,
                            dimension: 'ROWS',
                            startIndex: i,
                            endIndex: i + 1,
                        },
                    },
                });
            } else {
                if (name) seenNames.set(name, sheetName);
                if (domain) seenDomains.set(domain, sheetName);
            }
        }
    }

    // レポート出力
    console.log('\n--- 重複レポート ---');
    let totalDups = 0;
    for (const sheetName of TARGET_SHEETS) {
        if (!report[sheetName]) continue;
        const stats = report[sheetName];
        console.log(`\nシート: ${sheetName}`);
        console.log(`  全行数: ${stats.total}`);
        console.log(`  重複: ${stats.duplicates.length}件`);
        totalDups += stats.duplicates.length;
        stats.duplicates.forEach(d => console.log(`    - 行${d.row}: ${d.name} (${d.reason})`));
    }

    console.log(`\n合計重複: ${totalDups}件`);

    if (process.argv.includes('--execute')) {
        if (deleteRequests.length > 0) {
            console.log(`\n${deleteRequests.length}件の行を削除中...`);
            await sheets.spreadsheets.batchUpdate({
                spreadsheetId: SPREADSHEET_ID,
                resource: { requests: deleteRequests },
            });
            console.log('✅ 削除完了');
        } else {
            console.log('削除対象なし');
        }
    } else {
        console.log('\n--execute オプションで実際に削除します。');
    }
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
