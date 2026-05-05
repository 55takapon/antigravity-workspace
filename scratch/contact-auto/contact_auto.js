/**
 * contact_auto.js
 * ─────────────────────────────────────────────────────────────────────────────
 * 企業お問い合わせフォーム自動送信 — メインCLI
 * 
 * アーキテクチャ: ハイブリッドE改
 *   CF7検出 → HTTP直接送信（1-3秒）
 *   それ以外 → Playwright高精度入力（10-30秒）
 *   マッピング不能 → スキップ（手動キュー）
 * 
 * 使い方:
 *   node contact_auto.js \
 *     --sheets <スプレッドシートID> \
 *     --sheet-name <シート名> \
 *     --rows <開始>-<終了> \
 *     [--profile <プロファイル名>] \
 *     [--mapping <マッピング名>] \
 *     [--dry-run] [--all-fields] [--no-cf7]
 * ─────────────────────────────────────────────────────────────────────────────
 */

const { chromium } = require('patchright');
const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');

// Core modules
const { submitCF7, isCF7Page } = require('./core/cf7_http_submitter');
const { submitViaPlaywright } = require('./core/playwright_submitter');
const { checkSalesNG, checkFormPurpose, BlacklistManager, randomDelay, withRetry, SHEET_SKIP_KEYWORDS } = require('./compliance/compliance');

// ── 定数 ──
const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots');
const LOGS_DIR = path.join(__dirname, 'logs', 'unmatched_fields');
const BLACKLIST_FILE = path.join(__dirname, 'config', 'blacklist.json');

// ── プロファイルをパーソナライズ ──
function buildProfile(base, rowData) {
    const p = Object.assign({}, base);
    if (p.message) {
        p.message = p.message
            .replace(/\{\{company\}\}/g, rowData.company || '')
            .replace(/\{\{rep_name\}\}/g, rowData.rep_name || '')
            .replace(/代表取締役\s*ご担当者/g, 'ご担当者')
            .replace(/代表取締役\s*担当者/g, 'ご担当者');
    }
    // ※ p.company は上書きしない（送信者の会社名を維持）
    // 送信先企業名は本文中の {{company}} パーソナライズにのみ使用
    if (p.name) {
        const parts = p.name.trim().split(/\s+/);
        p.name_sei = parts[0] || '';
        p.name_mei = parts.slice(1).join(' ') || '';
    }
    if (p.kana) {
        const parts = p.kana.trim().split(/\s+/);
        p.kana_sei = parts[0] || '';
        p.kana_mei = parts.slice(1).join(' ') || '';
    }
    if (p.phone) {
        const parts = p.phone.split('-');
        p.phone_1 = parts[0] || '';
        p.phone_2 = parts[1] || '';
        p.phone_3 = parts[2] || '';
    }
    if (p.address) {
        const zipMatch = p.address.match(/(\d{3})[-ー](\d{4})/);
        if (zipMatch) {
            p.zipcode = zipMatch[1] + '-' + zipMatch[2];
            p.zipcode_1 = zipMatch[1];
            p.zipcode_2 = zipMatch[2];
            p.address = p.address.replace(/〒?\s*\d{3}[-ー]\d{4}\s*/, '').trim();
        }
    }
    return p;
}

// ── メイン ──
async function main() {
    const args = process.argv.slice(2);

    let spreadsheetId = null, sheetName = null, rowStart = null, rowEnd = null;
    let profileName = 'web-company';
    let mappingName = 'web-company';
    const dryRun = args.includes('--dry-run');
    const isAllFields = args.includes('--all-fields');
    const noCF7 = args.includes('--no-cf7');

    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--sheets' && args[i + 1]) spreadsheetId = args[i + 1];
        if (args[i] === '--sheet-name' && args[i + 1]) sheetName = args[i + 1];
        if (args[i] === '--profile' && args[i + 1]) profileName = args[i + 1];
        if (args[i] === '--mapping' && args[i + 1]) mappingName = args[i + 1];
        if (args[i] === '--rows' && args[i + 1]) {
            const m = args[i + 1].match(/^(\d+)-(\d+)$/);
            if (m) { rowStart = parseInt(m[1]); rowEnd = parseInt(m[2]); }
        }
    }

    if (!spreadsheetId || !sheetName || !rowStart || !rowEnd) {
        console.error('使い方: node contact_auto.js --sheets <ID> --sheet-name <NAME> --rows <START>-<END>');
        console.error('オプション: --profile <名前> --mapping <名前> --dry-run --all-fields --no-cf7');
        process.exit(1);
    }

    // ── 設定読み込み ──
    const profilePath = path.join(__dirname, 'config', 'profiles', `${profileName}.json`);
    const mappingPath = path.join(__dirname, 'config', 'mappings', `${mappingName}.json`);
    if (!fs.existsSync(profilePath)) { console.error(`❌ プロファイル未発見: ${profilePath}`); process.exit(1); }
    if (!fs.existsSync(mappingPath)) { console.error(`❌ マッピング未発見: ${mappingPath}`); process.exit(1); }

    const baseProfile = JSON.parse(fs.readFileSync(profilePath, 'utf-8'));
    const mapping = JSON.parse(fs.readFileSync(mappingPath, 'utf-8'));
    const blacklist = new BlacklistManager(BLACKLIST_FILE);

    // ── ディレクトリ確保 ──
    [SCREENSHOTS_DIR, LOGS_DIR].forEach(d => { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); });

    console.log('\n' + '━'.repeat(60));
    console.log('📨 contact-auto v0.2.0 — ハイブリッドE改');
    console.log(`   シート: ${spreadsheetId}`);
    console.log(`   シート名: ${sheetName}`);
    console.log(`   行: ${rowStart}〜${rowEnd}`);
    console.log(`   プロファイル: ${profileName}`);
    console.log(`   モード: ${dryRun ? '🔍 DryRun' : '📤 送信'} | CF7 HTTP: ${noCF7 ? '無効' : '有効'}`);
    console.log('━'.repeat(60) + '\n');

    // ── Google Sheets読み込み ──
    const sheetsClient = await getGoogleSheetsClient();
    const { headers, rows } = await readSheet(sheetsClient, spreadsheetId, sheetName);

    const colIdx = (name) => headers.indexOf(name);
    const urlCol = colIdx('問い合わせフォームURL');
    const dateCol = colIdx('送信日');
    const statusCol = colIdx('送信○×');
    const reasonCol = colIdx('送信不可理由');
    const companyCol = colIdx('企業名');
    const repCol = colIdx('代表者名');

    if (urlCol < 0) { console.error('❌ 列「問い合わせフォームURL」なし'); process.exit(1); }

    // ── 対象行を絞り込む ──
    const targets = [];
    for (let i = 0; i < rows.length; i++) {
        const sheetRow = i + 2;
        if (sheetRow < rowStart || sheetRow > rowEnd) continue;

        const row = rows[i];
        const formUrl = urlCol >= 0 ? (row[urlCol] || '').trim() : '';
        const dateVal = dateCol >= 0 ? (row[dateCol] || '').trim() : '';
        const reasonVal = reasonCol >= 0 ? (row[reasonCol] || '').trim() : '';
        const companyName = companyCol >= 0 ? (row[companyCol] || '') : '';
        const repName = repCol >= 0 ? (row[repCol] || '') : '';

        if (dateVal) { console.log(`⏭️  行${sheetRow}「${companyName}」送信済み → スキップ`); continue; }
        if (reasonVal) { console.log(`⏭️  行${sheetRow}「${companyName}」送信不可: ${reasonVal} → スキップ`); continue; }
        if (!formUrl || !formUrl.startsWith('http')) { console.log(`⏭️  行${sheetRow}「${companyName}」URLなし → スキップ`); continue; }
        if (blacklist.isBlocked(formUrl)) { console.log(`🚫 行${sheetRow}「${companyName}」ブラックリスト → スキップ`); continue; }

        targets.push({ sheetRow, formUrl, companyName, repName });
    }

    if (targets.length === 0) {
        console.log('✅ 対象行なし');
        return;
    }
    console.log(`📌 対象: ${targets.length}件\n`);

    // ── ブラウザ起動（Playwright用） ──
    let browser = null, context = null;

    // ── 処理開始 ──
    const results = { success: 0, failed: 0, skipped: 0, cf7: 0, playwright: 0 };
    const summary = [];

    for (let idx = 0; idx < targets.length; idx++) {
        const { sheetRow, formUrl, companyName, repName } = targets[idx];

        console.log(`\n${'─'.repeat(60)}`);
        console.log(`📝 [${idx + 1}/${targets.length}] 行${sheetRow}: ${companyName} (${repName || '不明'})`);
        console.log(`🔗 ${formUrl}`);
        console.log('─'.repeat(60));

        const profile = buildProfile(baseProfile, { company: companyName, rep_name: repName });
        let result;

        try {
            result = await withRetry(async () => {
                // ──── Route 1: CF7 HTTP直接送信 ────
                if (!noCF7) {
                    const cf7 = await isCF7Page(formUrl);
                    if (cf7) {
                        console.log('  🚀 CF7検出 → HTTP直接送信ルート');
                        const cf7Result = await submitCF7(formUrl, profile, { dryRun, logsDir: LOGS_DIR, rowId: sheetRow });
                        if (cf7Result.success) {
                            results.cf7++;
                            return cf7Result;
                        }
                        // CF7送信失敗 → Playwrightにフォールバック
                        console.log('  ⚠️ CF7 HTTP失敗 → Playwrightにフォールバック');
                    }
                }

                // ──── Route 2: Playwright ────
                console.log('  🎭 Playwright送信ルート');

                // ブラウザが未起動なら起動
                if (!browser) {
                    console.log('  🌐 Patchrightブラウザ起動...');
                    browser = await chromium.launch({ headless: false });
                    context = await browser.newContext();
                }

                const page = await context.newPage();

                // 営業NGチェック
                await page.goto(formUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
                await page.waitForTimeout(2000);

                const pageText = await page.evaluate(() => document.body.textContent || '');

                // 営業NG検出
                const ngKeyword = checkSalesNG(pageText);
                if (ngKeyword) {
                    await page.close();
                    return { success: false, status: '×', reason: `営業お断り: ${ngKeyword}` };
                }

                // 用途限定フォーム検出
                const purpose = checkFormPurpose(pageText);
                if (purpose.isPurposeLimited) {
                    await page.close();
                    return { success: false, status: '×', reason: `用途限定: ${purpose.keyword}` };
                }

                // Playwright送信
                const pwResult = await submitViaPlaywright(page, formUrl, profile, mapping, {
                    dryRun,
                    isAllFields,
                    screenshotsDir: SCREENSHOTS_DIR,
                    rowId: sheetRow,
                    logsDir: LOGS_DIR
                });
                results.playwright++;
                await page.close();
                return pwResult;

            }, 2); // 最大2回リトライ

        } catch (e) {
            result = { success: false, status: '×', reason: `致命的エラー: ${e.message.substring(0, 50)}` };
        }

        // ── 結果書き戻し ──
        const today = new Date().toLocaleDateString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '/');

        // 全ステータスをシートに記録（DryRun以外）
        if (!dryRun && result.status !== '未') {
            await updateSheetRow(sheetsClient, spreadsheetId, sheetName, sheetRow, {
                statusCol, reasonCol, dateCol,
                status: result.status,
                reason: result.reason || '',
                date: result.status === '〇' ? today : ''  // △は日付なし（手動確認待ち）
            });
        }
        // △/未もシートに理由を書き戻す
        if (!dryRun && (result.status === '△' || result.status === '未')) {
            await updateSheetRow(sheetsClient, spreadsheetId, sheetName, sheetRow, {
                statusCol, reasonCol, dateCol,
                status: result.status,
                reason: result.reason || '',
                date: ''
            });
        }

        // 集計
        if (result.status === '〇') results.success++;
        else if (result.status === '△') { results.success++; results.needCheck = (results.needCheck || 0) + 1; }
        else if (result.status === '×') results.failed++;
        else results.skipped++;

        const icon = result.status === '〇' ? '✅' :
                     result.status === '△' ? '⚠️' :
                     result.status === '×' ? '❌' : '❓';
        const evidenceTag = result.evidence ? ` [Rank ${result.evidence}]` : '';
        summary.push(`${icon} 行${sheetRow}: ${companyName} → ${result.status}${evidenceTag} ${result.reason || ''}`);
        console.log(`\n${icon} 結果: ${result.status}${evidenceTag} ${result.reason || ''}`);

        // ── レート制御（次の送信前に待機） ──
        if (idx < targets.length - 1) {
            await randomDelay(5000, 15000);
        }
    }

    // ── ブラウザ終了 ──
    if (browser) await browser.close();

    // ── サマリー ──
    console.log('\n\n' + '━'.repeat(60));
    console.log('📊 送信完了サマリー');
    console.log('━'.repeat(60));
    console.log(`  ✅ 成功(〇): ${results.success - (results.needCheck || 0)} | ⚠️ 要確認(△): ${results.needCheck || 0} | ❌ 失敗(×): ${results.failed} | ❓ 判定不能(未): ${results.skipped}`);
    console.log(`  🚀 CF7 HTTP: ${results.cf7} | 🎭 Playwright: ${results.playwright}`);
    if (results.needCheck) {
        console.log(`\n  ⚠️ ${results.needCheck}件が手動確認待ちです。スプレッドシートの「△」行を確認してください。`);
    }
    console.log('');
    for (const line of summary) {
        console.log('  ' + line);
    }
    console.log('');

    // -- skill_learner: 日次スキル自動学習 --
    if (!dryRun) {
        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('日次スキル自動学習 (skill_learner) を起動...');
        try {
            const { execSync } = require('child_process');
            const learnerPath = path.join(__dirname, 'skill_learner.js');
            execSync('node ' + JSON.stringify(learnerPath) + ' --min-count 1', {
                cwd: __dirname,
                stdio: 'inherit',
                timeout: 30000
            });
        } catch (e) {
            console.log('  skill_learner 実行エラー（スキップ）: ' + (e.message || '').substring(0, 80));
        }
    }

    // -- save_daily_stats: 日次送信統計を自動保存 --
    if (!dryRun) {
        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('📊 日次送信統計を保存 (save_daily_stats) ...');
        try {
            const { execSync } = require('child_process');
            const statsPath = path.join(__dirname, 'save_daily_stats.js');
            execSync(
                'node ' + JSON.stringify(statsPath) +
                ' --sheets ' + spreadsheetId +
                ' --sheet-name ' + JSON.stringify(sheetName),
                { cwd: __dirname, stdio: 'inherit', timeout: 30000 }
            );
        } catch (e) {
            console.log('  save_daily_stats 実行エラー（スキップ）: ' + (e.message || '').substring(0, 80));
        }
    }
}

// ── Google Sheets API ──
async function getGoogleSheetsClient() {
    const credPath = path.join(__dirname, 'google_credentials.json');
    if (!fs.existsSync(credPath)) { console.error('❌ google_credentials.json なし'); process.exit(1); }
    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({ credentials, scopes: ['https://www.googleapis.com/auth/spreadsheets'] });
    return google.sheets({ version: 'v4', auth });
}

async function readSheet(sheets, spreadsheetId, sheetName) {
    const response = await sheets.spreadsheets.values.get({ spreadsheetId, range: `'${sheetName}'` });
    const values = response.data.values || [];
    if (values.length === 0) return { headers: [], rows: [] };
    console.log(`  📊 シート読み込み: ${values.length - 1}行 / ${values[0].length}列`);
    return { headers: values[0], rows: values.slice(1) };
}

async function updateSheetRow(sheets, spreadsheetId, sheetName, rowNum, { statusCol, reasonCol, dateCol, status, reason, date }) {
    const colLetter = (idx) => {
        let result = '', i = idx + 1;
        while (i > 0) { result = String.fromCharCode(65 + ((i - 1) % 26)) + result; i = Math.floor((i - 1) / 26); }
        return result;
    };
    const updates = [];
    if (statusCol >= 0) updates.push({ range: `'${sheetName}'!${colLetter(statusCol)}${rowNum}`, values: [[status]] });
    if (reasonCol >= 0) updates.push({ range: `'${sheetName}'!${colLetter(reasonCol)}${rowNum}`, values: [[reason]] });
    if (dateCol >= 0) updates.push({ range: `'${sheetName}'!${colLetter(dateCol)}${rowNum}`, values: [[date]] });
    if (updates.length > 0) {
        await sheets.spreadsheets.values.batchUpdate({ spreadsheetId, requestBody: { valueInputOption: 'USER_ENTERED', data: updates } });
    }
}

main().catch(err => { console.error('\n❌ Fatal:', err.message); process.exit(1); });
