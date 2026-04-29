/**
 * fix_name_noise.js
 * 新しく強化された isValidCompanyName と NG_INDUSTRY_KEYWORDS に基づいて
 * 既存シートのゴミテキスト企業（C株式会社、株式会社設立等）、および飼料系企業を削除。
 * また、企業名に「様」などのゴミが残っているものをクリーニングして上書きする。
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEETS = ['Webマーケティング', 'Webマーケティング_名古屋', 'クリニック専門支援'];
const EXCLUDE_SHEET = '除外リスト';

async function fixNameNoise(sheets, sheetName) {
    // キャッシュクリアして最新のcrawler.jsを読み込む
    delete require.cache[require.resolve('./crawler')];
    const { isNGIndustry, isValidCompanyName, isListedCorporation, cleanCompanyName } = require('./crawler');

    console.log(`\n=== シート: ${sheetName} のノイズ修正を開始 ===`);
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });
    const allRows = res.data.values || [];
    if (allRows.length <= 1) return { toDelete: [], toUpdate: [] };
    
    const header  = allRows[0];
    const nameCol = header.indexOf('企業名');
    const urlCol  = header.indexOf('ホームページURL');

    const toDelete = [];
    const toUpdate = [];
    
    for (let i = 1; i < allRows.length; i++) {
        const row    = allRows[i];
        let name     = (row[nameCol] || '').trim();
        const url    = (row[urlCol]  || '').trim();
        const rowNum = i + 1;

        if (!name) continue;

        // 1. まず現在の名前でNG判定（「田中飼料株式会社」など）
        let reason = null;
        if (!isValidCompanyName(name)) {
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
            continue; // 削除対象なら更新はしない
        }

        // 2. クリーニングの適用（「株式会社note様」→「株式会社note」）
        const cleaned = cleanCompanyName(name);
        if (cleaned !== name) {
            // クリーニング後、もし無効になってしまったら削除
            if (!cleaned || cleaned.length < 3 || !isValidCompanyName(cleaned)) {
                toDelete.push({ rowNum, name, url, reason: `クリーニング後無効: ${cleaned}` });
            } else {
                // 有効なら更新リストへ
                toUpdate.push({ rowNum, oldName: name, newName: cleaned });
            }
        }
    }

    if (toDelete.length > 0) {
        console.log(`\n[${sheetName}] 削除対象: ${toDelete.length}件`);
        toDelete.forEach(r => console.log(`  行${r.rowNum}: 「${r.name}」→ ${r.reason}`));
    }
    if (toUpdate.length > 0) {
        console.log(`\n[${sheetName}] 更新対象: ${toUpdate.length}件`);
        toUpdate.forEach(r => console.log(`  行${r.rowNum}: 「${r.oldName}」→ 「${r.newName}」`));
    }

    return { toDelete, toUpdate };
}

async function main() {
    const sheets = await getGoogleSheetsClient();

    let allToDelete = [];
    let allToUpdate = [];
    for (const sheetName of TARGET_SHEETS) {
        const { toDelete, toUpdate } = await fixNameNoise(sheets, sheetName);
        if (toDelete.length > 0) allToDelete.push({ sheetName, rows: toDelete });
        if (toUpdate.length > 0) allToUpdate.push({ sheetName, rows: toUpdate });
    }

    // --- 削除処理 ---
    if (allToDelete.length > 0) {
        const exRes = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: EXCLUDE_SHEET });
        const existingNames = new Set((exRes.data.values || []).slice(1).map(r => (r[0] || '').trim()));
        
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

        const meta = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
        for (const { sheetName, rows } of allToDelete) {
            const sheetId = meta.data.sheets.find(s => s.properties.title === sheetName).properties.sheetId;
            const requests = [...rows].sort((a, b) => b.rowNum - a.rowNum).map(r => ({
                deleteDimension: { range: { sheetId, dimension: 'ROWS', startIndex: r.rowNum - 1, endIndex: r.rowNum } },
            }));
            await sheets.spreadsheets.batchUpdate({ spreadsheetId: SPREADSHEET_ID, requestBody: { requests } });
            console.log(`シート「${sheetName}」から${rows.length}行を削除完了`);
        }
    }

    // --- 更新処理 ---
    if (allToUpdate.length > 0) {
        for (const { sheetName, rows } of allToUpdate) {
            const updates = rows.map(r => ({
                range: `${sheetName}!C${r.rowNum}`,
                values: [[r.newName]],
            }));
            const data = updates.map(u => ({ range: u.range, values: u.values }));
            await sheets.spreadsheets.values.batchUpdate({
                spreadsheetId: SPREADSHEET_ID,
                requestBody: { valueInputOption: 'USER_ENTERED', data: data }
            });
            console.log(`シート「${sheetName}」で${rows.length}件の企業名を修正（様等の除去）完了`);
        }
    }
}

main().catch(e => { console.error(e.message); process.exit(1); });
