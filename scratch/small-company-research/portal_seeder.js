/**
 * portal_seeder.js - ポータルサイトから企業シードを収集する
 *
 * 対象ポータル:
 *   1. Web奉行 (web-bugyo.com) — 第一優先
 *   2. PRONIアイミツ (imitsu.jp) — 第二（件数多め）
 *
 * 出力: seeds.jsonl（1行1JSON）
 *
 * ★ 重複フィルター設計:
 *   起動時に既存シート（Webマーケティング + 名古屋）の全URLからドメインインデックスを構築。
 *   ポータル詳細ページで candidate_url が判明した「直後」にドメイン照合し、
 *   既存データとの重複なら公式サイトクロールをスキップ。クロールコストゼロ。
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

// ─────────────────────────────────
//  設定
// ─────────────────────────────────

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const EXISTING_SHEETS = ['Webマーケティング', 'Webマーケティング_名古屋', 'クリニック専門支援', 'Web奉行'];

const REGIONS = {
    osaka:   { name: '大阪府', bugyo: 'osaka',   imitsu: 'pr-osaka' },
    hyogo:   { name: '兵庫県', bugyo: 'hyogo',   imitsu: 'pr-hyogo' },
    mie:     { name: '三重県', bugyo: 'mie',     imitsu: 'pr-mie' },
    shiga:   { name: '滋賀県', bugyo: 'shiga',   imitsu: 'pr-shiga' },
    nara:    { name: '奈良県', bugyo: 'nara',    imitsu: 'pr-nara' },
    wakayama:{ name: '和歌山県', bugyo: 'wakayama', imitsu: 'pr-wakayama' },
    kyoto:   { name: '京都府', bugyo: 'kyoto',   imitsu: 'pr-kyoto' },
    aichi:   { name: '愛知県', bugyo: 'aichi',   imitsu: 'pr-aichi' },
    fukuoka: { name: '福岡県', bugyo: 'fukuoka', imitsu: 'pr-fukuoka' },
    tokyo:   { name: '東京都', bugyo: 'tokyo',   imitsu: 'pr-tokyo' },
    kanagawa:{ name: '神奈川県', bugyo: 'kanagawa',imitsu: 'pr-kanagawa' },
    saitama: { name: '埼玉県', bugyo: 'saitama', imitsu: 'pr-saitama' },
    chiba:   { name: '千葉県', bugyo: 'chiba',   imitsu: 'pr-chiba' },
    ibaraki: { name: '茨城県', bugyo: 'ibaraki', imitsu: 'pr-ibaraki' },
    tochigi: { name: '栃木県', bugyo: 'tochigi', imitsu: 'pr-tochigi' },
    gunma:   { name: '群馬県', bugyo: 'gunma',   imitsu: 'pr-gunma' },
};

// コマンドライン引数からリージョン取得
const args = process.argv.slice(2);
const regionIdx = args.indexOf('--region');
const regionArg = regionIdx !== -1 ? args[regionIdx + 1] : 'osaka';

const maxPagesIdx = args.indexOf('--max-pages');
const MAX_PAGES_BUGYO = maxPagesIdx !== -1 ? parseInt(args[maxPagesIdx + 1], 10) : 30;

const SKIP_IMITSU = args.includes('--skip-imitsu');
const DRY_RUN = args.includes('--dry-run');

const region = REGIONS[regionArg];
if (!region) {
    console.error(`❌ 未知のリージョン: ${regionArg}`);
    console.log('利用可能:', Object.keys(REGIONS).join(', '));
    process.exit(1);
}

const OUTPUT_FILE = path.join(__dirname, `seeds_${regionArg}.jsonl`);

// ─────────────────────────────────
//  除外ドメイン（references/exclude-domains.md から）
// ─────────────────────────────────

const EXCLUDE_DOMAINS = new Set([
    'web-kanji.com', 'web-bugyo.com', 'imitsu.jp',
    'mynavi.jp', 'doda.jp', 'rikunabi.co.jp', 'indeed.com', 'en-japan.com',
    'type.jp', 'twitter.com', 'x.com', 'facebook.com', 'instagram.com',
    'linkedin.com', 'youtube.com', 'tiktok.com', 'note.com', 'ameblo.jp',
    'line.me', 'amazon.co.jp', 'rakuten.co.jp', 'yahoo.co.jp', 'mercari.com',
    'prtimes.jp', 'itreview.jp', 'boxil.jp', 'ferret-plus.com', 'liskul.com',
    'google.com', 'nikkei.com', 'asahi.com', 'mainichi.jp', 'yomiuri.co.jp',
    'wikipedia.org', 'ja.wikipedia.org', 'recruit.co.jp', 'wantedly.com',
    'bizreach.jp', 'green-japan.com', 'cyberagent.co.jp', 'dentsu.co.jp',
    'hakuhodo.co.jp', 'ntt.com', 'softbank.jp', 'kddi.com', 'toyota.co.jp',
]);

function isDomainExcluded(url) {
    try {
        const hostname = new URL(url).hostname.replace(/^www\./, '').toLowerCase();
        for (const ex of EXCLUDE_DOMAINS) {
            if (hostname === ex || hostname.endsWith('.' + ex)) return true;
        }
        return false;
    } catch { return true; }
}

function normalizeDomain(url) {
    try {
        return new URL(url).hostname.replace(/^www\./, '').toLowerCase();
    } catch { return ''; }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 対象スプレッドシートID
const SPREADSHEETS = [
    '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk',
    '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ'
];

async function buildExistingIndex() {
    const existingDomains = new Set();
    const excludeFilePath = path.join(__dirname, '..', 'company_search', 'exclude_domains.txt');
    
    if (!fs.existsSync(excludeFilePath)) {
        console.warn(`[重複チェック] 軽量フィルタファイルが見つかりません: ${excludeFilePath}`);
        return existingDomains;
    }
    
    try {
        const content = fs.readFileSync(excludeFilePath, 'utf-8');
        const lines = content.split('\n');
        for (const line of lines) {
            const domain = line.trim();
            if (domain) {
                existingDomains.add(domain);
            }
        }
        console.log(`[重複チェック] 軽量フィルタ読込完了: ${existingDomains.size} ドメイン (exclude_domains.txt)`);
    } catch (e) {
        console.error(`[重複チェック] 読み込みエラー: ${e.message}`);
    }

    return existingDomains;
}

// ─────────────────────────────────
//  Web奉行スクレイパー
// ─────────────────────────────────

async function scrapeWebBugyo(page, regionKey, regionName, existingDomains) {
    const seeds = [];
    let pageNum = 1;

    console.log(`\n[Web奉行] ${regionName} の収集開始`);

    while (pageNum <= MAX_PAGES_BUGYO) {
        const url = pageNum === 1
            ? `https://web-bugyo.com/category/${regionKey}/`
            : `https://web-bugyo.com/category/${regionKey}/page/${pageNum}/`;

        console.log(`  [Web奉行] ページ${pageNum}: ${url}`);

        try {
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
            await delay(1500);

            // 企業一覧を取得
            const items = await page.evaluate(() => {
                // Web奉行のDOM構造: div.p-postList__item > a.p-postList__link
                // aタグ自体が詳細ページへのリンクで、内部にh2がある
                return Array.from(document.querySelectorAll('div.p-postList__item a.p-postList__link, .p-postList__item a.p-postList__link')).map(el => {
                    const h2 = el.querySelector('h2, h2.p-postList__title, .p-postList__title');
                    return {
                        detailUrl: el.href || '',
                        companyName: h2?.textContent?.trim() || el.textContent?.trim().substring(0, 50) || '',
                    };
                }).filter(item => item.detailUrl && item.companyName && item.detailUrl.includes('web-bugyo.com'));
            });

            if (items.length === 0) {
                console.log(`  [Web奉行] 企業なし、終了`);
                break;
            }

            console.log(`  [Web奉行] ${items.length}件の企業ページを発見`);

            // 各企業の詳細ページから公式URLを取得
            for (const item of items) {
                try {
                    await page.goto(item.detailUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
                    await delay(1000);

                    const detail = await page.evaluate(() => {
                        const rows = Array.from(document.querySelectorAll('table tr, dl dt'));
                        let officialUrl = '';
                        let representative = '';

                        // th/td テーブル形式
                        document.querySelectorAll('table tr').forEach(tr => {
                            const th = tr.querySelector('th');
                            const td = tr.querySelector('td');
                            if (!th || !td) return;
                            const label = th.textContent.trim();
                            if (/サイトURL|公式サイト|URL|ホームページ/i.test(label)) {
                                const a = td.querySelector('a');
                                officialUrl = a?.href || td.textContent.trim();
                            }
                            if (/代表者|代表取締役|担当者/i.test(label)) {
                                representative = td.textContent.trim();
                            }
                        });

                        // dl/dt/dd 形式フォールバック
                        if (!officialUrl) {
                            document.querySelectorAll('dl').forEach(dl => {
                                const dts = dl.querySelectorAll('dt');
                                const dds = dl.querySelectorAll('dd');
                                dts.forEach((dt, i) => {
                                    if (/サイトURL|URL|公式|ホームページ/i.test(dt.textContent)) {
                                        const a = dds[i]?.querySelector('a');
                                        officialUrl = a?.href || dds[i]?.textContent.trim() || '';
                                    }
                                    if (/代表者|代表取締役/i.test(dt.textContent)) {
                                        representative = dds[i]?.textContent.trim() || '';
                                    }
                                });
                            });
                        }

                        return { officialUrl, representative };
                    });

                    if (!detail.officialUrl || isDomainExcluded(detail.officialUrl)) {
                        console.log(`    [スキップ] ${item.companyName}: URL不正または除外ドメイン (${detail.officialUrl})`);
                        continue;
                    }

                    // ★ 既存データとの重複チェック（クロール前に実施）
                    const candidateDomain = normalizeDomain(detail.officialUrl);
                    if (existingDomains.has(candidateDomain)) {
                        console.log(`    [重複] ${item.companyName}: 既存データに存在 (${candidateDomain})`);
                        continue;
                    }

                    // ★ 企業名バリデーション（まとめ記事・アフィ系を除外）
                    const isArticleTitle = /選！|おすすめ|ランキング|まとめ|ご紹介|の作り方|レンタルサーバー|ドメイン取得|比較|選び方/.test(item.companyName);
                    if (isArticleTitle) {
                        console.log(`    [記事除外] ${item.companyName}`);
                        continue;
                    }
                    if (/px\.a8\.net|af\.moshimo\.com|ck\.jp\.ap\.valuecommerce/.test(detail.officialUrl)) {
                        console.log(`    [除外] アフィリエイトURL: ${detail.officialUrl}`);
                        continue;
                    }

                    const seed = {
                        company_name: item.companyName,
                        candidate_url: detail.officialUrl,
                        representative_hint: detail.representative,
                        portal_source: 'web-bugyo',
                        portal_category: 'Web制作',
                        region: regionName,
                        portal_page_url: item.detailUrl,
                    };
                    seeds.push(seed);
                    if (!DRY_RUN) console.log(`    ✅ ${item.companyName} → ${detail.officialUrl}`);

                } catch (err) {
                    console.log(`    [エラー] ${item.companyName}: ${err.message.substring(0, 60)}`);
                }
                await delay(800);
            }

            // 次ページ確認
            const hasNext = await page.evaluate(() => {
                const next = document.querySelector('a.next.page-numbers, .next a, [rel="next"]');
                return !!next;
            });

            if (!hasNext) {
                console.log(`  [Web奉行] 最終ページ到達`);
                break;
            }

            pageNum++;
            await delay(2000);

        } catch (err) {
            console.log(`  [Web奉行] ページ${pageNum}エラー: ${err.message.substring(0, 80)}`);
            break;
        }
    }

    console.log(`[Web奉行] ${regionName}: ${seeds.length}件収集完了`);
    return seeds;
}

// ─────────────────────────────────
//  PRONIアイミツスクレイパー
// ─────────────────────────────────

async function scrapeIimitsu(page, regionKey, regionName, existingDomains) {
    const seeds = [];
    let pageNum = 1;
    const MAX_PAGES_IMITSU = 10; // 件数が多いので上限を設ける

    console.log(`\n[PRONIアイミツ] ${regionName} の収集開始`);

    while (pageNum <= MAX_PAGES_IMITSU) {
        const url = pageNum === 1
            ? `https://imitsu.jp/ct-hp-design/${regionKey}/`
            : `https://imitsu.jp/ct-hp-design/${regionKey}/?page=${pageNum}`;

        console.log(`  [アイミツ] ページ${pageNum}: ${url}`);

        try {
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
            await delay(2000);

            // モーダルを閉じる（存在する場合）
            try {
                const closeBtn = await page.$('button[aria-label="Close"], .modal-close, [data-dismiss="modal"], button.close');
                if (closeBtn) {
                    await closeBtn.click();
                    await delay(500);
                }
            } catch { }

            const items = await page.evaluate(() => {
                // 企業カードのセレクタ（構造が変更されている可能性あり）
                const cards = Array.from(document.querySelectorAll(
                    'article.service-card, .vendor-card, .company-card, [class*="service-card"], [class*="company-item"]'
                ));

                if (cards.length > 0) {
                    return cards.map(card => {
                        const link = card.querySelector('a[href*="/lp/"], a.service-title-link, h3 a, h2 a');
                        const name = card.querySelector('h3, h2, .service-name, .company-name');
                        return {
                            detailUrl: link?.href || '',
                            companyName: name?.textContent?.trim() || '',
                        };
                    }).filter(i => i.detailUrl && i.companyName);
                }

                // フォールバック: 全リンクから会社詳細ページと思われるものを抽出
                return Array.from(document.querySelectorAll('a[href*="/lp/"]')).map(a => ({
                    detailUrl: a.href,
                    companyName: a.textContent.trim().substring(0, 50),
                })).filter(i => i.companyName.length > 2);
            });

            if (items.length === 0) {
                console.log(`  [アイミツ] 企業なし、終了`);
                break;
            }

            console.log(`  [アイミツ] ${items.length}件の企業ページを発見`);

            for (const item of items) {
                try {
                    await page.goto(item.detailUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
                    await delay(1000);

                    // モーダルを閉じる
                    try {
                        const closeBtn = await page.$('button[aria-label="Close"], .modal-close, [data-dismiss="modal"]');
                        if (closeBtn) { await closeBtn.click(); await delay(500); }
                    } catch { }

                    const detail = await page.evaluate(() => {
                        let officialUrl = '';

                        // 外部リンク（公式HP）を探す
                        const allLinks = Array.from(document.querySelectorAll('a[href^="http"]'));
                        for (const a of allLinks) {
                            const href = a.href;
                            const label = (a.textContent + a.getAttribute('aria-label') + (a.closest('*')?.getAttribute('data-label') || '')).trim();
                            if (/公式|サイト|ホームページ|HP|Web|会社|URL/i.test(label)) {
                                if (!href.includes('imitsu.jp') && !href.includes('google.com')) {
                                    officialUrl = href;
                                    break;
                                }
                            }
                        }

                        // フォールバック: 会社情報テーブルから取得
                        if (!officialUrl) {
                            document.querySelectorAll('table tr, dl').forEach(el => {
                                const text = el.textContent;
                                if (/URL|ホームページ|公式サイト/i.test(text)) {
                                    const a = el.querySelector('a[href^="http"]');
                                    if (a && !a.href.includes('imitsu.jp')) {
                                        officialUrl = a.href;
                                    }
                                }
                            });
                        }

                        return { officialUrl };
                    });

                    if (!detail.officialUrl || isDomainExcluded(detail.officialUrl)) {
                        console.log(`    [スキップ] ${item.companyName}: URL不正 (${detail.officialUrl})`);
                        continue;
                    }

                    // ★ 既存データとの重複チェック（クロール前に実施）
                    const candidateDomain = normalizeDomain(detail.officialUrl);
                    if (existingDomains.has(candidateDomain)) {
                        console.log(`    [重複] ${item.companyName}: 既存データに存在 (${candidateDomain})`);
                        continue;
                    }

                    const seed = {
                        company_name: item.companyName,
                        candidate_url: detail.officialUrl,
                        representative_hint: '',
                        portal_source: 'imitsu',
                        portal_category: 'Web制作',
                        region: regionName,
                        portal_page_url: item.detailUrl,
                    };
                    seeds.push(seed);
                    if (!DRY_RUN) console.log(`    ✅ ${item.companyName} → ${detail.officialUrl}`);

                } catch (err) {
                    console.log(`    [エラー] ${item.companyName}: ${err.message.substring(0, 60)}`);
                }
                await delay(800);
            }

            pageNum++;
            await delay(2000);

        } catch (err) {
            console.log(`  [アイミツ] ページ${pageNum}エラー: ${err.message.substring(0, 80)}`);
            break;
        }
    }

    console.log(`[PRONIアイミツ] ${regionName}: ${seeds.length}件収集完了`);
    return seeds;
}

// ─────────────────────────────────
//  重複排除（ドメイン正規化）
// ─────────────────────────────────

function normalizeDomain(url) {
    try {
        return new URL(url).hostname.replace(/^www\./, '').toLowerCase();
    } catch { return url; }
}

function deduplicateSeeds(seeds, existingDomains = new Set()) {
    const seen = new Set();
    const filtered = [];
    let dupExisting = 0;
    let dupInBatch = 0;

    for (const seed of seeds) {
        const domain = normalizeDomain(seed.candidate_url);
        if (existingDomains.has(domain)) {
            dupExisting++;
            continue;
        }
        if (seen.has(domain)) {
            dupInBatch++;
            continue;
        }
        seen.add(domain);
        filtered.push(seed);
    }

    if (dupExisting > 0) console.log(`  [重複除去] 既存DBとの重複: ${dupExisting}件`);
    if (dupInBatch > 0) console.log(`  [重複除去] バッチ内（府県またぎ含む）重複: ${dupInBatch}件`);
    return filtered;
}

// ─────────────────────────────────
//  メイン
// ─────────────────────────────────

async function main() {
    console.log('========================================');
    console.log(`  ポータルシードコレクター`);
    console.log(`  対象: ${region.name}`);
    console.log(`  出力: ${OUTPUT_FILE}`);
    console.log('========================================\n');

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        locale: 'ja-JP',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    });

    // ★ 起動時に既存シートのドメインインデックスを構築
    const existingDomains = await buildExistingIndex();

    let allSeeds = [];

    try {
        // ① Web奉行
        const page1 = await context.newPage();
        const bugyoSeeds = await scrapeWebBugyo(page1, region.bugyo, region.name, existingDomains);
        await page1.close();
        allSeeds.push(...bugyoSeeds);

        // ② PRONIアイミツ（--skip-imitsuがない場合）
        if (!SKIP_IMITSU) {
            const page2 = await context.newPage();
            const imitsuSeeds = await scrapeIimitsu(page2, region.imitsu, region.name, existingDomains);
            await page2.close();
            allSeeds.push(...imitsuSeeds);
        }

    } finally {
        await context.close();
        await browser.close();
    }

    // 重複排除（同一バッチ内）
    const beforeDedupe = allSeeds.length;
    allSeeds = deduplicateSeeds(allSeeds, existingDomains);
    console.log(`\n重複排除: ${beforeDedupe}件 \u2192 ${allSeeds.length}件`);

    // 出力
    if (!DRY_RUN) {
        const output = allSeeds.map(s => JSON.stringify(s)).join('\n');
        fs.writeFileSync(OUTPUT_FILE, output, 'utf-8');
        console.log(`\n✅ ${allSeeds.length}件を ${OUTPUT_FILE} に保存しました`);

        // ★ 府県またぎ重複を防ぐため、収集したドメインを即座に exclude_domains.txt へ追記
        // （次の府県を処理する別プロセスがこのファイルを読み込むため、漏れがなくなる）
        try {
            const excludeFilePath = path.join(__dirname, '..', 'company_search', 'exclude_domains.txt');
            const existing = new Set();
            if (fs.existsSync(excludeFilePath)) {
                fs.readFileSync(excludeFilePath, 'utf-8').split('\n').forEach(d => {
                    if (d.trim()) existing.add(d.trim());
                });
            }
            let addedCount = 0;
            for (const seed of allSeeds) {
                const domain = normalizeDomain(seed.candidate_url);
                if (domain && !existing.has(domain)) {
                    existing.add(domain);
                    addedCount++;
                }
            }
            if (addedCount > 0) {
                fs.writeFileSync(excludeFilePath, Array.from(existing).sort().join('\n'), 'utf-8');
                console.log(`[exclude_domains.txt] +${addedCount}件を即時追記 → 合計${existing.size}件（府県またぎ重複防止）`);
            }
        } catch (err) {
            console.error(`[exclude_domains.txt] 追記エラー: ${err.message}`);
        }
    } else {
        console.log('\n[ドライラン] 書き込みなし。サンプル:');
        allSeeds.slice(0, 5).forEach(s => console.log('  ', JSON.stringify(s)));
    }

    console.log('\n完了！');
    console.log(`次ステップ: node search_companies_v2.js --seeds ${OUTPUT_FILE} --region ${regionArg}`);
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
