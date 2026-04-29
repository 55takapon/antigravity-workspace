/**
 * テスト: 5層フィールド認識 + CF7検出 + コンプライアンス
 */
const { chromium } = require('patchright');
const { analyzeFormFields, resolveFieldMappings } = require('./core/field_recognizer');
const { detectCF7 } = require('./core/cf7_http_submitter');
const { checkSalesNG, checkFormPurpose } = require('./compliance/compliance');
const fs = require('fs');
const axios = require('axios');

const TEST_URL = process.argv[2] || 'https://jet-produce.com/contact/';
const mapping = JSON.parse(fs.readFileSync('./config/mappings/web-company.json', 'utf-8'));

(async () => {
    console.log(`\n🧪 contact-auto 統合テスト`);
    console.log(`🔗 URL: ${TEST_URL}\n`);

    // ── Test 1: CF7検出（HTTP） ──
    console.log('━'.repeat(50));
    console.log('📋 Test 1: CF7 HTTP検出');
    console.log('━'.repeat(50));
    try {
        const { data: html } = await axios.get(TEST_URL, {
            timeout: 10000,
            headers: { 'User-Agent': 'Mozilla/5.0' }
        });
        const { isCF7, formData } = detectCF7(html);
        if (isCF7) {
            console.log(`  ✅ CF7フォーム検出!`);
            console.log(`     ID: ${formData.wpcf7Id}`);
            console.log(`     REST: ${formData.restEndpoint}`);
            console.log(`     フィールド数: ${formData.formFields.length}`);
            formData.formFields.forEach(f => {
                console.log(`       - ${f.name} (${f.type}) ${f.isRequired ? '【必須】' : ''}`);
            });
        } else {
            console.log(`  ⚪ CF7フォームではありません`);
        }
    } catch (e) {
        console.log(`  ❌ HTTP取得エラー: ${e.message}`);
    }

    // ── Test 2: 5層フィールド認識（Playwright） ──
    console.log('\n' + '━'.repeat(50));
    console.log('📋 Test 2: 5層フィールド認識エンジン');
    console.log('━'.repeat(50));

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(TEST_URL, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(2000);

    const rawFields = await analyzeFormFields(page);
    const fields = resolveFieldMappings(rawFields, mapping);

    fields.forEach(f => {
        const icon = f.matchedKey ? '✅' : '❓';
        const src = (f.matchSource || 'none').padEnd(10);
        const key = (f.matchedKey || 'UNMATCH').padEnd(18);
        const req = f.isRequired ? '【必須】' : '';
        console.log(`  ${icon} ${key} [${src}] L1="${(f.layer1 || '').substring(0, 25)}" name="${f.name}" ${req}`);
    });

    const matched = fields.filter(f => f.matchedKey);
    const unmatched = fields.filter(f => !f.matchedKey && f.name);
    console.log(`\n  📊 ${matched.length}マッチ / ${unmatched.length}未マッチ`);

    // ── Test 3: コンプライアンスチェック ──
    console.log('\n' + '━'.repeat(50));
    console.log('📋 Test 3: コンプライアンスチェック');
    console.log('━'.repeat(50));

    const pageText = await page.evaluate(() => document.body.textContent || '');
    const ngResult = checkSalesNG(pageText);
    const purposeResult = checkFormPurpose(pageText);

    console.log(`  営業NG: ${ngResult ? '🚫 検出: ' + ngResult : '✅ なし'}`);
    console.log(`  用途限定: ${purposeResult.isPurposeLimited ? '🚫 ' + purposeResult.keyword : '✅ なし'}`);

    await browser.close();

    console.log('\n✅ 全テスト完了\n');
})().catch(e => {
    console.error('❌ テスト失敗:', e.message);
    process.exit(1);
});
