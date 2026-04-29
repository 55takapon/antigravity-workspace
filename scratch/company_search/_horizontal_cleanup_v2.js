/**
 * horizontal_cleanup_v2.js
 * 新たな3つの構造（HD、ISP、研究所）の水平展開とシートクリーンアップ
 */
const fs = require('fs');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET   = 'Webマーケティング';
const EXCLUDE_SHEET  = '除外リスト';

function patchCrawlerHorizontalV2() {
    let content = fs.readFileSync('crawler.js', 'utf8');

    // NG_INDUSTRY_KEYWORDS への追加
    const NG_OLD = `    // ★ v2.3.0 追加: 今回漏れた業種カテゴリー`;
    const NG_NEW = `    // ★ v2.5.0 水平展開追加: ホールディングス・ISP・研究所
    // ホールディングス・持株会社
    'ホールディングス', 'HD', 'グループ本社',
    // ISP・プロバイダ大手
    'ビッグローブ', 'BIGLOBE', 'So-net', 'Nifty', 'OCN', 'ぷらら', 'インターネットイニシアティブ', 'IIJ',
    // シンクタンク・研究機関
    '研究所', '総研', 'シンクタンク',
    // ★ v2.3.0 追加: 今回漏れた業種カテゴリー`;

    if (content.includes(NG_OLD)) {
        content = content.replace(NG_OLD, NG_NEW);
        console.log('Fix1: NG_INDUSTRY_KEYWORDS v2.5.0 水平展開追加完了');
    }

    fs.writeFileSync('crawler.js', content, 'utf8');
}

async function scanAndDeleteV2() {
    const { isNGIndustry, isValidCompanyName, isListedCorporation } = require('./crawler');
    const sheets = await getGoogleSheetsClient();

    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET,
    });
    const allRows = res.data.values || [];
    if (allRows.length === 0) return;
    
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

        // 個別指定リカバリー
        const explicitMatches = ['セイワホールディングス', 'ビッグローブ', '東京コンサルティング研究所'];
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
    toDelete.forEach(r => console.log(`  行${r.rowNum}: 「${r.name}」→ ${r.reason}`));

    if (toDelete.length === 0) return;

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
    patchCrawlerHorizontalV2();
    await scanAndDeleteV2();
}

main().catch(e => { console.error(e.message); process.exit(1); });
