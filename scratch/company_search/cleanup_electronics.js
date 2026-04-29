/**
 * cleanup_electronics.js
 * 総合電機・ITゼネコン等の超大手グループを水平展開パッチ＆一斉削除
 */
const fs = require('fs');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEETS = ['Webマーケティング', 'Webマーケティング_名古屋', 'クリニック専門支援'];
const EXCLUDE_SHEET  = '除外リスト';

function patchCrawlerElectronics() {
    let content = fs.readFileSync('crawler.js', 'utf8');

    const NG_OLD = `    // 自動車メーカーグループ`;
    const NG_NEW = `    // 総合電機・ITゼネコン・精密機器グループ
    '東芝', '日立', 'パナソニック', 'Panasonic', 'ソニー', 'Sony', '三菱電機', '富士通', 'NEC', '日本電気', 'シャープ', 'キヤノン', 'Canon', 'リコー', 'RICOH', 'セイコー', 'エプソン', 'EPSON',
    // 自動車メーカーグループ`;

    if (content.includes(NG_OLD) && !content.includes('東芝')) {
        content = content.replace(NG_OLD, NG_NEW);
        console.log('Fix: NG_INDUSTRY_KEYWORDS に総合電機メガグループ（東芝等）を追加');
        fs.writeFileSync('crawler.js', content, 'utf8');
    }
}

async function scanAndDeleteElectronics(sheets, sheetName) {
    const { isNGIndustry, isValidCompanyName, isListedCorporation } = require('./crawler');
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
    const explicitMatches = [
        '東芝', '日立', 'パナソニック', 'ソニー', '三菱電機', '富士通', 'NEC', 'シャープ'
    ];
    
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

        if (!reason) {
            for (const m of explicitMatches) {
                if (name.includes(m)) {
                    reason = 'NG個別指定:' + m;
                    break;
                }
            }
        }

        if (reason && (reason.includes('東芝') || reason.includes('日立') || reason.includes('パナソニック') || reason.includes('ソニー') || reason.includes('三菱電機') || reason.includes('富士通') || reason.includes('NEC') || reason.includes('シャープ') || explicitMatches.some(m => name.includes(m)))) {
            toDelete.push({ rowNum, name, url, reason });
        }
    }

    if (toDelete.length > 0) {
        console.log(`\n[${sheetName}] 削除対象: ${toDelete.length}件`);
        toDelete.forEach(r => console.log(`  行${r.rowNum}: 「${r.name}」→ ${r.reason}`));
    }
    return toDelete;
}

async function main() {
    patchCrawlerElectronics();
    const sheets = await getGoogleSheetsClient();

    let allToDelete = [];
    for (const sheetName of TARGET_SHEETS) {
        const toDelete = await scanAndDeleteElectronics(sheets, sheetName);
        if (toDelete.length > 0) {
            allToDelete.push({ sheetName, rows: toDelete });
        }
    }

    if (allToDelete.length === 0) {
        console.log('削除対象は見つかりませんでした。');
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
