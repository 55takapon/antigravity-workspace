/**
 * fill_employees.js - 求人ボックス→Google検索で従業員数を取得しJ列に書き込み
 * 
 * 処理:
 *  1. シートから従業員数「不明」の企業を取得
 *  2. 求人ボックスで会社名検索 → 求人詳細ページの企業情報から従業員数抽出
 *  3. 取得できなければGoogle検索「{会社名} 従業員数」でフォールバック
 *  4. 取得した従業員数をJ列に書き込み
 *  5. 上場企業を検出した場合は削除対象としてマーク
 */
const { chromium } = require('playwright');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
let SHEET_NAME = 'Webマーケティング_大阪';

const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--sheet' && args[i+1]) {
        SHEET_NAME = args[i+1];
        i++;
    }
}

function randomDelay(min, max) {
    return new Promise(r => setTimeout(r, min + Math.random() * (max - min)));
}

// 従業員数の抽出パターン
const EMP_PATTERNS = [
    /従業員[数]?[：:\s]*[約]?([\d,]+)\s*[名人]/,
    /社員[数]?[：:\s]*[約]?([\d,]+)\s*[名人]/,
    /スタッフ[：:\s]*[約]?([\d,]+)\s*[名人]/,
    /([\d,]+)\s*(?:名|人)\s*(?:在籍|所属)/,
    /正社員[：:\s]*([\d,]+)[名人]/,
    /従業員[：:\s]*約?([\d,]+)/,
];

// 上場キーワード（検出したら除外対象）
const LISTED_KEYWORDS = [
    '東証プライム', '東証スタンダード', '東証グロース',
    '東証一部', '東証二部', 'JASDAQ', 'マザーズ',
    '上場企業', '証券コード', '株式上場', 'IPO',
    '東京証券取引所', '名古屋証券取引所', '札幌証券取引所', '福岡証券取引所',
];

function detectListed(text) {
    return LISTED_KEYWORDS.some(kw => text.includes(kw));
}

// === STEP1: 求人ボックスで検索 ===
async function searchKyujinBox(page, companyName) {
    try {
        // URL直接アクセス方式（入力不要）
        const searchUrl = `https://xn--pckua2a7gp15o89zb.com/${encodeURIComponent(companyName + 'の仕事')}`;
        await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
        await randomDelay(1500, 3000);

        const text = await page.evaluate(() => document.body?.textContent || '');

        // 上場チェック
        if (detectListed(text)) {
            return { employees: null, listed: true };
        }

        // 求人詳細ページへ遷移して企業情報を確認
        const jobLinks = await page.evaluate(() =>
            Array.from(document.querySelectorAll('a[href*="/jb/"]')).map(a => a.href).slice(0, 3)
        );

        for (const link of jobLinks) {
            try {
                await page.goto(link, { waitUntil: 'domcontentloaded', timeout: 15000 });
                await randomDelay(1000, 2000);
                const jobText = await page.evaluate(() => document.body?.textContent || '');

                // 上場チェック
                if (detectListed(jobText)) {
                    return { employees: null, listed: true };
                }

                // 従業員数を抽出
                for (const pattern of EMP_PATTERNS) {
                    const match = jobText.match(pattern);
                    if (match) {
                        const count = parseInt(match[1].replace(/,/g, ''), 10);
                        if (count > 0 && count < 100000) {
                            return { employees: count, listed: false };
                        }
                    }
                }
            } catch { }
        }

        return { employees: null, listed: false };
    } catch {
        return { employees: null, listed: false };
    }
}

// === STEP2: Google検索でフォールバック ===
async function searchGoogle(page, companyName) {
    try {
        const query = encodeURIComponent(`${companyName} 従業員数 会社概要`);
        await page.goto(`https://www.google.com/search?q=${query}`, {
            waitUntil: 'domcontentloaded', timeout: 15000
        });
        await randomDelay(2000, 4000);

        const text = await page.evaluate(() => document.body?.textContent || '');

        // 上場チェック
        if (detectListed(text)) {
            return { employees: null, listed: true };
        }

        // 従業員数を抽出
        for (const pattern of EMP_PATTERNS) {
            const match = text.match(pattern);
            if (match) {
                const count = parseInt(match[1].replace(/,/g, ''), 10);
                if (count > 0 && count < 100000) {
                    return { employees: count, listed: false };
                }
            }
        }

        return { employees: null, listed: false };
    } catch {
        return { employees: null, listed: false };
    }
}

async function main() {
    console.log('========================================');
    console.log('  従業員数取得 (求人ボックス→Google)');
    console.log('========================================\n');

    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);

    const empIdx = header.indexOf('従業員数');
    if (empIdx < 0) { console.log('従業員数列なし'); return; }
    const empCol = String.fromCharCode(65 + empIdx);

    // 対象: 従業員数が空/不明/null
    const targets = [];
    for (let i = 0; i < dataRows.length; i++) {
        const emp = (dataRows[i][empIdx] || '').trim();
        if (!emp || emp === '不明' || emp === 'null') {
            targets.push({
                idx: i,
                name: (dataRows[i][2] || '').trim(),
                url: (dataRows[i][4] || '').trim(),
                row: i + 2,
            });
        }
    }

    console.log(`対象: ${targets.length}社 (従業員数不明)\n`);
    if (targets.length === 0) { console.log('全社取得済み'); return; }

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    });
    const page = await context.newPage();

    let found = 0, listed = 0, unknown = 0;
    const listedCompanies = [];

    for (let t = 0; t < targets.length; t++) {
        const target = targets[t];
        console.log(`[${t + 1}/${targets.length}] ${target.name}`);

        // STEP1: 求人ボックス
        let result = await searchKyujinBox(page, target.name);

        if (result.listed) {
            console.log(`  → 上場企業検出 → 除外対象`);
            listedCompanies.push({ name: target.name, row: target.row });
            listed++;
            continue;
        }

        // STEP2: Googleフォールバック
        if (!result.employees) {
            result = await searchGoogle(page, target.name);
            if (result.listed) {
                console.log(`  → 上場企業検出 (Google) → 除外対象`);
                listedCompanies.push({ name: target.name, row: target.row });
                listed++;
                continue;
            }
        }

        if (result.employees) {
            console.log(`  → 従業員数: ${result.employees}名`);
            await sheets.spreadsheets.values.update({
                spreadsheetId: SPREADSHEET_ID,
                range: `${SHEET_NAME}!${empCol}${target.row}`,
                valueInputOption: 'USER_ENTERED',
                requestBody: { values: [[result.employees]] },
            });
            found++;
        } else {
            console.log(`  → 不明`);
            unknown++;
        }

        await randomDelay(1000, 2000);
    }

    await browser.close();

    console.log('\n========================================');
    console.log(`  結果: 取得 ${found}社 / 上場企業 ${listed}社 / 不明 ${unknown}社`);
    console.log('========================================');

    if (listedCompanies.length > 0) {
        console.log('\n⚠️ 上場企業（要確認・除外候補）:');
        for (const c of listedCompanies) {
            console.log(`  - 行${c.row}: ${c.name}`);
        }
    }
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
