/**
 * cleanup_medical_operations.js
 * 医療・介護系の「本業支援（臨床検査、電子カルテ、介護施設など）」を
 * 検索レベルおよび抽出レベルで一括ブロックし、既存シートから削除する
 */
const fs = require('fs');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'クリニック専門支援';
const EXCLUDE_SHEET = '除外リスト';

function stopWhackAMole() {
    // 1. crawler.js のパッチ（医療・介護の実務系を弾く）
    let crawlerContent = fs.readFileSync('crawler.js', 'utf8');

    const NG_OLD = `    // ★ v2.6.0 追加: クリニック物理支援（開業時の不動産・建築・医療機器）`;
    const NG_NEW = `    // ★ v2.7.0 追加: いたちごっこ根本対応（医療・介護の「実務・システム・検査」系）
    '臨床検査', '血液検査', '電子カルテ', 'レセコン', 'PHC', 'ウィーメックス', 'エスアールエル', 'SRL', '介護', '福祉', '訪問看護', 'デイサービス', '老人ホーム', '医療事業開発', 'ケアマックス', 'ドクターソリューション', '医療サポート', 'メディカルフロント', 'メディカルガレージ', 'オクスアイ',
    // ★ v2.6.0 追加: クリニック物理支援（開業時の不動産・建築・医療機器）`;

    if (crawlerContent.includes(NG_OLD) && !crawlerContent.includes('臨床検査')) {
        crawlerContent = crawlerContent.replace(NG_OLD, NG_NEW);
        console.log('Fix1: crawler.js に医療・介護の実務支援系（電子カルテ・検査・介護等）を追加');
        fs.writeFileSync('crawler.js', crawlerContent, 'utf8');
    }

    // 2. searcher.js のパッチ（検索エンジンレベルでの「医療/介護の実務」排除）
    let searcherContent = fs.readFileSync('searcher.js', 'utf8');

    // 置換対象のクエリ文字列
    const QUERY_OLD = `-不動産 -建築 -設計 -医療機器 -機器 -プロパティ -建設 -工事 -貿易 -製造`;
    const QUERY_NEW = `-不動産 -建築 -設計 -医療機器 -機器 -プロパティ -建設 -工事 -貿易 -製造 -臨床検査 -電子カルテ -レセコン -介護 -福祉 -医薬品`;

    if (searcherContent.includes(QUERY_OLD) && !searcherContent.includes('-臨床検査')) {
        // searcher.js 内の2箇所（CSEとDDG）を一括置換
        searcherContent = searcherContent.split(QUERY_OLD).join(QUERY_NEW);
        console.log('Fix2: searcher.js の検索クエリに「-臨床検査 -電子カルテ -介護」等を追加');
        fs.writeFileSync('searcher.js', searcherContent, 'utf8');
    }
}

async function scanAndDeleteMedical() {
    const { isNGIndustry, isValidCompanyName, isListedCorporation } = require('./crawler');
    const sheets = await getGoogleSheetsClient();

    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET,
    });
    const allRows = res.data.values || [];
    if (allRows.length <= 1) return;
    
    const header  = allRows[0];
    const nameCol = header.indexOf('企業名');
    const urlCol  = header.indexOf('ホームページURL');

    const toDelete = [];
    const explicitMatches = [
        'ドクターソリューション', '東京医療サポート', 'メディカルフロント',
        'エスアールエル', 'ウィーメックス', 'メディカルガレージ',
        'オクスアイ', 'ケアマックス', '医療総研'
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

        if (reason) {
            toDelete.push({ rowNum, name, url, reason });
        }
    }

    console.log(`\n削除対象: ${toDelete.length}件`);
    if (toDelete.length === 0) return;

    toDelete.forEach(r => console.log(`  行${r.rowNum}: 「${r.name}」→ ${r.reason}`));

    // 除外リストに追記
    const exRes = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: EXCLUDE_SHEET,
    });
    const existingNames = new Set(
        (exRes.data.values || []).slice(1).map(r => (r[0] || '').trim())
    );
    
    const today = new Date().toLocaleDateString('ja-JP');
    const toAdd = toDelete
        .filter(r => r.name && !existingNames.has(r.name))
        .map(r => [r.name, '', r.url, r.reason, today]);

    if (toAdd.length > 0) {
        await sheets.spreadsheets.values.append({
            spreadsheetId: SPREADSHEET_ID,
            range: `${EXCLUDE_SHEET}!A:E`,
            valueInputOption: 'RAW',
            requestBody: { values: toAdd },
        });
        console.log(`\n除外リストに${toAdd.length}件追記`);
    }

    // シートから削除（降順）
    const meta = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    const sheetId = meta.data.sheets.find(s => s.properties.title === TARGET_SHEET).properties.sheetId;
    
    const requests = [...toDelete].sort((a, b) => b.rowNum - a.rowNum).map(r => ({
        deleteDimension: {
            range: { sheetId, dimension: 'ROWS', startIndex: r.rowNum - 1, endIndex: r.rowNum },
        },
    }));
    
    await sheets.spreadsheets.batchUpdate({ spreadsheetId: SPREADSHEET_ID, requestBody: { requests } });
    console.log(`シートから${toDelete.length}行を削除完了`);
}

async function main() {
    stopWhackAMole();
    await scanAndDeleteMedical();
}

main().catch(e => { console.error(e.message); process.exit(1); });
