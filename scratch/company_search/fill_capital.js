/**
 * fill_capital.js - 既存82社のURLをクロールして資本金を取得し、K列に書き込む
 */
const { chromium } = require('playwright');
const { getGoogleSheetsClient } = require('./sheets_writer');
const { CAPITAL_PATTERNS, COMPANY_PAGE_PATTERNS } = require('./crawler');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
let SHEET_NAME = 'Webマーケティング_大阪';

const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--sheet' && args[i+1]) {
        SHEET_NAME = args[i+1];
        i++;
    }
}

function normalizeDigits(text) {
    return text.replace(/[０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0));
}

function randomDelay(min, max) {
    return new Promise(r => setTimeout(r, min + Math.random() * (max - min)));
}

// 資本金の抽出パターン
const CAPITAL_REGEX = [
    /資本金[：:\s]*([０-９\d,.]+[万億]?円?[^\n<{]*)/,
    /([０-９\d,.]+[万億]円)\s*（.*?資本準備金/,
    /資本金[：:\s]*([^\n<{]{3,30})/,
];

async function extractCapital(page, url) {
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
        await randomDelay(1000, 2000);

        let fullText = await page.evaluate(() => document.body?.textContent || '');

        // 会社概要ページがあれば遷移
        const links = await page.evaluate(() =>
            Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href, text: (a.textContent || '').trim().substring(0, 100)
            }))
        );

        const companyPatterns = [/company/i, /about/i, /corporate/i, /会社概要/, /会社案内/, /会社情報/, /企業情報/, /企業概要/];
        let companyPageUrl = '';
        for (const link of links) {
            if (companyPatterns.some(p => p.test(link.href) || p.test(link.text))) {
                companyPageUrl = link.href;
                break;
            }
        }

        if (companyPageUrl && companyPageUrl !== url) {
            try {
                await page.goto(companyPageUrl, { waitUntil: 'domcontentloaded', timeout: 15000 });
                await randomDelay(1000, 2000);
                const companyText = await page.evaluate(() => document.body?.textContent || '');
                fullText += '\n' + companyText;
            } catch { }
        }

        // 資本金を抽出
        const normalized = normalizeDigits(fullText);
        for (const pattern of CAPITAL_REGEX) {
            const match = normalized.match(pattern);
            if (match) {
                let capital = match[1].trim();
                // 余分な部分を削除
                capital = capital.replace(/\s+/g, '').replace(/[（(].*/g, '').trim();
                if (capital.length > 30) capital = capital.substring(0, 30);
                return capital;
            }
        }
        return '';
    } catch (err) {
        console.log(`    エラー: ${err.message.substring(0, 50)}`);
        return '';
    }
}

async function main() {
    console.log('========================================');
    console.log('  資本金データ取得 & K列書き込み');
    console.log('========================================\n');

    const sheets = await getGoogleSheetsClient();

    // シートデータ読み取り
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);
    console.log(`対象: ${dataRows.length}社\n`);

    // K列(index 10)のインデックスを確認
    const capitalIdx = header.indexOf('資本金');
    if (capitalIdx < 0) {
        console.log('エラー: K列「資本金」ヘッダーが見つかりません');
        return;
    }
    console.log(`資本金列: ${String.fromCharCode(65 + capitalIdx)}列 (index ${capitalIdx})\n`);

    // 既に資本金がある行をスキップ
    const targets = [];
    for (let i = 0; i < dataRows.length; i++) {
        const existing = (dataRows[i][capitalIdx] || '').trim();
        if (!existing || existing === '不明') {
            targets.push({
                rowIdx: i,
                name: (dataRows[i][2] || '').trim(),
                url: (dataRows[i][4] || '').trim(),
                sheetRow: i + 2,
            });
        }
    }
    console.log(`取得対象: ${targets.length}社 (既取得: ${dataRows.length - targets.length}社)\n`);

    if (targets.length === 0) {
        console.log('全社の資本金が取得済みです。');
        return;
    }

    // ブラウザ起動
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });
    const page = await context.newPage();

    let found = 0, notFound = 0;
    const colLetter = String.fromCharCode(65 + capitalIdx);

    for (let t = 0; t < targets.length; t++) {
        const target = targets[t];
        console.log(`[${t + 1}/${targets.length}] ${target.name}`);
        console.log(`  URL: ${target.url}`);

        if (!target.url) {
            console.log('  → URLなし、スキップ\n');
            notFound++;
            continue;
        }

        const capital = await extractCapital(page, target.url);

        if (capital) {
            console.log(`  → 資本金: ${capital}`);
            found++;

            // K列に書き込み
            const cell = `${SHEET_NAME}!${colLetter}${target.sheetRow}`;
            await sheets.spreadsheets.values.update({
                spreadsheetId: SPREADSHEET_ID,
                range: cell,
                valueInputOption: 'USER_ENTERED',
                requestBody: { values: [[capital]] },
            });
            console.log(`  → ${cell} 書き込み完了\n`);
        } else {
            console.log('  → 資本金: 不明\n');
            notFound++;
        }

        // レート制限対策
        await randomDelay(500, 1500);
    }

    await browser.close();

    console.log('========================================');
    console.log(`  完了: 取得 ${found}社 / 不明 ${notFound}社`);
    console.log('========================================');
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
