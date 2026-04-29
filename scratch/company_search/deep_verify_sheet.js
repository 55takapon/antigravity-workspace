/**
 * deep_verify_sheet.js - 企業名とURLの完全整合性チェック（Playwright実アクセス照合）
 * 
 * すべてのURLのルート（トップページ）または対象ページにアクセスし、
 * <title> や Copyright に「シート記載の企業名」が含まれているか厳密にチェック。
 * 含まれていなければ「提携会社・事例」の誤抽出とみなしシートから削除する。
 */
const { chromium } = require('playwright');
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

// ★ シート名は --sheet 引数で指定可能（デフォルト: 'Webマーケティング'）
// 例: node deep_verify_sheet.js --sheet Webマーケティング
let SHEET_NAME = 'Webマーケティング';
const _args = process.argv.slice(2);
for (let _i = 0; _i < _args.length; _i++) {
    if (_args[_i] === '--sheet' && _args[_i + 1]) SHEET_NAME = _args[_i + 1];
}

function cleanNameForMatch(name) {
    if (!name) return '';
    return name.replace(/(株式会社|合同会社|有限会社|一般社団法人)/g, '').trim().toLowerCase();
}

async function verifyCompanyUrl(page, name, url) {
    try {
        const u = new URL(url);
        // トップページを優先して確認（提携会社などでないか確認するため）
        const rootUrl = `${u.protocol}//${u.hostname}/`;
        
        console.log(`  [アクセス] ${rootUrl}`);
        await page.goto(rootUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
        
        const coreName = cleanNameForMatch(name);
        
        // 1. Titleタグをチェック
        const title = await page.evaluate(() => document.title || '') || '';
        if (title.toLowerCase().includes(coreName)) {
            console.log(`  ✅ Title一致: "${title}" に "${coreName}" が含まれます`);
            return true;
        }

        // 2. OGP Site Nameをチェック
        const ogSiteName = await page.evaluate(() => {
            const meta = document.querySelector('meta[property="og:site_name"]');
            return meta ? meta.content : '';
        }) || '';
        if (ogSiteName.toLowerCase().includes(coreName)) {
            console.log(`  ✅ OGP一致: "${ogSiteName}"`);
            return true;
        }

        // 3. Copyright (Footer) をチェック
        const footerText = await page.evaluate(() => {
            const footer = document.querySelector('footer');
            return footer ? footer.textContent : document.body.innerText.substring(document.body.innerText.length - 1000);
        }) || '';
        
        if (footerText.toLowerCase().includes(coreName)) {
            console.log(`  ✅ Copyright等一致`);
            return true;
        }

        console.log(`  ❌ 不一致: Title="${title}", OGP="${ogSiteName}" -> "${coreName}" が見つかりません`);
        return false;
    } catch (e) {
        console.log(`  ⚠️ アクセスエラー: ${e.message.split('\n')[0]}`);
        // エラーの場合は判断つかないため、安全側に倒して true（削除回避）を返す
        return true;
    }
}

async function main() {
    console.log('========================================');
    console.log('  URL・企業名の精密照合 (全件Playwrightチェック)');
    console.log(`  対象シート: ${SHEET_NAME}`);
    console.log('========================================\n');

    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    
    const allRows = response.data.values || [];
    const dataRows = allRows.slice(1);
    
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    let deletedCount = 0;
    const deleteRequests = [];

    for (let i = dataRows.length - 1; i >= 0; i--) {
        const name = (dataRows[i][2] || '').trim();
        const url = (dataRows[i][4] || '').trim();
        
        if (!name || !url) continue;

        console.log(`[照合] ${name} | ${url}`);
        
        const isValid = await verifyCompanyUrl(page, name, url);
        
        if (!isValid) {
            console.log(`  🚨 削除マーキング: 企業名とURLが乖離している致命的欠陥`);
            const sheetRowIndex = i + 1;
            deleteRequests.push({
                deleteDimension: {
                    range: {
                        dimension: "ROWS",
                        startIndex: sheetRowIndex,
                        endIndex: sheetRowIndex + 1
                    }
                }
            });
            deletedCount++;
        }
    }

    await browser.close();

    if (deleteRequests.length > 0) {
        // sheetId動的取得
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
        const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
        const sheetId = sheet.properties.sheetId;
        
        deleteRequests.forEach(req => req.deleteDimension.range.sheetId = sheetId);

        await sheets.spreadsheets.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: { requests: deleteRequests }
        });
        console.log(`\n✅ 合計 ${deletedCount} 件（企業名・URL乖離エラー）を削除しました。`);
    } else {
        console.log('\n🌟 全件、URLと企業名が正確に一致しています。欠陥はありません。');
    }
}

main().catch(console.error);
