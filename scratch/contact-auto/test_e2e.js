/**
 * test_e2e.js
 * ─────────────────────────────────────────────────────────────────
 * ローカルテストサーバーに対して自動送信を実行するE2Eテスト
 * 
 * 前提: test_server.js が起動済み（node test_server.js）
 * 使い方: node test_e2e.js [--port 3456]
 * ─────────────────────────────────────────────────────────────────
 */

const { chromium } = require('patchright');
const path = require('path');
const fs = require('fs');
const axios = require('axios');

const { submitViaPlaywright } = require('./core/playwright_submitter');
const { submitCF7, isCF7Page } = require('./core/cf7_http_submitter');
const { checkSalesNG, checkFormPurpose } = require('./compliance/compliance');

// ── 設定 ──
const args = process.argv.slice(2);
let PORT = 3456;
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--port' && args[i + 1]) PORT = parseInt(args[i + 1]);
}
const BASE = `http://localhost:${PORT}`;

// テスト用プロファイル
const PROFILE = {
    name: '田中 太郎',
    name_sei: '田中',
    name_mei: '太郎',
    kana: 'タナカ タロウ',
    kana_sei: 'タナカ',
    kana_mei: 'タロウ',
    email: 'tanaka@example.com',
    phone: '090-1234-5678',
    phone_1: '090',
    phone_2: '1234',
    phone_3: '5678',
    company: '株式会社テスト',
    department: '営業部',
    subject: 'テスト送信',
    message: 'これはcontact-autoの自動送信テストです。10パターンのフォームに対する送信精度を検証しています。',
    url: 'https://example.com',
    address: '東京都渋谷区テスト1-2-3',
    zipcode: '150-0001',
    zipcode_1: '150',
    zipcode_2: '0001',
    inquiry_type: '協業・パートナーシップ',
    preferred_contact: 'メール',
    referral: '検索エンジン'
};

// マッピング読み込み
const MAPPING_PATH = path.join(__dirname, 'config', 'mappings', 'web-company.json');
const MAPPING = fs.existsSync(MAPPING_PATH) ? JSON.parse(fs.readFileSync(MAPPING_PATH, 'utf-8')) : {};

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots', 'e2e_test');
const LOGS_DIR = path.join(__dirname, 'logs', 'e2e_test');

// ── テストケース定義 ──
const TEST_CASES = [
    { id: 1,  name: '標準ラベル付き',              route: 'playwright', expectSuccess: true },
    { id: 2,  name: 'placeholderのみ',             route: 'playwright', expectSuccess: true },
    { id: 3,  name: 'テーブルレイアウト',           route: 'playwright', expectSuccess: true },
    { id: 4,  name: '姓名・フリガナ分割',           route: 'playwright', expectSuccess: true },
    { id: 5,  name: '電話・郵便番号分割',           route: 'playwright', expectSuccess: true },
    { id: 6,  name: 'name属性のみ（最難関）',       route: 'playwright', expectSuccess: false },
    { id: 7,  name: 'dl/dt/dd レイアウト',          route: 'playwright', expectSuccess: true },
    { id: 8,  name: 'チェックボックス + select',    route: 'playwright', expectSuccess: true },
    { id: 9,  name: 'CF7ダミー',                   route: 'cf7',        expectSuccess: true },
    { id: 10, name: '営業お断り',                  route: 'compliance', expectSuccess: false },
    // select/radio 強化テスト
    { id: 11, name: 'selectプルダウン複数',         route: 'playwright', expectSuccess: true },
    { id: 12, name: 'ラジオ（種別・連絡方法）',     route: 'playwright', expectSuccess: true },
    { id: 13, name: 'CF7 + select/radio',          route: 'cf7',        expectSuccess: true },
    { id: 14, name: 'ラジオ（labelなし）',          route: 'playwright', expectSuccess: true },
];

async function main() {
    console.log('\n' + '═'.repeat(60));
    console.log('🧪 contact-auto E2E テスト — ローカルサーバー実送信');
    console.log('═'.repeat(60));
    console.log(`   サーバー: ${BASE}`);
    console.log(`   フォーム数: ${TEST_CASES.length}`);
    console.log('');

    // サーバー接続確認
    try {
        await axios.get(BASE, { timeout: 3000 });
    } catch (e) {
        console.error('❌ テストサーバーに接続できません。先に node test_server.js を起動してください。');
        process.exit(1);
    }

    // ディレクトリ確保
    [SCREENSHOTS_DIR, LOGS_DIR].forEach(d => { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); });

    // ブラウザ起動
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();

    const results = [];

    for (const tc of TEST_CASES) {
        const url = `${BASE}/form/${tc.id}`;
        console.log(`\n${'─'.repeat(60)}`);
        console.log(`📝 [${tc.id}/10] Form ${tc.id}: ${tc.name}`);
        console.log(`   ルート: ${tc.route} | 期待: ${tc.expectSuccess ? '成功' : '失敗/スキップ'}`);
        console.log('─'.repeat(60));

        let result;

        try {
            if (tc.route === 'cf7') {
                // ── CF7 HTTPルート ──
                console.log('  🚀 CF7 HTTP直接送信ルート');
                result = await submitCF7(url, PROFILE, {
                    dryRun: false,
                    logsDir: LOGS_DIR,
                    rowId: `e2e_form${tc.id}`
                });

            } else if (tc.route === 'compliance') {
                // ── コンプライアンスチェック（送信しない） ──
                const page = await context.newPage();
                await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 });
                await page.waitForTimeout(1000);
                const pageText = await page.evaluate(() => document.body.textContent || '');

                const ngKeyword = checkSalesNG(pageText);
                if (ngKeyword) {
                    result = { success: false, status: '×', reason: `営業お断り: ${ngKeyword}` };
                    console.log(`  🚫 営業NG検出: 「${ngKeyword}」 → 送信スキップ（正常動作）`);
                } else {
                    const purpose = checkFormPurpose(pageText);
                    if (purpose.isPurposeLimited) {
                        result = { success: false, status: '×', reason: `用途限定: ${purpose.keyword}` };
                        console.log(`  🚫 用途限定検出: 「${purpose.keyword}」 → 送信スキップ（正常動作）`);
                    } else {
                        result = { success: true, status: '△', reason: 'NG未検出（想定外）' };
                    }
                }
                await page.close();

            } else {
                // ── Playwrightルート ──
                const page = await context.newPage();
                result = await submitViaPlaywright(page, url, PROFILE, MAPPING, {
                    dryRun: false,
                    isAllFields: true,
                    screenshotsDir: SCREENSHOTS_DIR,
                    rowId: `e2e_form${tc.id}`,
                    logsDir: LOGS_DIR
                });
                await page.close();
            }
        } catch (e) {
            result = { success: false, status: '×', reason: `エラー: ${e.message.substring(0, 60)}` };
        }

        // 期待値との照合
        const actualSuccess = result.status === '〇';
        const testPassed = tc.expectSuccess ? actualSuccess : !actualSuccess;

        const icon = testPassed ? '✅' : '❌';
        const detail = result.reason || (result.status === '〇' ? '送信成功' : '');

        results.push({
            formId: tc.id,
            name: tc.name,
            route: tc.route,
            status: result.status,
            testPassed,
            detail
        });

        console.log(`\n  ${icon} Form ${tc.id}: ${result.status} ${detail}`);
        console.log(`     テスト判定: ${testPassed ? 'PASS' : 'FAIL'}（期待: ${tc.expectSuccess ? '成功' : '失敗/スキップ'}）`);

        // フォーム間の待機
        await new Promise(r => setTimeout(r, 1000));
    }

    await browser.close();

    // ── サマリー ──
    console.log('\n\n' + '═'.repeat(60));
    console.log('📊 E2E テスト結果サマリー');
    console.log('═'.repeat(60));

    const passed = results.filter(r => r.testPassed).length;
    const failed = results.filter(r => !r.testPassed).length;

    console.log('');
    console.log(`  ${'Form'.padEnd(6)} ${'名前'.padEnd(24)} ${'ルート'.padEnd(12)} ${'結果'.padEnd(4)} ${'テスト'.padEnd(6)} 詳細`);
    console.log('  ' + '─'.repeat(80));

    for (const r of results) {
        const icon = r.testPassed ? '✅' : '❌';
        console.log(`  ${String(r.formId).padEnd(6)} ${r.name.padEnd(22)} ${r.route.padEnd(12)} ${r.status.padEnd(4)} ${icon}      ${r.detail}`);
    }

    console.log('');
    console.log(`  合計: ${passed} PASS / ${failed} FAIL`);

    // サーバーの結果を取得
    try {
        const serverResults = await axios.get(`${BASE}/results`);
        const data = serverResults.data;
        console.log(`\n  📧 サーバー受信数: ${data.totalSubmissions}件`);
        console.log(`\n  📬 メール確認方法:`);
        console.log(`     1. https://ethereal.email/login にアクセス`);
        console.log(`     2. User: ${data.etherealLogin.user}`);
        console.log(`     3. Pass: ${data.etherealLogin.pass}`);
        console.log(`     4. 「Messages」タブで送信メール一覧を確認`);
    } catch (e) {
        console.log(`\n  ⚠️ サーバー結果の取得に失敗: ${e.message}`);
    }

    console.log('\n  📸 スクリーンショット: ' + SCREENSHOTS_DIR);
    console.log('  📋 ログ: ' + LOGS_DIR);
    console.log('');
}

main().catch(e => { console.error('\n❌ Fatal:', e.message); process.exit(1); });
