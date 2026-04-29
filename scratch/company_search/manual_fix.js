/**
 * manual_fix.js - 目視チェックで発見した問題の修正
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング';

async function main() {
    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const dataRows = allRows.slice(1);

    console.log(`全${dataRows.length}件をチェック\n`);

    const deleteIndices = [];
    const fixList = [];

    for (let i = 0; i < dataRows.length; i++) {
        const name = (dataRows[i][2] || '').trim();
        const url = (dataRows[i][4] || '').trim();
        let domain = '';
        try { domain = new URL(url).hostname.toLowerCase(); } catch {}

        // === 削除対象 ===
        
        // 1. 企業名に「@@」「×」等の装飾記号が含まれる（サービス名・タグライン）
        if (/[×@＠]/.test(name)) {
            console.log(`  削除: #${i+1} "${name}" - 装飾記号/サービス名`);
            deleteIndices.push(i);
            continue;
        }

        // 2. 「株式会社tps」のような明らかに不正な名前
        if (/^株式会社[a-z]{2,4}$/.test(name) && !/^株式会社[A-Z]/.test(name)) {
            console.log(`  削除: #${i+1} "${name}" - 不正な英字のみ企業名`);
            deleteIndices.push(i);
            continue;
        }

        // 3. URL-企業名の明白な不一致
        // 株式会社100 -> pensees.co.jp (PENSEESは別会社)
        if (name === '株式会社100' && domain.includes('pensees')) {
            console.log(`  削除: #${i+1} "${name}" -> ${domain} (URL不一致)`);
            deleteIndices.push(i);
            continue;
        }
        // 株式会社インタビュー動画 -> web-meister.jp
        if (name.includes('インタビュー動画') && domain.includes('web-meister')) {
            console.log(`  削除: #${i+1} "${name}" -> ${domain} (URL不一致)`);
            deleteIndices.push(i);
            continue;
        }

        // === 修正対象 ===
        
        // 4. 「会社概要」が社名に混入
        if (/会社概要/.test(name)) {
            const fixed = name.replace(/会社概要/g, '').trim();
            console.log(`  修正: #${i+1} "${name}" -> "${fixed}"`);
            fixList.push({ row: i + 2, col: 'C', value: fixed });
        }

        // 5. 末尾のハイフン除去
        if (/[-－ー]$/.test(name)) {
            const fixed = name.replace(/[-－ー]+$/, '').trim();
            console.log(`  修正: #${i+1} "${name}" -> "${fixed}"`);
            fixList.push({ row: i + 2, col: 'C', value: fixed });
        }
    }

    console.log(`\n削除: ${deleteIndices.length}件, 修正: ${fixList.length}件\n`);

    // 修正実行
    for (const fix of fixList) {
        await sheets.spreadsheets.values.update({
            spreadsheetId: SPREADSHEET_ID,
            range: `${SHEET_NAME}!${fix.col}${fix.row}`,
            valueInputOption: 'USER_ENTERED',
            requestBody: { values: [[fix.value]] },
        });
        console.log(`  修正完了: ${fix.col}${fix.row} = "${fix.value}"`);
    }

    // 削除実行
    if (deleteIndices.length > 0) {
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
        const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
        const sheetId = sheet.properties.sheetId;

        const sorted = [...deleteIndices].sort((a, b) => b - a);
        await sheets.spreadsheets.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: {
                requests: sorted.map(idx => ({
                    deleteDimension: {
                        range: { sheetId, dimension: 'ROWS', startIndex: idx + 1, endIndex: idx + 2 }
                    }
                })),
            },
        });
        console.log(`  ${deleteIndices.length}行を削除完了`);
    }

    // 最終件数
    const final = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!B:C`,
    });
    const finalRows = (final.data.values || []).filter(r => r[0] && r[0] !== 'エリア');
    const areas = {};
    finalRows.forEach(r => { areas[r[0]] = (areas[r[0]] || 0) + 1; });
    console.log(`\n=== 最終件数 ===`);
    console.log(`合計: ${finalRows.length}件`);
    Object.entries(areas).forEach(([a, c]) => console.log(`  ${a}: ${c}社`));
}

main().catch(err => { console.error(err.message); process.exit(1); });
