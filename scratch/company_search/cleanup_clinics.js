/**
 * cleanup_clinics.js
 * クリニック開業支援などのキーワードで混入した
 * 「物理的な支援会社（不動産、建築、医療機器）」や「ゴミテキスト」を一斉排除
 */
const fs = require('fs');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET   = 'クリニック専門支援';
const EXCLUDE_SHEET  = '除外リスト';

function patchCrawlerClinicPatterns() {
    let content = fs.readFileSync('crawler.js', 'utf8');

    // NG_INDUSTRY_KEYWORDS に追加
    const NG_OLD = `    // ★ v2.5.0 水平展開追加: ホールディングス・ISP・研究所`;
    const NG_NEW = `    // ★ v2.6.0 追加: クリニック物理支援（開業時の不動産・建築・医療機器）
    '貿易', '医療機器', '歯科産業', '産業株式会社', '地所', 'プロパティマネジメント', '建築', '日建', '設計', '調剤薬局',
    // ★ v2.5.0 水平展開追加: ホールディングス・ISP・研究所`;

    if (content.includes(NG_OLD)) {
        content = content.replace(NG_OLD, NG_NEW);
        console.log('Fix1: NG_INDUSTRY_KEYWORDS にクリニック物理支援系（不動産・機器・貿易）を追加');
    }

    // INVALID_PATTERNS に追加（ゴミテキスト対策）
    const VALID_OLD = `    // 「トップ |」「アクセス |」「会社概要」で始まるものはページタイトル`;
    const VALID_NEW = `    // ★ v2.6.0 ゴミテキスト対策追加
    if (/https/i.test(name)) return false;            // URLの混入
    if (/ニュー速/.test(name)) return false;           // まとめサイトの混入
    if (/様Webサイ/.test(name)) return false;          // 抽出失敗ゴミ
    if (/^株式会社.{1}$/.test(name)) return false;    // 「株式会社調」などの1文字ゴミ
    if (/医療法人社団/.test(name)) return false;       // クリニックそのもの

    // 「トップ |」「アクセス |」「会社概要」で始まるものはページタイトル`;

    if (content.includes(VALID_OLD)) {
        content = content.replace(VALID_OLD, VALID_NEW);
        console.log('Fix2: isValidCompanyName にゴミテキスト・医療法人そのものを追加');
    }

    fs.writeFileSync('crawler.js', content, 'utf8');
}

async function scanAndDeleteClinics() {
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
    const explicitMatches = [
        '株式会社https', '三菱地所プロパティマネジメント', '日本医療宣研',
        '医療経営研究所', '株式会社日建', '医療法人社団進興会',
        'シンプリック様', 'ニュー速:', '株式会社調', '医療DXコンサルティング',
        '白水貿易', '株式会社APPY', '東京歯科産業'
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
            reason = '企業名無効(ゴミテキスト/法人そのもの)';
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
    patchCrawlerClinicPatterns();
    await scanAndDeleteClinics();
}

main().catch(e => { console.error(e.message); process.exit(1); });
