/**
 * test_real_site.js
 * ─────────────────────────────────────────────────────────────────
 * 実サイトへの DryRun テスト（送信はしない。フィールド認識のみ確認）
 * その後 --send オプションで実際に送信
 * 
 * 対象:
 *   https://jet-produce.com/contact/
 *   https://jet-produce.com/contact2/
 * 
 * 使い方:
 *   node test_real_site.js           # DryRun（認識確認のみ）
 *   node test_real_site.js --send    # 実際に送信
 * ─────────────────────────────────────────────────────────────────
 */

const { chromium } = require('patchright');
const path = require('path');
const fs = require('fs');

const { submitViaPlaywright } = require('./core/playwright_submitter');
const { submitCF7, isCF7Page } = require('./core/cf7_http_submitter');
const { checkSalesNG, checkFormPurpose } = require('./compliance/compliance');

const args = process.argv.slice(2);
const SEND_MODE = args.includes('--send');

// プロファイル読み込み
const profilePath = path.join(__dirname, 'config', 'profiles', 'web-company.json');
const mappingPath = path.join(__dirname, 'config', 'mappings', 'web-company.json');
const baseProfile = JSON.parse(fs.readFileSync(profilePath, 'utf-8'));
const mapping = fs.existsSync(mappingPath) ? JSON.parse(fs.readFileSync(mappingPath, 'utf-8')) : {};

// プロファイル補完
const profile = { ...baseProfile };
if (profile.name) {
    const parts = profile.name.trim().split(/\s+/);
    profile.name_sei = parts[0] || '';
    profile.name_mei = parts.slice(1).join(' ') || '';
}
if (profile.kana) {
    const parts = profile.kana.trim().split(/\s+/);
    profile.kana_sei = parts[0] || '';
    profile.kana_mei = parts.slice(1).join(' ') || '';
}
if (profile.phone) {
    const p = profile.phone.split('-');
    profile.phone_1 = p[0] || '';
    profile.phone_2 = p[1] || '';
    profile.phone_3 = p[2] || '';
}

const SCREENSHOTS_DIR = path.join(__dirname, 'screenshots', 'real_site_test');
const LOGS_DIR = path.join(__dirname, 'logs', 'real_site_test');
[SCREENSHOTS_DIR, LOGS_DIR].forEach(d => { if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true }); });

const TARGETS = [
    { id: 'contact1', url: 'https://jet-produce.com/contact/' },
    { id: 'contact2', url: 'https://jet-produce.com/contact2/' }
];

async function main() {
    console.log('\n' + '═'.repeat(60));
    console.log('🧪 実サイト送信テスト — jet-produce.com');
    console.log('═'.repeat(60));
    console.log(`   モード: ${SEND_MODE ? '🔴 実際に送信 (--send)' : '🟡 DryRun（認識確認のみ）'}`);
    console.log(`   プロファイル: ${profile.name} <${profile.email}>`);
    console.log('');

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();

    const results = [];

    for (const target of TARGETS) {
        console.log(`\n${'─'.repeat(60)}`);
        console.log(`📝 ${target.id}: ${target.url}`);
        console.log('─'.repeat(60));

        let result;

        try {
            // ── CF7チェック ──
            console.log('  🔍 CF7判定中...');
            const isCF7 = await isCF7Page(target.url);

            if (isCF7) {
                console.log('  🚀 CF7検出 → HTTP直接送信ルート');
                result = await submitCF7(target.url, profile, {
                    dryRun: !SEND_MODE,
                    logsDir: LOGS_DIR,
                    rowId: target.id
                });
            } else {
                console.log('  🎭 CF7なし → Playwrightルート');

                // ── 営業NGチェック（Playwrightで） ──
                const page = await context.newPage();
                await page.goto(target.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
                await page.waitForTimeout(2000);

                const pageText = await page.evaluate(() => document.body.textContent || '');
                const ngKeyword = checkSalesNG(pageText);
                if (ngKeyword) {
                    console.log(`  🚫 営業NG検出: 「${ngKeyword}」 → スキップ`);
                    await page.close();
                    result = { success: false, status: '×', reason: `営業お断り: ${ngKeyword}` };
                } else {
                    result = await submitViaPlaywright(page, target.url, profile, mapping, {
                        dryRun: !SEND_MODE,
                        isAllFields: true,
                        screenshotsDir: SCREENSHOTS_DIR,
                        rowId: target.id,
                        logsDir: LOGS_DIR
                    });
                    await page.close();
                }
            }
        } catch (e) {
            result = { success: false, status: '×', reason: `エラー: ${e.message.substring(0, 80)}` };
            console.log(`  ❌ エラー: ${e.message}`);
        }

        const icon = result.status === '〇' ? '✅' : result.status === '△' ? '⚠️' : result.status === '未' ? '❓' : '❌';
        console.log(`\n  ${icon} 結果: ${result.status} ${result.reason || ''}`);
        results.push({ ...target, result });

        // 2件目の前に少し待機
        if (target !== TARGETS[TARGETS.length - 1]) {
            await new Promise(r => setTimeout(r, 2000));
        }
    }

    await browser.close();

    // ── サマリー ──
    console.log('\n\n' + '═'.repeat(60));
    console.log('📊 テスト結果サマリー');
    console.log('═'.repeat(60));
    for (const r of results) {
        const icon = r.result.status === '〇' ? '✅' : r.result.status === '△' ? '⚠️' : '❌';
        console.log(`  ${icon} ${r.id}: ${r.url}`);
        console.log(`     → ${r.result.status} ${r.result.reason || (r.result.status === '〇' ? '成功' : '')}`);
    }
    console.log(`\n  📸 スクリーンショット: ${SCREENSHOTS_DIR}`);
    if (!SEND_MODE) {
        console.log('\n  💡 実際に送信する場合: node test_real_site.js --send');
    }
    console.log('');
}

main().catch(e => { console.error('\n❌ Fatal:', e.message); process.exit(1); });
