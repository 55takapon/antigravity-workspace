/**
 * sweep_all.js
 * サイレントエラーで適用が漏れていたv2.5〜v2.7のパッチ（総研、ISP、医療、不動産など数十のNGキーワード）を
 * 既存シート（Webマーケティング、名古屋、クリニック）の全件に徹底的に再適用して一掃する。
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEETS = ['Webマーケティング', 'Webマーケティング_名古屋', 'クリニック専門支援'];
const EXCLUDE_SHEET = '除外リスト';

async function sweepSheet(sheets, sheetName) {
    // 最新のcrawler.jsを読み込む（キャッシュクリアが必要な場合は別途対応するが、今回起動したプロセスなら問題ない）
    delete require.cache[require.resolve('./crawler')];
    const { isNGIndustry, isValidCompanyName, isListedCorporation } = require('./crawler');

    console.log(`\n=== シート: ${sheetName} の徹底スキャンを開始 ===`);
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });
    const allRows = res.data.values || [];
    if (allRows.length <= 1) return [];
    
    const header  = allRows[0];
    const nameCol = header.indexOf('企業名');
    const urlCol  = header.indexOf('ホームページURL');

    const toDelete = [];
    
    for (let i = 1; i < allRows.length; i++) {
        const row    = allRows[i];
        const name   = (row[nameCol] || '').trim();
        const url    = (row[urlCol]  || '').trim();
        const rowNum = i + 1;

        let reason = null;
        if (!name) {
            reason = '企業名なし';
        } else if (!isValidCompanyName(name)) {
            reason = '企業名無効';
        } else if (isListedCorporation(name)) {
            reason = '上場企業キーワード検出';
        } else {
            const industryCheck = isNGIndustry(name);
            if (industryCheck.blocked) {
                reason = 'NG業種:' + industryCheck.reason;
            }
        }

        if (reason) {
            toDelete.push({ rowNum, name, url, reason });
        }
    }

    if (toDelete.length > 0) {
        console.log(`\n[${sheetName}] 削除対象: ${toDelete.length}件`);
        toDelete.forEach(r => console.log(`  行${r.rowNum}: 「${r.name}」→ ${r.reason}`));
    } else {
        console.log(`削除対象なし`);
    }
    return toDelete;
}

async function main() {
    const sheets = await getGoogleSheetsClient();

    let allToDelete = [];
    for (const sheetName of TARGET_SHEETS) {
        const toDelete = await sweepSheet(sheets, sheetName);
        if (toDelete.length > 0) {
            allToDelete.push({ sheetName, rows: toDelete });
        }
    }

    if (allToDelete.length === 0) {
        console.log('完全クリーンアップ完了。削除対象は見つかりませんでした。');
        return;
    }

    // 除外リストに追記
    const exRes = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: EXCLUDE_SHEET,
    });
    const existingNames = new Set(
        (exRes.data.values || []).slice(1).map(r => (r[0] || '').trim())
    );
    
    const today = new Date().toLocaleDateString('ja-JP');
    const toAdd = [];
    allToDelete.forEach(({ rows }) => {
        rows.forEach(r => {
            if (r.name && !existingNames.has(r.name)) {
                toAdd.push([r.name, '', r.url, r.reason, today]);
                existingNames.add(r.name);
            }
        });
    });

    if (toAdd.length > 0) {
        await sheets.spreadsheets.values.append({
            spreadsheetId: SPREADSHEET_ID,
            range: `${EXCLUDE_SHEET}!A:E`,
            valueInputOption: 'RAW',
            requestBody: { values: toAdd },
        });
        console.log(`\n除外リストに${toAdd.length}件追記`);
    }

    // シートから削除（シート毎に降順で実行）
    const meta = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    
    for (const { sheetName, rows } of allToDelete) {
        const sheetId = meta.data.sheets.find(s => s.properties.title === sheetName).properties.sheetId;
        const requests = [...rows].sort((a, b) => b.rowNum - a.rowNum).map(r => ({
            deleteDimension: {
                range: { sheetId, dimension: 'ROWS', startIndex: r.rowNum - 1, endIndex: r.rowNum },
            },
        }));
        
        await sheets.spreadsheets.batchUpdate({ spreadsheetId: SPREADSHEET_ID, requestBody: { requests } });
        console.log(`シート「${sheetName}」から${rows.length}行を削除完了`);
    }
}

main().catch(e => { console.error(e.message); process.exit(1); });
