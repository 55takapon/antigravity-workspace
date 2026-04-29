/**
 * searcher.js - Web検索モジュール
 *
 * 3段構成:
 *   1. Google Custom Search API（メイン）
 *   2. DuckDuckGo HTMLスクレイピング（サブ）
 *   3. Google検索 + 人間速度スクレイピング（最終手段）
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

// 求人サイト・SNS・ポータルの除外ドメイン
const EXCLUDED_DOMAINS = [
    // 求人サイト
    'indeed.com', 'indeed.co.jp',
    'recruit.co.jp', 'rikunabi.com',
    'mynavi.jp', 'mynavi.co.jp',
    'en-japan.com', 'en.co.jp',
    'doda.jp', 'type.jp',
    'wantedly.com', 'green-japan.com',
    'hellowork.go.jp', 'jsite.mhlw.go.jp',
    'stanby.co.jp', 'careerjet.jp',
    'baito.mynavi.jp', 'townwork.net',
    'baitoru.com',
    // SNS・メッセージ
    'facebook.com', 'twitter.com', 'x.com',
    'instagram.com', 'linkedin.com',
    'youtube.com', 'tiktok.com',
    'pinterest.com', 'pinterest.jp',
    'threads.net', 'tumblr.com',
    'line.me', 'note.com',
    // 大手ポータル・EC
    'wikipedia.org', 'amazon.co.jp', 'amazon.com',
    'rakuten.co.jp', 'yahoo.co.jp',
    // マップ・レビュー
    'google.com', 'google.co.jp',
    'tabelog.com', 'hotpepper.jp', 'ekiten.jp',
    // 比較・まとめ・メディア
    'matome.naver.jp', 'kakaku.com',
    'qiita.com', 'zenn.dev',
    'hubspot.com', 'hubspot.jp',
    'salesforce.com', 'marketo.com',
    // ツール・SaaS
    'getpocket.com', 'feedly.com',
    'slack.com', 'notion.so',
    'apps.apple.com', 'play.google.com',
    // 政府・自治体
    'go.jp', 'pref.osaka.jp',
    // ブログプラットフォーム
    'ameblo.jp', 'hatenablog.com', 'livedoor.jp',
    'medium.com', 'substack.com',
    // その他除外
    'baseconnect.in',
    // 求人（追加 v2.0.0）
    'job-gear.net', 'job-list.net', 'helloworkplus.com',
    'kyujinbu.com', 'career-on.jp',
    // 法人情報DB
    'houjin.jp', 'houjin-lookup.info',
    // ナビ・地図
    'navitime.co.jp',
    // クラウドファンディング
    'camp-fire.jp',
    // パチンコ
    'p-world.co.jp',
    // ニュース
    'mainichi.jp', 'nikkei.com', 'chunichi.co.jp',
    // 行政（追加）
    'mhlw.go.jp', 'soumu.go.jp',
    // 金融情報
    'smbcnikko.co.jp',
    // その他
    'bestcalendar.jp', 'dreamnews.jp',
];

/**
 * URLが除外ドメインに該当するかチェック
 */
function isExcludedUrl(url) {
    try {
        const hostname = new URL(url).hostname.toLowerCase();
        return EXCLUDED_DOMAINS.some(d => hostname.includes(d));
    } catch {
        return true;
    }
}

/**
 * ランダム待機
 */
function randomDelay(min, max) {
    return new Promise(resolve => setTimeout(resolve, min + Math.random() * (max - min)));
}

/**
 * URLから企業ドメインを正規化（重複チェック用）
 */
function normalizeDomain(url) {
    try {
        const u = new URL(url);
        return u.hostname.replace(/^www\./, '').toLowerCase();
    } catch {
        return url;
    }
}

// ============================================================
// 1. Google Custom Search API（メイン）
// ============================================================

async function searchGoogleCSE(config) {
    const { api_key, cx } = config.google_cse;
    if (!api_key || !cx) {
        console.log('[CSE] APIキーまたはCXが未設定。スキップします。');
        return null;
    }

    const keywords = config.search.keywords.join(' ');
    // ★ 「支援」を加えて「提供側」の会社に絞り込む。
    //   ネガティブキーワードで「事例記事」「まとめ記事」を排除
    // ★ v2.6.0: さらに「物理支援（不動産・建築・機器）」も検索エンジンレベルで排除し無駄な抽出を防ぐ
    const query = `${keywords} 支援 ${config.search.region} -事例 -導入事例 -成功事例 -比較 -ランキング -おすすめ -一覧 -不動産 -建築 -設計 -医療機器 -機器 -プロパティ -建設 -工事 -貿易 -製造 -臨床検査 -電子カルテ -レセコン -介護 -福祉 -医薬品`;
    const maxResults = config.search.max_results || 50;
    const results = [];
    const seenDomains = new Set();

    console.log(`[CSE] 検索クエリ: "${query}" (最大${maxResults}件)`);

    // CSEは1回のリクエストで最大10件。start=1,11,21...で取得
    const numPages = Math.ceil(maxResults / 10);

    for (let page = 0; page < numPages; page++) {
        const start = page * 10 + 1;
        if (start > 100) break; // CSEの上限は100件

        const url = `https://www.googleapis.com/customsearch/v1?key=${api_key}&cx=${cx}&q=${encodeURIComponent(query)}&start=${start}&lr=lang_ja&gl=jp`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                const errText = await response.text();
                console.error(`[CSE] APIエラー (start=${start}): ${response.status} - ${errText.substring(0, 200)}`);
                if (response.status === 429) {
                    console.log('[CSE] 日次クエリ上限到達。');
                    break;
                }
                continue;
            }

            const data = await response.json();
            const items = data.items || [];

            for (const item of items) {
                if (isExcludedUrl(item.link)) continue;
                const domain = normalizeDomain(item.link);
                if (seenDomains.has(domain)) continue;
                seenDomains.add(domain);

                results.push({
                    title: item.title || '',
                    url: item.link,
                    snippet: item.snippet || '',
                    source: 'google_cse',
                });
            }

            console.log(`[CSE] ページ${page + 1}: ${items.length}件取得 → 有効${results.length}件`);

            if (!data.queries?.nextPage) break; // もう次のページがない

        } catch (err) {
            console.error(`[CSE] リクエストエラー: ${err.message}`);
            break;
        }
    }

    console.log(`[CSE] 合計 ${results.length} 件の企業URL取得完了`);
    return results.length > 0 ? results : null;
}

// ============================================================
// 2. DuckDuckGo HTMLスクレイピング（サブ）
// ============================================================

async function searchDuckDuckGo(config, browser, queryOverride = null) {
    const keywords = config.search.keywords.join(' ');
    // ★ 同上: 支援 + ネガティブKWで「提供側」に絞る + 物理的支援（不動産・機器等）を検索レベルで弾く
    const query = queryOverride || `${keywords} 支援 ${config.search.region} -事例 -導入事例 -成功事例 -比較 -ランキング -おすすめ -一覧 -不動産 -建築 -設計 -医療機器 -機器 -プロパティ -建設 -工事 -貿易 -製造 -臨床検査 -電子カルテ -レセコン -介護 -福祉 -医薬品`;
    const maxResults = queryOverride ? 3 : (config.search.max_results || 50);
    const speed = config.speed || {};

    console.log(`[DDG] 検索クエリ: "${query}" (最大${maxResults}件)`);

    const context = await browser.newContext({
        locale: 'ja-JP',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    });
    const page = await context.newPage();
    const results = [];
    const seenDomains = new Set();

    try {
        // DuckDuckGoで検索（日本語優先設定）
        const searchUrl = `https://duckduckgo.com/?q=${encodeURIComponent(query)}&kl=jp-jp&ia=web`;
        await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await randomDelay(speed.page_wait_min || 2000, speed.page_wait_max || 5000);

        // 「もっと見る」ボタンを押してスクロールしながら結果を増やす
        let prevCount = 0;
        for (let attempt = 0; attempt < 10 && results.length < maxResults; attempt++) {
            // 結果を抽出
            const links = await page.evaluate(() => {
                const items = [];
                // DuckDuckGoの検索結果リンク
                document.querySelectorAll('article[data-testid="result"]').forEach(article => {
                    const linkEl = article.querySelector('a[data-testid="result-title-a"]');
                    const snippetEl = article.querySelector('span[data-testid="result-snippet"]');
                    if (linkEl) {
                        items.push({
                            title: linkEl.textContent?.trim() || '',
                            url: linkEl.href || '',
                            snippet: snippetEl?.textContent?.trim() || '',
                        });
                    }
                });
                // フォールバック: 古いDDGのDOM構造
                if (items.length === 0) {
                    document.querySelectorAll('.result__a, .result__title a').forEach(a => {
                        items.push({
                            title: a.textContent?.trim() || '',
                            url: a.href || '',
                            snippet: '',
                        });
                    });
                }
                return items;
            });

            for (const item of links) {
                if (isExcludedUrl(item.url)) continue;
                const domain = normalizeDomain(item.url);
                if (seenDomains.has(domain)) continue;
                seenDomains.add(domain);
                results.push({ ...item, source: 'duckduckgo' });
            }

            if (results.length >= maxResults) break;
            if (results.length === prevCount && attempt > 2) break; // 増えなくなったら終了
            prevCount = results.length;

            // 「もっと見る」ボタンをクリック
            try {
                const moreButton = page.locator('button#more-results, button:has-text("More results"), button:has-text("もっと見る")').first();
                if (await moreButton.isVisible({ timeout: 3000 })) {
                    await moreButton.click();
                    await randomDelay(speed.crawl_interval_min || 3000, speed.crawl_interval_max || 8000);
                } else {
                    // スクロールで追加読み込み
                    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
                    await randomDelay(2000, 4000);
                }
            } catch {
                break;
            }
        }
    } catch (err) {
        console.error(`[DDG] 検索エラー: ${err.message}`);
    } finally {
        await page.close();
        await context.close();
    }

    console.log(`[DDG] 合計 ${results.length} 件の企業URL取得完了`);
    return results.length > 0 ? results : null;
}

// ============================================================
// 3. Google検索 + 人間速度（最終手段）
// ============================================================

async function searchGoogleDirect(config, browser) {
    const query = `${keywords} 支援 ${config.search.region} -事例 -導入事例 -成功事例 -比較 -ランキング -おすすめ -一覧`;


    const maxResults = config.search.max_results || 50;
    const speed = config.speed || {};

    console.log(`[Google直接] 検索クエリ: "${query}" (人間速度モード)`);
    console.log('[Google直接] ※最終手段のため、CAPTCHA発生時は中断します');

    const context = await browser.newContext({
        locale: 'ja-JP',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        viewport: { width: 1366, height: 768 },
    });
    const page = await context.newPage();
    const results = [];
    const seenDomains = new Set();

    try {
        // まずGoogle.co.jpにアクセス
        await page.goto('https://www.google.co.jp/', { waitUntil: 'domcontentloaded', timeout: 30000 });
        await randomDelay(2000, 4000);

        // 検索ボックスに人間速度で入力
        const searchBox = page.locator('textarea[name="q"], input[name="q"]').first();
        await searchBox.click();
        await randomDelay(500, 1000);

        for (const char of query) {
            await searchBox.type(char, { delay: 50 + Math.random() * 100 });
        }
        await randomDelay(1000, 2000);

        // Enter で検索
        await page.keyboard.press('Enter');
        await page.waitForLoadState('domcontentloaded', { timeout: 15000 });
        await randomDelay(speed.page_wait_min || 2000, speed.page_wait_max || 5000);

        // CAPTCHA チェック
        const isCaptcha = await page.evaluate(() => {
            return document.body.textContent.includes('unusual traffic') ||
                   document.body.textContent.includes('お使いのコンピュータ ネットワークから通常と異なるトラフィック') ||
                   document.querySelector('#captcha-form') !== null;
        });

        if (isCaptcha) {
            console.log('[Google直接] CAPTCHA検出。この方法は使用できません。');
            await page.close();
            await context.close();
            return null;
        }

        // 検索結果ページを巡回
        for (let pageNum = 0; pageNum < 5 && results.length < maxResults; pageNum++) {
            // 広告を含む検索結果を取得
            const links = await page.evaluate(() => {
                const items = [];
                // オーガニック結果
                document.querySelectorAll('#search .g a[href^="http"], #rso .g a[href^="http"]').forEach(a => {
                    const h3 = a.querySelector('h3');
                    if (h3 && a.href) {
                        const parent = a.closest('.g');
                        const snippet = parent?.querySelector('.VwiC3b, .st, span[style]')?.textContent || '';
                        items.push({
                            title: h3.textContent?.trim() || '',
                            url: a.href,
                            snippet: snippet.trim(),
                            isAd: false,
                        });
                    }
                });
                // 広告結果
                document.querySelectorAll('#tads .uEierd a[href^="http"], #bottomads .uEierd a[href^="http"]').forEach(a => {
                    const title = a.querySelector('.sVXRqc, span[role="text"]')?.textContent || a.textContent;
                    if (title && a.href) {
                        items.push({
                            title: title.trim(),
                            url: a.href,
                            snippet: '',
                            isAd: true,
                        });
                    }
                });
                return items;
            });

            for (const item of links) {
                if (isExcludedUrl(item.url)) continue;
                const domain = normalizeDomain(item.url);
                if (seenDomains.has(domain)) continue;
                seenDomains.add(domain);
                results.push({
                    title: item.title,
                    url: item.url,
                    snippet: item.snippet,
                    source: item.isAd ? 'google_ad' : 'google_organic',
                });
            }

            console.log(`[Google直接] ページ${pageNum + 1}: 有効${results.length}件`);

            if (results.length >= maxResults) break;

            // 次のページへ（人間速度）
            const nextBtn = page.locator('#pnnext, a:has-text("次へ")').first();
            if (await nextBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
                await randomDelay(speed.crawl_interval_min || 3000, speed.crawl_interval_max || 8000);
                // マウスを動かしてからクリック
                const box = await nextBtn.boundingBox();
                if (box) {
                    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
                    await randomDelay(500, 1000);
                }
                await nextBtn.click();
                await page.waitForLoadState('domcontentloaded', { timeout: 15000 });
                await randomDelay(speed.page_wait_min || 2000, speed.page_wait_max || 5000);
            } else {
                break;
            }
        }
    } catch (err) {
        console.error(`[Google直接] エラー: ${err.message}`);
    } finally {
        await page.close();
        await context.close();
    }

    console.log(`[Google直接] 合計 ${results.length} 件の企業URL取得完了`);
    return results.length > 0 ? results : null;
}

// ============================================================
// エクスポート
// ============================================================

module.exports = {
    searchGoogleCSE,
    searchDuckDuckGo,
    searchGoogleDirect,
    isExcludedUrl,
    normalizeDomain,
    randomDelay,
    EXCLUDED_DOMAINS,
};
