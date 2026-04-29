/**
 * patch_and_delete_v23.js
 * 1. crawler.js に NG パターン追加
 * 2. 指定会社をシートから削除 + 除外リスト追記
 */
const fs = require('fs');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET   = 'Webマーケティング';
const EXCLUDE_SHEET  = '除外リスト';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// STEP1: crawler.js パッチ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function patchCrawler() {
    let content = fs.readFileSync('crawler.js', 'utf8');

    // ① NG_INDUSTRY_KEYWORDS 末尾に追加
    const NG_OLD = `    // ★ v2.2.0 追加: 絶対再発防止`;
    const NG_NEW = `    // ★ v2.3.0 追加: 今回発見された漏れ業種
    // インフラ・電気工事
    '電設', 'タワーライン', 'データセンター',
    // 交通・輸送
    'バス株式会社', '運輸株式会社', '交通株式会社',
    // 食品・農業
    '青果', 'バイオパートナー', '農業',
    // 住宅・不動産系
    '住宅保証', '建築検査', 'レコードマネジメント',
    // 金融・リース・商社
    'センチュリー株式会社', '双日', '伊藤忠', '丸紅', '住友商事',
    // 保険（東京海上等）
    '損保', '損害保険', '生命保険', '火災保険', 'あんしんコンサルティング',
    // 医療・ヘルスケア
    '総合メディカル', 'メディカル株式会社', '病院', '医療法人',
    // 調査・リサーチ
    '商工リサーチ', '日経リサーチ', 'リサーチ株式会社', '信用調査',
    // 書店・出版物販
    'ブックセンター', '書店', '本店',
    // エンタメ・施設
    'ドーム株式会社', 'スタジアム', '展示会',
    // 自動車・部品大手
    'デンソー', '自動車株式会社',
    // ガス・エネルギー大手
    '岩谷', 'ガス株式会社',
    // 工学・CAE・専門ソフト
    'CAEソリューション', 'MBD', '構造計算',
    // 投資育成・VC
    '投資育成', '中小企業投資',
    // 環境系（規模次第だが大手系）
    'エコ・プラン', '環境コンサル',
    // ★ v2.2.0 追加: 絶対再発防止`;

    if (content.includes(NG_OLD)) {
        content = content.replace(NG_OLD, NG_NEW);
        console.log('Fix1 OK: NG_INDUSTRY_KEYWORDS v2.3.0追加');
    } else {
        console.log('WARN: Fix1 target not found - skip');
    }

    // ② isValidCompanyName INVALID_PATTERNS に追加
    // 「法人格の直後に助詞が来る場合」の直前に挿入
    const VALID_OLD = `    // 法人格の直後に助詞が来る場合は文章片（例: 「株式会社との」「株式会社様を」）
    if (/(?:株式会社|合同会社|有限会社)[様さん]?[はがをでにともの]/.test(name)) return false;`;
    const VALID_NEW = `    // ★ v2.3.0: ページタイトル混入パターン追加
    // 「トップ |」「アクセス |」「会社概要」で始まるものはページタイトル
    if (/^(?:トップ|アクセス|会社概要|ホーム|HOME|Top)\s*[|｜]/.test(name)) return false;
    // 「〇〇ソリューションカンパニー|株式会社」のような社内部署名パターン
    if (/カンパニー\s*[|｜]/.test(name)) return false;
    // URLショートナー・Webサービス名
    if (/^URL\s/i.test(name) || /Shortener/i.test(name)) return false;
    // クラウドファンディング・プラットフォーム系
    if (/^クラウドファンディング/.test(name) || /^Readyfor/i.test(name)) return false;
    // 「コーポレートサイト」そのものが企業名
    if (/コーポレートサイト/.test(name)) return false;
    // 「建築構造計算ソフトウェアの〇〇株式会社」のような冗長なページタイトル
    if (/ソフトウェアの[^\s]/.test(name)) return false;
    // 「〇〇 - 〇〇本店」のような書店・施設名
    if (/ブックセンター/.test(name)) return false;

    // 法人格の直後に助詞が来る場合は文章片（例: 「株式会社との」「株式会社様を」）
    if (/(?:株式会社|合同会社|有限会社)[様さん]?[はがをでにともの]/.test(name)) return false;`;

    if (content.includes(VALID_OLD)) {
        content = content.replace(VALID_OLD, VALID_NEW);
        console.log('Fix2 OK: isValidCompanyName v2.3.0追加');
    } else {
        console.log('WARN: Fix2 target not found - skip');
    }

    fs.writeFileSync('crawler.js', content, 'utf8');
    console.log('crawler.js 保存完了\n');
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// STEP2: 今回のNG会社 + 前回の漏れ会社を合わせて削除
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const ALL_NG_TARGETS = [
    // ★ 今回追加分
    { match: '東京海上日動あんしんコンサルティング', reason: 'NG業種:保険系コンサル' },
    { match: 'CAEソリューションカンパニー',          reason: 'NG業種:工学CAEソフト' },
    { match: 'Idaj',                                reason: 'NG業種:工学CAEソフト' },
    { match: '総合メディカル',                        reason: 'NG業種:医療' },
    { match: '東京商工リサーチ',                      reason: 'NG業種:信用調査' },
    { match: 'コンサルティンググループ株式会社',        reason: 'NG:企業名無効(グループ名)' },
    { match: 'GENOVA',                               reason: 'NG業種:医療IT' },
    { match: '東京中小企業投資育成',                   reason: 'NG業種:投資育成機関' },
    { match: 'エコ・プラン',                          reason: 'NG業種:環境系' },
    { match: 'シーシーエス',                          reason: 'NG業種:照明製造' },
    { match: '青山ブックセンター',                     reason: 'NG業種:書店' },
    { match: 'TSP太陽',                              reason: 'NG業種:展示会・イベント' },
    { match: '日経リサーチ',                          reason: 'NG業種:市場調査' },
    // ★ 前回の漏れ分（_patch_v23実行前）
    { match: '飯舘バイオパートナーズ',                 reason: 'NG業種:バイオ農業' },
    { match: '東京レコードマネジメント',                reason: 'NG業種:文書管理' },
    { match: '東京電設サービス',                       reason: 'NG業種:電設工事' },
    { match: 'コーポレートサイト',                     reason: '企業名無効:サイト用語' },
    { match: 'ＧＤＢＬ',                             reason: 'NG:業種不明対象外' },
    { match: 'アット東京',                            reason: 'NG業種:データセンター' },
    { match: 'タワーライン',                          reason: 'NG業種:通信インフラ' },
    { match: 'ファミリーネット・ジャパン',              reason: 'NG業種:ISP' },
    { match: 'ホームテック',                          reason: 'NG業種:住宅リフォーム' },
    { match: 'プライムソリューションズ',               reason: 'NG業種:対象外' },
    { match: 'ハウスプラス住宅保証',                   reason: 'NG業種:住宅保証' },
    { match: 'Readyfor',                             reason: '企業名無効:CF' },
    { match: 'クラウドファンディング',                  reason: '企業名無効:CF' },
    { match: '東京ドーム',                            reason: 'NG業種:施設' },
    { match: '京成バス',                              reason: 'NG業種:交通' },
    { match: '東京シティ青果',                         reason: 'NG業種:青果卸' },
    { match: 'URL Shortener',                        reason: '企業名無効:ツール' },
    { match: '会社概要・アクセス',                     reason: '企業名無効:ページタイトル' },
    { match: 'デンソー',                             reason: 'NG業種:自動車部品大手' },
    { match: '日本建築検査協会',                       reason: 'NG業種:検査協会' },
    { match: '岩谷産業',                              reason: 'NG業種:ガス大手' },
    { match: 'プレサンスコーポレーション',              reason: 'NG業種:不動産デベロッパー' },
    { match: '東京センチュリー',                       reason: 'NG業種:リース金融' },
    { match: '双日',                                  reason: 'NG業種:総合商社' },
    { match: '建築構造計算ソフトウェア',                reason: '企業名無効:ページタイトル' },
    { match: 'ユニオンシステム',                       reason: 'NG業種:建築CADソフト' },
    { match: 'Kokusai',                              reason: 'NG業種:対象外' },
    { match: '株式会社日新',                           reason: 'NG:ページタイトル混入' },
];

async function deleteFromSheet() {
    const sheets = await getGoogleSheetsClient();

    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET,
    });
    const allRows = res.data.values || [];
    const header  = allRows[0];
    const nameCol = header.indexOf('企業名');
    const urlCol  = header.indexOf('ホームページURL');

    const toDelete = [];
    for (let i = 1; i < allRows.length; i++) {
        const name   = (allRows[i][nameCol] || '').trim();
        const url    = (allRows[i][urlCol]  || '').trim();
        const rowNum = i + 1;
        for (const t of ALL_NG_TARGETS) {
            if (name.includes(t.match) || url.includes(t.match)) {
                toDelete.push({ rowNum, name, url, reason: t.reason });
                break;
            }
        }
    }

    console.log(`削除対象: ${toDelete.length}件`);
    toDelete.forEach(r => console.log(`  行${r.rowNum}: 「${r.name}」→ ${r.reason}`));

    if (toDelete.length === 0) { console.log('削除対象なし'); return; }

    // 除外リスト追記
    const exRes = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID, range: EXCLUDE_SHEET,
    });
    const existingNames = new Set((exRes.data.values || []).slice(1).map(r => (r[0] || '').trim()));
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
    console.log('=== STEP1: crawler.js パッチ ===');
    patchCrawler();

    console.log('=== STEP2: シート削除 + 除外リスト追記 ===');
    await deleteFromSheet();

    console.log('\n=== 完了 ===');
}

main().catch(e => { console.error(e.message); process.exit(1); });
