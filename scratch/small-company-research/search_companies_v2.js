/**
 * search_companies_v2.js
 * ポータルから収集したシードURLをクロールし、品質ゲートを通過したものだけをシートに書き込む。
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);
const { google } = require('googleapis');

const { crawlOfficialSite } = require('./official_crawler');
const { runQualityGate } = require('./quality_gate');
const { SPREADSHEET_ID, normalizeDomain, appendExcludeDomains } = require('./schema');

// 設定
const TARGET_SHEET = 'Web奉行';

// キーワード（references/vertical-profiles.mdからWeb Production用を抜粋）
const KEYWORDS = [
    'ホームページ制作', 'Webサイト制作', 'サイト制作', 'コーポレートサイト',
    'LP制作', 'ランディングページ', 'WordPress', 'CMS', 'ECサイト', 'Shopify',
    'Webデザイン', 'UIデザイン', '保守運用'
];

const args = process.argv.slice(2);
const seedsFileIdx = args.indexOf('--seeds');
const SEEDS_FILE = seedsFileIdx !== -1 ? args[seedsFileIdx + 1] : '';
const DRY_RUN = args.includes('--dry-run');
const maxIdx = args.indexOf('--max');
const MAX_LIMIT = maxIdx !== -1 ? parseInt(args[maxIdx + 1], 10) : 0;

if (!SEEDS_FILE || !fs.existsSync(SEEDS_FILE)) {
    console.error(`エラー: シードファイルが指定されていないか、存在しません。`);
    console.log(`Usage: node search_companies_v2.js --seeds seeds_osaka.jsonl`);
    process.exit(1);
}

// Sheets書き込み用関数
async function appendToSheet(results) {
    let credPath = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
    if (!fs.existsSync(credPath)) credPath = path.join(__dirname, 'google_credentials.json');
    if (!fs.existsSync(credPath)) {
        console.warn('google_credentials.json がないため Sheetsへの書き込みをスキップします。');
        return;
    }

    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({ credentials, scopes: ['https://www.googleapis.com/auth/spreadsheets'] });
    const sheets = google.sheets({ version: 'v4', auth });

    // C列(企業名)の最終行を取得して、空行を詰めずに追記するためのロジック
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${TARGET_SHEET}!C:C`,
    });
    const lastRowIndex = (res.data.values || []).length + 1;
    const range = `${TARGET_SHEET}!A${lastRowIndex}`;

    const values = results.map(r => {
        // A: № (空白)
        // B: エリア
        // C: 企業名
        // D: 代表者名
        // E: URL
        // F: 問い合わせフォームURL
        // G: 送信日
        // H: 送信○×
        // I: 送信不可理由 (✕なら理由)
        // J: 従業員数 (空欄)
        // K: 資本金
        // L: キーワードHIT (カンマ区切り)
        // M: HIT詳細
        // N: 取得日時
        // O: 種類 (Web制作)
        // P: シード元 (Web奉行など)
        
        return [
            '', // A
            r.region, // B
            r.companyName, // C
            r.representative, // D
            r.url, // E
            r.contactUrl, // F
            '', // G
            r.status === '✕' ? '✕' : '', // H
            r.rejectReason, // I
            '', // J
            r.capitalText, // K
            r.hits ? r.hits.join(', ') : '', // L
            '', // M: 空白（古い仕様との互換）
            new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }), // N
            r.portal_category, // O
            r.portal_source === 'web-bugyo' ? 'Web奉行' : (r.portal_source === 'imitsu' ? 'PRONIアイミツ' : r.portal_source) // P
        ];
    });

    await sheets.spreadsheets.values.update({
        spreadsheetId: SPREADSHEET_ID,
        range: range,
        valueInputOption: 'USER_ENTERED',
        requestBody: { values },
    });

    console.log(`\n✅ Google Sheets に ${values.length} 件を書き込みました。`);

    // ★ exclude_domains.txt を即座に更新（連続バッチ時の重複防止）
    const newDomains = results.map(r => normalizeDomain(r.url)).filter(d => d);
    appendExcludeDomains(newDomains);
}

async function main() {
    console.log(`========================================`);
    console.log(`  小規模企業リサーチエンジン v2`);
    console.log(`  シードファイル: ${SEEDS_FILE}`);
    console.log(`========================================\n`);

    // シード読み込み
    const seeds = [];
    const lines = fs.readFileSync(SEEDS_FILE, 'utf-8').split('\n');
    for (const line of lines) {
        if (!line.trim()) continue;
        try { seeds.push(JSON.parse(line)); } catch { }
    }

    console.log(`✅ ${seeds.length}件のシードを読み込みました。クロール開始...\n`);

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        locale: 'ja-JP',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    });

    const results = [];

    const loopMax = MAX_LIMIT > 0 ? Math.min(MAX_LIMIT, seeds.length) : seeds.length;

    for (let i = 0; i < loopMax; i++) {
        const seed = seeds[i];
        console.log(`[${i + 1}/${loopMax}] クロール中: ${seed.company_name} (${seed.candidate_url})`);

        const page = await context.newPage();
        const crawlData = await crawlOfficialSite(page, seed.candidate_url);
        await page.close();
        
        // シードの情報をマージ
        crawlData.companyName = crawlData.companyName || seed.company_name;
        crawlData.representative = crawlData.representative || seed.representative_hint;
        crawlData.url = seed.candidate_url; // 正規URL

        // 品質ゲート判定
        const gateResult = runQualityGate(crawlData, KEYWORDS);

        if (gateResult.shouldWrite) {
            console.log(`  → 通過: ${gateResult.status === '✕' ? 'NGフラグあり (' + gateResult.rejectReason + ')' : 'OK'}`);
            results.push({
                region: seed.region,
                companyName: crawlData.companyName,
                representative: crawlData.representative,
                url: crawlData.url,
                contactUrl: crawlData.contactUrl,
                status: gateResult.status,
                rejectReason: gateResult.rejectReason,
                capitalText: crawlData.capitalText,
                hits: gateResult.hits,
                portal_source: seed.portal_source,
                portal_category: seed.portal_category
            });
        } else {
            console.log(`  → 破棄: ${gateResult.rejectReason}`);
        }
    }

    await context.close();
    await browser.close();

    console.log(`\nクロール完了。${seeds.length}件中 ${results.length}件をシート書き込み対象として保持。`);

    if (!DRY_RUN && results.length > 0) {
        await appendToSheet(results);
    } else if (DRY_RUN) {
        console.log(`[ドライラン] 以下のデータを書き込みます:`);
        results.slice(0, 3).forEach(r => console.log(' ', r));
    }

    console.log('完了！');
}

main().catch(console.error);
