/**
 * strict_cleanup.js - 強化版クリーンアップ (パターン検出 + Playwright精密照合)
 * 
 * STEP 1: パターンベースで明確にNG（ページタイトル混入、政府ドメイン、ポータルサイト等）を即削除
 * STEP 2: 残った全件に対してPlaywrightで実URLにアクセスし、
 *         <title> / OGP / <footer> に企業名(中核名)が含まれるか厳格確認 → 不一致は削除
 */
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);
const { getGoogleSheetsClient } = require('./sheets_writer');
const { isValidCompanyName } = require('./crawler');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
let SHEET_NAME = 'Webマーケティング';

const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--sheet' && args[i+1]) {
        SHEET_NAME = args[i+1];
        i++;
    }
}

function normalizeDomain(url) {
    if (!url) return '';
    try { return new URL(url).hostname.replace(/^(www|corp|en|ja|jp|info)\./i, '').toLowerCase(); }
    catch { return ''; }
}

function cleanNameForMatch(name) {
    if (!name) return '';
    return name.replace(/(株式会社|合同会社|有限会社|一般社団法人)/g, '').trim();
}

// ═══════════════════════════════════════════
//  STEP 1: パターンベース即削除
// ═══════════════════════════════════════════

// 確実にNGと判定できるドメイン
const ABSOLUTE_NG_DOMAINS = [
    // 政府・公的
    'soumu.go.jp', 'meti.go.jp', 'kantei.go.jp', 'mhlw.go.jp', 'maff.go.jp',
    // メディア・ニュース
    'impress.co.jp', 'itmedia.co.jp', 'nikkei.com', 'nhk.or.jp',
    'livedoor.com', 'excite.co.jp', 'goo.ne.jp', 'biglobe.ne.jp',
    // 掲示板・C2C
    'jimoty', 'jmty.jp', 'coconala.com',
    // クラウドソーシング
    'lancers.jp', 'crowdworks.jp',
    // 求人
    'mynavi.jp', 'doda.jp', 'en-japan.com', 'indeed.com', 'wantedly.com',
    'rikunabi.com', 'green-japan.com', 'hellowork.go.jp', 'hikoma.jp',
    // 比較・ランキング
    'dairitenkeisyu', 'proni.co.jp', 'imitsu.jp',
    // PR
    'prtimes.jp', 'atpress.ne.jp',
    // SNS系
    'note.com', 'qiita.com', 'hatena.ne.jp', 'medium.com',
    'twitter.com', 'x.com', 'facebook.com', 'instagram.com',
    // その他
    'keiei.ne.jp', 'kigyoshinbun.jp', 'netshop.impress.co.jp',
    'sgforum.impress.co.jp', 'thinkit.co.jp', 'webtan.impress.co.jp',
];

// 企業名のNG正規表現パターン
function isNamePatternNG(name) {
    if (!name) return true;
    const coreName = cleanNameForMatch(name);

    // 1. 法人格除去後1文字以下
    if (coreName.length <= 1) return true;

    // 2. パイプ文字（ページタイトル混入）
    if (/\|/.test(name)) return true;

    // 3. 検索結果・一覧・ランキング等
    if (/の検索結果|ページ目|ジモティー|検索結果/.test(name)) return true;

    // 4. 所在地・住所等のメタ情報
    if (/所在地|住所$|電話番号/.test(name)) return true;

    // 5. 明確な記事タイトル風
    if (/おすすめ\d+選|比較\d+選|ランキング\d+/.test(name)) return true;

    // 6. Web広告代理店・Web... のような記事タイトル
    if (/^Web.{15,}(代理店|おすすめ|会社|まとめ)/.test(name)) return true;

    // 7. 1文字英字+法人格のみ
    if (/^[A-Za-zＡ-Ｚａ-ｚ]株式会社$|^株式会社[A-Za-zＡ-Ｚａ-ｚ]$/.test(name)) return true;

    // 8. 40文字以上は異常
    if (name.length > 40) return true;

    // 9. 中国語のパターン
    if (/[游戏柯伊索](?:[游戏柯伊索])/.test(name)) return true;

    return false;
}

// URL自体がドメインのトップページでなく深い階層のポータルページか
function isAbsoluteNGUrl(url) {
    const domain = normalizeDomain(url);
    if (!domain) return true;

    // ドメイン自体がNG
    if (ABSOLUTE_NG_DOMAINS.some(d => domain.includes(d))) return true;

    // go.jp / lg.jp / ac.jp / ed.jp で終わる
    if (/\.(go|lg|ac|ed)\.jp$/.test(domain)) return true;

    return false;
}


// ═══════════════════════════════════════════
//  STEP 2: Playwright精密照合
// ═══════════════════════════════════════════
async function playwrightVerify(page, name, url) {
    try {
        const u = new URL(url);
        const rootUrl = `${u.protocol}//${u.hostname}/`;
        
        await page.goto(rootUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
        await page.waitForTimeout(1000);
        
        const coreName = cleanNameForMatch(name).toLowerCase();
        if (!coreName || coreName.length < 2) return false;

        // 部分一致検索用: 3文字以上の断片いずれかが含まれていればOK
        const fragments = [];
        if (coreName.length >= 3) fragments.push(coreName);
        // 社名が長い場合は前半部分でもチェック
        if (coreName.length >= 6) fragments.push(coreName.substring(0, Math.ceil(coreName.length / 2)));

        // 1. Title
        const title = (await page.evaluate(() => document.title || '')).toLowerCase();
        if (fragments.some(f => title.includes(f))) return true;

        // 2. OGP site_name
        const ogSiteName = (await page.evaluate(() => {
            const meta = document.querySelector('meta[property="og:site_name"]');
            return meta ? meta.content : '';
        })).toLowerCase();
        if (ogSiteName && fragments.some(f => ogSiteName.includes(f))) return true;

        // 3. Footer (Copyright)
        const footerText = (await page.evaluate(() => {
            const footer = document.querySelector('footer');
            return footer ? footer.textContent : '';
        })).toLowerCase();
        if (footerText && fragments.some(f => footerText.includes(f))) return true;

        // 4. 最後にbody末尾1500文字をチェック
        const bodyTail = (await page.evaluate(() => {
            return document.body ? document.body.innerText.substring(Math.max(0, document.body.innerText.length - 1500)) : '';
        })).toLowerCase();
        if (bodyTail && fragments.some(f => bodyTail.includes(f))) return true;

        console.log(`    ❌ 不一致: title="${title.substring(0, 60)}" に "${coreName}" なし`);
        return false;
    } catch (e) {
        console.log(`    ⚠️ アクセス不能: ${e.message.split('\n')[0].substring(0, 60)}`);
        return false; // アクセスできないURLは削除対象
    }
}

// ═══════════════════════════════════════════
//  メイン処理
// ═══════════════════════════════════════════
async function main() {
    console.log('═══════════════════════════════════════════');
    console.log('  強化版クリーンアップ + Playwright精密照合');
    console.log('═══════════════════════════════════════════\n');

    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const dataRows = allRows.slice(1);
    console.log(`[読取] ${dataRows.length}件\n`);

    // ━━━ STEP 1: パターンベース即削除 ━━━
    console.log('━━━ STEP 1: パターンベース検出 ━━━\n');
    const step1Delete = new Set();

    for (let i = 0; i < dataRows.length; i++) {
        const name = (dataRows[i][2] || '').trim();
        const url = (dataRows[i][4] || '').trim();

        if (isNamePatternNG(name)) {
            console.log(`  #${i + 1} [企業名NG] "${name}"`);
            step1Delete.add(i);
            continue;
        }
        if (isAbsoluteNGUrl(url)) {
            console.log(`  #${i + 1} [URL NG] "${name}" -> ${normalizeDomain(url)}`);
            step1Delete.add(i);
            continue;
        }
        if (!isValidCompanyName(name)) {
            console.log(`  #${i + 1} [バリデーション不合格] "${name}"`);
            step1Delete.add(i);
            continue;
        }
    }
    console.log(`\nSTEP 1 結果: ${step1Delete.size}件をパターンで検出\n`);

    // ━━━ STEP 2: Playwright精密照合（STEP1で除外されなかったもの全件） ━━━
    console.log('━━━ STEP 2: Playwright精密照合 ━━━\n');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        locale: 'ja-JP',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    });
    const page = await context.newPage();
    const step2Delete = new Set();
    let checked = 0;

    for (let i = 0; i < dataRows.length; i++) {
        if (step1Delete.has(i)) continue;
        const name = (dataRows[i][2] || '').trim();
        const url = (dataRows[i][4] || '').trim();
        if (!name || !url) { step2Delete.add(i); continue; }

        checked++;
        console.log(`  [${checked}] ${name} | ${url}`);
        const ok = await playwrightVerify(page, name, url);
        if (!ok) {
            console.log(`    🚨 削除: 企業名とURLが不一致`);
            step2Delete.add(i);
        } else {
            console.log(`    ✅ OK`);
        }

        // レート制限回避
        await page.waitForTimeout(1500);
    }
    await browser.close();

    console.log(`\nSTEP 2 結果: ${step2Delete.size}件がURL-企業名不一致\n`);

    // ━━━ STEP 3: 削除実行 ━━━
    const allDeletes = new Set([...step1Delete, ...step2Delete]);
    console.log(`━━━ STEP 3: 削除実行 (合計 ${allDeletes.size}件) ━━━\n`);

    if (allDeletes.size > 0) {
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
        const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
        const sheetId = sheet.properties.sheetId;

        // 削除リクエスト（後ろから順に）
        const sorted = [...allDeletes].sort((a, b) => b - a);
        await sheets.spreadsheets.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: {
                requests: sorted.map(idx => ({
                    deleteDimension: {
                        range: { sheetId, dimension: 'ROWS', startIndex: idx + 1, endIndex: idx + 2 }
                    }
                })),
            },
        });
        console.log(`✅ ${allDeletes.size}件を削除完了`);
        console.log(`  - パターンベース: ${step1Delete.size}件`);
        console.log(`  - Playwright照合: ${step2Delete.size}件`);
    }

    // ━━━ 最終件数 ━━━
    const final = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!B:C`,
    });
    const finalRows = (final.data.values || []).filter(r => r[0] && r[0] !== 'エリア');
    const areas = {};
    finalRows.forEach(r => { areas[r[0]] = (areas[r[0]] || 0) + 1; });

    console.log(`\n═══════════════════════════════════════════`);
    console.log(`  最終結果`);
    console.log(`═══════════════════════════════════════════`);
    console.log(`  修正前: ${dataRows.length}件`);
    console.log(`  削除: ${allDeletes.size}件`);
    console.log(`  最終: ${finalRows.length}件`);
    Object.entries(areas).forEach(([a, c]) => console.log(`    ${a}: ${c}社`));
    console.log(`\n  シートURL: https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit`);
}

main().catch(err => { console.error('Fatal:', err.message); process.exit(1); });
