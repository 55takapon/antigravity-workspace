/**
 * check_ng_forms.js - 問い合わせフォームの営業NG文言チェック
 *
 * 【鉄則】I列（送信不可理由）が空欄の行にのみ書き込む。
 *         既に値がある行は絶対にスキップする。消去機能は存在しない。
 *
 * 【判定方針】愚直（dumb）なキーワードマッチング。
 *   - 例外ルール（EXCLUDE_PATTERNS）は一切持たない。
 *   - 「営業のご連絡」がプルダウンの選択肢であっても、テキストに含まれていれば NG として記録する。
 *   - 誤検知（False Positive）は人間が目視で I列に「OK」or「【手動承認】」と入力して復帰させる。
 *   - 見落とし（False Negative）をゼロにすることを最優先とする。
 *
 * Usage:
 *   node check_ng_forms.js                     # I列空欄の全件チェック
 *   node check_ng_forms.js --dry-run            # テスト（書き込みなし）
 *   node check_ng_forms.js --max 20             # 最大20件チェック
 *   node check_ng_forms.js --sheet Webマーケティング_名古屋
 */

'use strict';

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const {
    SPREADSHEET_ID, TARGET_SHEETS, COL, NG_PREFIX,
    isWritable, getGoogleSheetsClient, normalizeDomain,
} = require('./schema');

// ─────────────────────────────────
//  コマンドライン引数
// ─────────────────────────────────

const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
let maxCheck = Infinity;
let sheetName = 'Webマーケティング';

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--max' && args[i + 1]) maxCheck = parseInt(args[i + 1], 10);
    if (args[i] === '--sheet' && args[i + 1]) { sheetName = args[i + 1]; i++; }
}

// ─────────────────────────────────
//  NGキーワード（愚直マッチング）
// ─────────────────────────────────

const NG_KEYWORDS = [
    '売り込み', '売込み',
    'セールス目的', 'セールスお断り',
    '営業お断り', '営業はお断り', '営業のお断り',
    '営業ご遠慮', '営業はご遠慮', '営業をご遠慮',
    '営業お控え', '営業はお控え',
    '営業メールはお断り', '営業メールは申し訳',
    '営業目的のお問い合わせ', '営業目的でのお問い合わせ',
    '営業目的のご連絡', '営業目的でのご連絡',
    '営業目的のメール', '営業目的でのメール',
    '営業の方はご遠慮', '営業の方は固く',
    '営業のご連絡', '営業のご案内', '営業のご提案',
    '営業活動はお断り', '営業行為はお断り',
    '営業には返信', '返信いたしかね',
    '勧誘はお断り', '勧誘お断り', '勧誘ご遠慮',
    '当社への営業', '弊社への営業',
    '営業・広報関連',
    '営業を目的としたお問い合わせはお断り',
    '営業禁止',
];

/**
 * ページテキストからNG文言を検出する（愚直マッチ）
 * @param {string} bodyText
 * @returns {{ keyword: string } | null}
 */
function detectNG(bodyText) {
    const text = bodyText.toLowerCase();
    for (const kw of NG_KEYWORDS) {
        if (text.includes(kw.toLowerCase())) {
            // 文脈の一文を抽出（表示用）
            const idx = bodyText.indexOf(kw);
            if (idx === -1) continue;
            const start = Math.max(0, bodyText.lastIndexOf('\n', idx) + 1);
            const end = bodyText.indexOf('\n', idx);
            const line = bodyText.substring(start, end === -1 ? undefined : end).trim();
            return { keyword: kw, context: line.substring(0, 200) };
        }
    }
    return null;
}

async function checkFormPage(page, url) {
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
        await page.waitForTimeout(2000);

        const bodyText = await page.evaluate(() => {
            return document.body ? document.body.innerText : '';
        });

        const hit = detectNG(bodyText);
        if (hit) {
            return { hasNG: true, context: hit.context };
        }
        return { hasNG: false };
    } catch (err) {
        return { hasNG: false, error: err.message.substring(0, 100) };
    }
}

async function main() {
    console.log('========================================');
    console.log('  動的チェック（check_ng_forms）');
    console.log(`  モード: ${isDryRun ? 'ドライラン' : '本番'}`);
    console.log(`  シート: ${sheetName}`);
    console.log(`  最大件数: ${maxCheck === Infinity ? '全件' : maxCheck}`);
    console.log('  判定方式: 愚直キーワードマッチ（例外ルールなし）');
    console.log('========================================\n');

    const sheetsClient = await getGoogleSheetsClient();
    const response = await sheetsClient.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });

    const allRows = response.data.values || [];
    console.log(`全${allRows.length - 1}件のデータを取得\n`);

    // ★ I列が空欄 かつ フォームURLがある行のみ対象
    const targets = [];
    for (let i = 1; i < allRows.length; i++) {
        const row = allRows[i];
        while (row.length < 16) row.push('');

        const currentI = (row[COL.REJECT_REASON] || '').trim();
        const formUrl  = (row[COL.FORM_URL] || '').trim();
        const name     = (row[COL.COMPANY_NAME] || '').trim();

        // ★ 鉄則: I列が空欄でなければスキップ
        if (!isWritable(currentI)) continue;
        if (!formUrl || formUrl === '-' || formUrl === 'なし') continue;

        targets.push({ rowIdx: i + 1, name, formUrl });
        if (targets.length >= maxCheck) break;
    }

    console.log(`チェック対象: ${targets.length}件（I列空欄 かつ フォームURLあり）\n`);
    if (targets.length === 0) {
        console.log('チェック対象がありません。');
        return;
    }

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        locale: 'ja-JP',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });

    let ngCount = 0, checkedCount = 0, errorCount = 0;
    const ngResults = [];

    for (let idx = 0; idx < targets.length; idx++) {
        const t = targets[idx];
        checkedCount++;
        process.stdout.write(`[${checkedCount}/${targets.length}] ${t.name} ... `);

        const page = await context.newPage();
        const result = await checkFormPage(page, t.formUrl);
        await page.close();

        if (result.error) {
            console.log(`⚠️ エラー: ${result.error.substring(0, 60)}`);
            errorCount++;
        } else if (result.hasNG) {
            ngCount++;
            console.log(`🚫 NG検出: "${result.context.substring(0, 80)}"`);
            ngResults.push({ rowIdx: t.rowIdx, name: t.name, context: result.context });

            if (!isDryRun) {
                const ngNote = `${NG_PREFIX.DYNAMIC}${result.context.substring(0, 200)}`;
                await sheetsClient.spreadsheets.values.update({
                    spreadsheetId: SPREADSHEET_ID,
                    range: `${sheetName}!H${t.rowIdx}:I${t.rowIdx}`,
                    valueInputOption: 'RAW',
                    requestBody: { values: [['✕', ngNote]] },
                });
                console.log(`  → H${t.rowIdx}:I${t.rowIdx} に記入完了`);
            }
        } else {
            console.log('✅ OK');
            // ★ OK判定時に既存フラグをクリアするロジックは存在しない。
            //    I列が空欄の行のみを対象としているため、ここに来る行のI列は必ず空欄。
        }

        if (idx < targets.length - 1) {
            await new Promise(r => setTimeout(r, 2000 + Math.random() * 3000));
        }
    }

    await context.close();
    await browser.close();

    console.log('\n========================================');
    console.log('  チェック完了');
    console.log('========================================');
    console.log(`  チェック件数: ${checkedCount}件`);
    console.log(`  NG検出: ${ngCount}件`);
    console.log(`  エラー: ${errorCount}件`);
    console.log(`  正常: ${checkedCount - ngCount - errorCount}件`);

    if (ngResults.length > 0) {
        console.log('\n[NG一覧]');
        for (const r of ngResults) {
            console.log(`  行${r.rowIdx}: ${r.name}`);
            console.log(`    文言: ${r.context.substring(0, 120)}`);
        }
    }
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
