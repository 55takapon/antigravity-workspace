/**
 * search_companies.js - メインオーケストレーター
 *
 * Web検索から企業情報を収集し、Google Sheetsに書き込む。
 * ※10社ごとに逐次自動保存を行う安全仕様
 *
 * 使い方:
 *   node search_companies.js                        # config.yamlで通常実行
 *   node search_companies.js --config custom.yaml   # カスタム設定
 *   node search_companies.js --dry-run              # Sheets書き込みなしでテスト
 *   node search_companies.js --dry-run --max 5      # テスト（最大5件）
 *   node search_companies.js --skip-crawl           # クロールなしで検索のみ
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const { searchGoogleCSE, searchDuckDuckGo, searchGoogleDirect, normalizeDomain, randomDelay } = require('./searcher');
const { crawlCompanyWebsite, extractCompanyLinksFromArticle, isArticlePage, isValidCompanyName, isNGIndustry, employeeFilter } = require('./crawler');
const { getGoogleSheetsClient, loadExcludeList, loadExistingUrls, writeCompaniesToSheet } = require('./sheets_writer');
const { initDB, checkDuplicate, persistNewCompanies } = require('./local_db');

// コマンドライン引数
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const skipCrawl = args.includes('--skip-crawl');
let configFile = 'config.yaml';
let maxOverride = null;

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--config' && args[i + 1]) configFile = args[i + 1];
    if (args[i] === '--max' && args[i + 1]) maxOverride = parseInt(args[i + 1], 10);
}

// 正規化・重複検知関数
function normalizeCoreName(name) {
    if (!name) return '';
    return name
        .replace(/株式会社|合同会社|有限会社/g, '')
        .replace(/[Ａ-Ｚａ-ｚ０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
        .replace(/　/g, ' ')
        .replace(/＆/g, '&')
        .toLowerCase()
        .replace(/[\s・\-_.&]/g, '')
        .trim();
}

function normalizeDeepDomain(url) {
    try {
        const u = new URL(url);
        let host = u.hostname.toLowerCase();
        return host.replace(/^(www|corp|en|ja|jp|info)\./i, '');
    } catch { return url; }
}

async function main() {
    console.log('========================================');
    console.log('  企業情報収集ツール (10社逐次保存版)');
    console.log(`  モード: ${isDryRun ? 'ドライラン（テスト）' : '本番'}`);
    console.log('========================================\n');

    // 1. 設定ファイル読み込み
    const configPath = path.join(__dirname, configFile);
    if (!fs.existsSync(configPath)) {
        console.error(`設定ファイルが見つかりません: ${configPath}`);
        process.exit(1);
    }
    const config = yaml.load(fs.readFileSync(configPath, 'utf-8'));
    if (maxOverride) config.search.max_results = maxOverride;

    console.log(`[設定] キーワード: ${config.search.keywords.join(', ')}`);
    console.log(`[設定] 地域: ${config.search.region}`);
    console.log(`[設定] 最大取得件数: ${config.search.max_results}`);
    console.log('');

    // 2. Google Sheets接続
    let sheetsClient = null;
    let excludeList = { names: new Set(), domains: new Set() };
    let existingUrls = new Set();

    try {
        sheetsClient = await getGoogleSheetsClient();
        excludeList = await loadExcludeList(sheetsClient, config);
        if (config.output?.spreadsheet_id) {
            existingUrls = await loadExistingUrls(sheetsClient, config.output.spreadsheet_id, config.output.sheet_name);
            console.log(`[重複チェック] 既存${existingUrls.size}件のURLを読み込み\n`);
        }
    } catch (err) {
        console.error(`[Sheets] 接続エラー: ${err.message}`);
        if (!isDryRun) process.exit(1);
        console.log('[Sheets] ドライランモードのため続行します\n');
    }

    // 2.5. ローカルDBの初期化（高速重複チェック用）
    let localDBContext = null;
    try {
        localDBContext = initDB();
    } catch (e) {
        console.warn(`[LocalDB] 初期化に失敗しました（無視して続行）: ${e.message}`);
    }

    // 3. Web検索
    console.log('--- STEP 1: Web検索 ---');
    let searchResults = [];
    const seenSearchDomains = new Set();
    let browser = null;

    if (config.google_cse?.enabled && config.google_cse?.api_key && config.google_cse?.cx) {
        console.log('[検索] Google Custom Search API を試行...');
        const cseResults = await searchGoogleCSE(config);
        if (cseResults) {
            for (const r of cseResults) {
                const d = normalizeDomain(r.url);
                if (!seenSearchDomains.has(d)) { seenSearchDomains.add(d); searchResults.push(r); }
            }
        }
    }

    if (searchResults.length < (config.search.max_results || 50)) {
        console.log(`[検索] DuckDuckGo — ${config.search.keywords.length}キーワードを個別検索...`);
        browser = await chromium.launch({ headless: true });

        for (let ki = 0; ki < config.search.keywords.length; ki++) {
            const keyword = config.search.keywords[ki];
            console.log(`\n[DDG ${ki+1}/${config.search.keywords.length}] "${keyword}"`);
            const tmpConfig = JSON.parse(JSON.stringify(config));
            tmpConfig.search.keywords = [keyword];

            const ddgResults = await searchDuckDuckGo(tmpConfig, browser);
            if (ddgResults) {
                let added = 0;
                for (const r of ddgResults) {
                    const d = normalizeDomain(r.url);
                    if (!seenSearchDomains.has(d)) {
                        seenSearchDomains.add(d); searchResults.push(r); added++;
                    }
                }
                console.log(`  → 新規${added}件追加 (累計${searchResults.length}件)`);
            }
            if (ki < config.search.keywords.length - 1) await randomDelay(3000, 6000);
        }
    }

    if (!searchResults || searchResults.length === 0) {
        console.error('\n[検索] 結果が取得できませんでした。');
        if (browser) await browser.close();
        process.exit(1);
    }
    console.log(`\n[検索結果] 合計 ${searchResults.length} 件のURLを取得\n`);

    // 4. フィルタリング
    console.log('--- STEP 2: フィルタリング ---');
    const filtered = searchResults.filter(item => {
        const domain = normalizeDomain(item.url);
        if (excludeList.domains.has(domain)) return false;
        if (excludeList.names.has(item.title)) return false;
        if (existingUrls.has(domain)) return false;
        return true;
    });
    console.log(`[フィルタ後] ${filtered.length} 件\n`);

    if (filtered.length === 0) {
        console.log('新規の企業が見つかりませんでした。');
        if (browser) await browser.close();
        return;
    }

    // --- バッチ処理用の状態管理 ---
    const seenFinalDomains = new Set();
    const seenFinalNames = new Set();
    const seenFinalNormNames = new Set();
    let totalWritten = 0;
    const finalQualityIssues = [];

    // バッチ書き込み関数
    async function processBatch(batchCompanies) {
        if (batchCompanies.length === 0) return;
        console.log(`\n=== 10社ごとの一括処理 & 書き込み (${batchCompanies.length}件クロール終了分) ===`);

        const deduplicated = [];
        for (const company of batchCompanies) {
            const d = normalizeDeepDomain(company.url);
            const coreName = (company.title || '').replace(/株式会社|合同会社|有限会社/g, '').trim();
            const normName = normalizeCoreName(company.title);

            if (seenFinalDomains.has(d)) continue;
            if (coreName && coreName.length >= 2 && seenFinalNames.has(coreName)) continue;
            if (normName && normName.length >= 2 && seenFinalNormNames.has(normName)) continue;
            
            let isDupByPartial = false;
            if (normName && normName.length >= 3) {
                for (const existing of seenFinalNormNames) {
                    if (existing.length >= 3 && (normName.includes(existing) || existing.includes(normName))) {
                        isDupByPartial = true;
                        break;
                    }
                }
            }
            if (isDupByPartial) continue;

            seenFinalDomains.add(d);
            if (coreName && coreName.length >= 2) seenFinalNames.add(coreName);
            if (normName && normName.length >= 2) seenFinalNormNames.add(normName);
            deduplicated.push(company);
        }

        const qualityChecked = deduplicated.filter(company => {
            const name = company.title || '';
            const rep = company.crawlData?.representative || '';
            
            if (!name || !isValidCompanyName(name)) {
                finalQualityIssues.push(`  [企業名無効] "${name}" → 除外`);
                return false;
            }
            if (rep && rep !== 'ご担当者') {
                if (/[はがをでにの].{3,}|しました|します|について|https?:|www\.|\.com|\.jp/.test(rep)) {
                    company.crawlData.representative = 'ご担当者';
                    finalQualityIssues.push(`  [代表者名修正] ${name}: "${rep}" → "ご担当者"`);
                }
            }
            
            // ★ v2.9.2: 問い合わせフォームURLがない場合はリスト化しない
            const formUrl = company.crawlData?.contactFormUrl || '';
            if (!formUrl || !formUrl.startsWith('http') || formUrl.match(/\.(pdf|doc|docx|zip)$/i)) {
                finalQualityIssues.push(`  [フォーム無効] "${name}" (URL: ${formUrl || 'なし'}) → 除外`);
                return false;
            }

            return true;
        });

        if (qualityChecked.length > 0) {
            if (!isDryRun && sheetsClient && config.output?.spreadsheet_id) {
                await writeCompaniesToSheet(
                    sheetsClient, config.output.spreadsheet_id, config.output.sheet_name,
                    qualityChecked, config
                );
                totalWritten += qualityChecked.length;
                console.log(`✅ ${qualityChecked.length}件書き込み完了 (累計: ${totalWritten}件)`);

                // ★ローカルDBに自動追記（書き込み成功後のみ）
                if (localDBContext) {
                    persistNewCompanies(
                        localDBContext.db, localDBContext.index,
                        qualityChecked, config.output.sheet_name
                    );
                }
                console.log('');
            } else if (isDryRun) {
                totalWritten += qualityChecked.length;
                console.log(`[ドライラン] ${qualityChecked.length}件シミュレーション (累計: ${totalWritten}件)\n`);
            }
        } else {
            console.log(`  → 内容がすべて無効・既存・重複のため書き込みなし\n`);
        }
    }

    let companies = [];

    if (!skipCrawl) {
        console.log('--- STEP 3: まとめ記事展開 & 企業HPクロール ---');
        if (!browser) browser = await chromium.launch({ headless: true });
        const context = await browser.newContext({
            locale: 'ja-JP',
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        });

        const expandedItems = [];
        const seenCrawlDomains = new Set();

        // ★★★ v2.2.0: 記事展開（article expansion）を完全廃止 ★★★
        // 
        // 「根本原因」の山移し
        //   従来: まとめ記事がヒット → 記事内のリンク20件を無差別取得
        //           → 博報堂・NTT・野球団がリストに混入
        //
        //   正しい設計: 検索クエリで最初から正しいURLのみ取得する。
        //              記事ページは展開せずスキップする。
        for (const item of filtered) {
            if (isArticlePage(item.url, item.title)) {
                console.log(`[記事スキップ] ${item.title || item.url}`);
                continue;  // 記事は展開せずスキップ
            }
            const d = normalizeDomain(item.url);
            if (!seenCrawlDomains.has(d)) {
                seenCrawlDomains.add(d);
                expandedItems.push(item);
            }
        }

        console.log(`\n[クロール対象] ${expandedItems.length}件の会社URL（10社ごとに逝次書き込み）\n`);


        for (let i = 0; i < expandedItems.length; i++) {
            const item = expandedItems[i];
            console.log(`\n[${i + 1}/${expandedItems.length}] ${item.url}`);

            // ★ クロール前にローカルDBで高速重複チェック（クロールコストをゼロに）
            if (localDBContext) {
                const dupCheck = checkDuplicate(localDBContext.index, { url: item.url, name: item.title });
                if (dupCheck.isDuplicate) {
                    console.log(`  [LocalDB スキップ] ${dupCheck.reason} (出典: ${dupCheck.matchedSource})`);
                    continue;
                }
            }

            const page = await context.newPage();
            try {
                let crawlData = await crawlCompanyWebsite(page, item.url, config);
                // ★ item.titleはDDG検索タイトルであり企業名ではない。クロール結果のみ使用。
                let companyName = crawlData.companyName || '';

                const portalDomains = ['mynavi.jp', 'doda.jp', 'en-japan.com', 'rikunabi.com', 'green-japan.com', 'wantedly.com', 'prtimes.jp', 'type.jp', 'hatena.ne.jp', 'bizreach.jp', 'tenshoku.mynavi.jp'];
                if (companyName && portalDomains.some(d => item.url.includes(d))) {
                    console.log(`  [公式HP再検索] ポータルサイト検出。企業名「${companyName}」で公式HPを検索します...`);
                    try {
                         const tmpBrowser = page.context().browser();
                         const portalSearchResults = await searchDuckDuckGo(config, tmpBrowser, `"${companyName}" 会社概要 -site:mynavi.jp -site:doda.jp -site:en-japan.com -site:prtimes.jp`);
                         let officialUrl = '';
                         if (portalSearchResults) {
                             for (const r of portalSearchResults) {
                                 if (!portalDomains.some(d => r.url.includes(d))) {
                                     officialUrl = r.url; break;
                                 }
                             }
                         }
                         if (officialUrl) {
                             console.log(`  [公式HP再クロール] ${officialUrl}`);
                             const officialData = await crawlCompanyWebsite(page, officialUrl, config);
                             crawlData = officialData;
                             companyName = officialData.companyName || companyName;
                             item.url = officialUrl;
                         }
                    } catch (e) { console.log(`  [公式HP再検索エラー] ${e.message.substring(0, 80)}`); }
                }

                // v2.0.0: 従業員数は参考情報として記録のみ（フィルタリング対象外）
                if (crawlData.employeeCount !== null) {
                    console.log(`  [従業員数] ${crawlData.employeeCount}名（参考情報）`);
                }

                companyName = crawlData.companyName || '';

                if (!companyName || !isValidCompanyName(companyName)) {
                    console.log(`  [スキップ] 企業名無効: "${companyName || '(空)'}"`);
                    await page.close(); continue;
                }

                // v2.0.0: NG業種除外ゲート
                const ngCheck = isNGIndustry(companyName);
                if (ngCheck.blocked) {
                    console.log(`  [NG業種] "${companyName}" → 理由: ${ngCheck.reason}`);
                    await page.close(); continue;
                }

                // v2.0.0: 上場企業チェック
                if (crawlData.isListed) {
                    console.log(`  [上場企業除外] ${companyName}`);
                    await page.close(); continue;
                }

                if (excludeList.names.has(companyName)) {
                    console.log(`  [除外] ${companyName} (除外リスト: 企業名)`);
                    await page.close(); continue;
                }

                const nameNormalized = companyName.replace(/株式会社|合同会社|有限会社/g, '').trim();
                let isExcludedByName = false;
                for (const excludeName of excludeList.names) {
                    const exNormalized = excludeName.replace(/株式会社|合同会社|有限会社/g, '').trim();
                    if (nameNormalized && exNormalized && nameNormalized.length >= 2 && exNormalized.length >= 2 &&
                        (nameNormalized.includes(exNormalized) || exNormalized.includes(nameNormalized))) {
                        isExcludedByName = true;
                        console.log(`  [除外] ${companyName} (部分一致 "${excludeName}")`);
                        break;
                    }
                }
                if (isExcludedByName) { await page.close(); continue; }

                companies.push({ ...item, title: companyName, crawlData });
            } catch (err) {
                console.error(`  [エラー] ${err.message.substring(0, 80)}`);
                companies.push({
                    ...item,
                    crawlData: {
                        companyName: '', employeeCount: null, representative: 'ご担当者', contactFormUrl: '',
                        keywordHits: [], keywordHitFlag: false, error: err.message.substring(0, 100),
                    },
                });
            }
            await page.close();

            // === 10件ごとの一括書き込み処理 ===
            if (companies.length >= 10 || i === expandedItems.length - 1) {
                await processBatch(companies);
                companies = [];
            }

            if (i < expandedItems.length - 1) {
                const speed = config.speed || {};
                await randomDelay(speed.crawl_interval_min || 3000, speed.crawl_interval_max || 8000);
            }
        }
        await context.close();
    } else {
        companies = filtered.map(item => ({
            ...item,
            crawlData: { companyName: '', employeeCount: null, representative: '', contactFormUrl: '', keywordHits: [], keywordHitFlag: false },
        }));
        await processBatch(companies);
        companies = [];
    }

    if (finalQualityIssues.length > 0) {
        console.log('\n  [品質問題の詳細]');
        for (const issue of finalQualityIssues) { console.log(issue); }
    }

    console.log('\n========================================');
    console.log('  完了');
    console.log('========================================');
    console.log(`  検索結果: ${searchResults.length}件`);
    console.log(`  フィルタ後: ${filtered.length}件`);
    console.log(`  スプレッドシート書き込み完了: ${totalWritten}件`);
    if (!isDryRun && config.output?.spreadsheet_id) {
        console.log(`   https://docs.google.com/spreadsheets/d/${config.output.spreadsheet_id}/edit`);
    }
    
    if (browser) await browser.close();
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
