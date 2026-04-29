/**
 * horizontal_cleanup.js
 * 水平展開によるシート一斉クリーンアップと crawler.js の強化
 */
const fs = require('fs');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET   = 'Webマーケティング';
const EXCLUDE_SHEET  = '除外リスト';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// STEP1: crawler.js への水平展開パッチ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
function patchCrawlerHorizontal() {
    let content = fs.readFileSync('crawler.js', 'utf8');

    // NG_INDUSTRY_KEYWORDS への追加
    const NG_OLD = `    // ★ v2.3.0 追加: 今回漏れた業種カテゴリー`;
    const NG_NEW = `    // ★ v2.4.0 水平展開追加: 大手インフラ・グループ企業
    // 電力・エネルギーグループ
    '東電', 'TEPCO', '関電', '九電', '東北電力', '中部電力', '関西電力', '九州電力',
    // モビリティ・次世代インフラ
    'モビリティ', 'Mobility', 'e-Mobility',
    // 鉄道・交通大手グループ
    'JR', 'メトロ', '京王', '小田急', '東急', '阪急', '近鉄', '名鉄', '西鉄', '東京地下鉄',
    // 通信大手グループ
    'KDDI', 'SoftBank', 'ソフトバンク',
    // 金融メガグループ
    'MUFG', 'SMBC', 'みずほ', '三井住友', '三菱UFJ',
    // 自動車メーカーグループ
    'トヨタ', 'ホンダ', '日産', 'マツダ', 'スバル', 'ダイハツ', 'スズキ',
    // ★ v2.3.0 追加: 今回漏れた業種カテゴリー`;

    // 既に v2.3.0 のパッチが当たっているか確認。当たっていなければ、前回のコードも含めて適用する必要があるが、
    // 前回の実行が失敗したままになっていたため、念のためここで v2.3.0 と v2.4.0 を合わせた文字列で置換を試みる。
    
    // crawler.js の現在の状態を確認するために、一度汎用的な場所を狙う
    const FALLBACK_OLD = `    // 大学系VC・インキュベーター
    'プラットフォーム開発', '協創', 'ベンチャーキャピタル',
];`;

    const FALLBACK_NEW = `    // 大学系VC・インキュベーター
    'プラットフォーム開発', '協創', 'ベンチャーキャピタル',
    
    // ★ v2.3.0 & v2.4.0 水平展開追加: 大手インフラ・グループ企業・漏れ業種
    // 電力・エネルギーグループ
    '東電', 'TEPCO', '関電', '九電', '東北電力', '中部電力', '関西電力', '九州電力',
    // モビリティ・次世代インフラ
    'モビリティ', 'Mobility', 'e-Mobility',
    // 鉄道・交通大手グループ
    'JR', 'メトロ', '京王', '小田急', '東急', '阪急', '近鉄', '名鉄', '西鉄', '東京地下鉄',
    // 通信大手グループ
    'KDDI', 'SoftBank', 'ソフトバンク',
    // 金融メガグループ
    'MUFG', 'SMBC', 'みずほ', '三井住友', '三菱UFJ', 'センチュリー株式会社',
    // 自動車メーカーグループ
    'トヨタ', 'ホンダ', '日産', 'マツダ', 'スバル', 'ダイハツ', 'スズキ', 'デンソー', '自動車株式会社',
    // インフラ・電気工事
    '電設', 'タワーライン', 'データセンター',
    // 交通・輸送
    'バス株式会社', '運輸株式会社', '交通株式会社',
    // 食品・農業
    '青果', 'バイオパートナー', '農業',
    // 住宅・不動産系
    '住宅保証', '建築検査', 'レコードマネジメント', '文書管理',
    // 金融・リース・商社
    '双日', '伊藤忠', '丸紅', '住友商事',
    // 保険（東京海上等）
    '損保', '損害保険', '生命保険', '火災保険', 'あんしんコンサルティング',
    // 医療・ヘルスケア
    '総合メディカル', 'メディカル株式会社', '病院', '医療法人', 'GENOVA',
    // 調査・リサーチ
    '商工リサーチ', '日経リサーチ', 'リサーチ株式会社', '信用調査',
    // 書店・出版物販
    'ブックセンター', '書店', '本店',
    // エンタメ・施設
    'ドーム株式会社', 'スタジアム', '展示会', 'TSP太陽',
    // ガス・エネルギー大手
    '岩谷', 'ガス株式会社',
    // 工学・CAE・専門ソフト
    'CAEソリューション', 'MBD', '構造計算', 'Idaj',
    // 投資育成・VC
    '投資育成', '中小企業投資',
    // 環境系
    'エコ・プラン', '環境コンサル',
];`;

    if (content.includes(FALLBACK_OLD)) {
        content = content.replace(FALLBACK_OLD, FALLBACK_NEW);
        console.log('Fix1: NG_INDUSTRY_KEYWORDS 水平展開追加完了');
    }

    const VALID_OLD = `    // 法人格の直後に助詞が来る場合は文章片（例: 「株式会社との」「株式会社様を」）
    if (/(?:株式会社|合同会社|有限会社)[様さん]?[はがをでにともの]/.test(name)) return false;`;
    
    const VALID_NEW = `    // ★ v2.3.0 & v2.4.0: ページタイトル混入パターン追加
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

    if (content.includes(VALID_OLD) && !content.includes('トップ |')) {
        content = content.replace(VALID_OLD, VALID_NEW);
        console.log('Fix2: isValidCompanyName ページタイトル混入対策追加完了');
    }

    fs.writeFileSync('crawler.js', content, 'utf8');
    console.log('crawler.js パッチ完了\n');
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// STEP2: シートを最新ロジックで全スキャン＆削除
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async function scanAndDelete() {
    // パッチを当てた最新のcrawler.jsを読み込む
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
    
    // スプレッドシートから読み込んだデータに対してループ
    for (let i = 1; i < allRows.length; i++) {
        const row    = allRows[i];
        const name   = (row[nameCol] || '').trim();
        const url    = (row[urlCol]  || '').trim();
        const rowNum = i + 1; // 1-indexed (header is 1)

        let reason = null;
        if (!name) {
            reason = '企業名なし';
        } else if (!isValidCompanyName(name)) {
            reason = '企業名無効/ページタイトル等';
        } else if (isListedCorporation(name)) {
            reason = '上場企業キーワード検出';
        } else {
            const industryCheck = isNGIndustry(name);
            if (industryCheck.blocked) {
                reason = 'NG業種:' + industryCheck.reason;
            } else if (url.includes('tepco.co.jp')) {
                 reason = 'NGドメイン:tepco.co.jp';
            }
        }

        // さらに、前回指摘分などで漏れている可能性をカバー
        const explicitMatches = [
            '東京海上日動', 'Idaj', 'GENOVA', 'TSP太陽', '日経リサーチ'
        ];
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

    if (toDelete.length === 0) { console.log('削除対象なし'); return; }

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
    console.log('=== STEP1: crawler.js への水平展開パッチ ===');
    patchCrawlerHorizontal();

    console.log('=== STEP2: シートの最新ロジックスキャンとクリーンアップ ===');
    await scanAndDelete();

    console.log('\n=== 完了 ===');
}

main().catch(e => { console.error(e.message); process.exit(1); });
