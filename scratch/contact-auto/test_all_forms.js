/**
 * test_all_forms.js
 * ─────────────────────────────────────────────────────────────────────────────
 * 10バリエーションのテストフォームに対して5層フィールド認識を一括テスト
 * ─────────────────────────────────────────────────────────────────────────────
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('patchright');
const { analyzeFormFields, resolveFieldMappings } = require('./core/field_recognizer');
const { detectCF7 } = require('./core/cf7_http_submitter');
const { checkSalesNG, checkFormPurpose } = require('./compliance/compliance');

const PORT = 8877;

// ── 各フォームの期待マッチ結果 ──
const EXPECTED = {
    form1: { total: 4, expectedKeys: ['name', 'email', 'company', 'message'] },
    form2: { total: 5, expectedKeys: ['name', 'email', 'phone', 'company', 'message'] },
    form3: { total: 5, expectedKeys: ['name', 'email', 'phone', 'company', 'message'] },
    form4: { total: 5, expectedKeys: ['name_sei', 'name_mei', 'kana_sei', 'kana_mei', 'email'] },
    form5: { total: 5, expectedKeys: ['name', 'email', 'phone_1', 'phone_2', 'phone_3'] },
    form6: { total: 6, expectedKeys: ['name', 'email', 'phone', 'company', 'department', 'message'] },
    form7: { total: 4, expectedKeys: ['name', 'company', 'email', 'message'] },
    form8: { total: 4, expectedKeys: ['name', 'email', 'inquiry_type', 'message'] },
    form9: { total: 6, expectedKeys: ['name', 'email', 'company', 'phone', 'subject', 'message'] },
    form10: { ngExpected: true }
};

const mapping = JSON.parse(fs.readFileSync('./config/mappings/web-company.json', 'utf-8'));

(async () => {
    // ── ローカルHTTPサーバー起動 ──
    const html = fs.readFileSync(path.join(__dirname, 'test_forms.html'), 'utf-8');
    const server = http.createServer((req, res) => {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(html);
    });
    await new Promise(r => server.listen(PORT, r));
    console.log(`\n🌐 テストサーバー起動: http://localhost:${PORT}\n`);

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(`http://localhost:${PORT}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    // ── 全体のページテキスト取得（コンプライアンス用） ──
    const fullPageText = await page.evaluate(() => document.body.textContent || '');

    // ── CF7検出テスト ──
    console.log('━'.repeat(60));
    console.log('📋 CF7 HTTP検出テスト');
    console.log('━'.repeat(60));
    const { isCF7, formData } = detectCF7(html);
    if (isCF7 && formData) {
        console.log(`  ✅ CF7フォーム検出: ID=${formData.wpcf7Id}, フィールド=${formData.formFields.length}`);
    } else {
        console.log(`  ❌ CF7フォーム検出失敗`);
    }

    // ── コンプライアンステスト（Form 10） ──
    console.log('\n' + '━'.repeat(60));
    console.log('📋 コンプライアンステスト（Form 10のテキスト）');
    console.log('━'.repeat(60));
    const ngResult = checkSalesNG(fullPageText);
    const purposeResult = checkFormPurpose(fullPageText);
    console.log(`  営業NG: ${ngResult ? '✅ 検出: "' + ngResult + '"' : '❌ 未検出（バグ）'}`);
    console.log(`  用途限定: ${purposeResult.isPurposeLimited ? '✅ 検出: "' + purposeResult.keyword + '"' : '❌ 未検出（バグ）'}`);

    // ── 各フォームのフィールド認識テスト ──
    let totalPassed = 0;
    let totalFailed = 0;

    for (let i = 1; i <= 10; i++) {
        const formId = `form${i}`;
        const expected = EXPECTED[formId];
        if (expected.ngExpected) continue; // Form 10はコンプライアンスで検出済み

        console.log('\n' + '━'.repeat(60));
        console.log(`📋 Form ${i}: フィールド認識テスト`);
        console.log('━'.repeat(60));

        // フォームコンテナ内のフィールドのみ取得
        const rawFields = await page.evaluate((fId) => {
            const container = document.getElementById(fId);
            if (!container) return [];
            const inputs = Array.from(container.querySelectorAll(
                'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select'
            ));

            return inputs.map(el => {
                // ──── Layer 1: 標準認識 ────
                let layer1Text = '';
                if (el.labels && el.labels.length > 0) {
                    layer1Text = el.labels[0].innerText || el.labels[0].textContent || '';
                }
                if (!layer1Text && el.getAttribute('aria-label')) {
                    layer1Text = el.getAttribute('aria-label');
                }
                if (!layer1Text && el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) layer1Text = label.innerText || label.textContent || '';
                }
                if (!layer1Text && el.getAttribute('placeholder')) {
                    layer1Text = el.getAttribute('placeholder');
                }

                // ──── Layer 2: DOM周辺走査 ────
                let layer2Text = '';
                let prev = el.previousElementSibling;
                if (!prev) {
                    const parent = el.parentElement;
                    if (parent) prev = parent.previousElementSibling;
                }
                if (prev) {
                    const t = (prev.innerText || prev.textContent || '').trim();
                    if (t.length > 0 && t.length < 100) layer2Text = t;
                }
                if (!layer2Text) {
                    const dd = el.closest('dd, td');
                    if (dd) {
                        const dt = dd.previousElementSibling;
                        if (dt && (dt.tagName === 'DT' || dt.tagName === 'TH')) {
                            layer2Text = (dt.innerText || dt.textContent || '').trim();
                        }
                    }
                }
                if (!layer2Text) {
                    const container = el.closest('tr, li, dl, .form-group, .form-item, .form-row, .field, .input-group');
                    if (container) {
                        const clone = container.cloneNode(true);
                        clone.querySelectorAll('input, textarea, select').forEach(e => e.remove());
                        const t = (clone.innerText || clone.textContent || '').trim().replace(/\s+/g, ' ');
                        if (t.length > 0 && t.length < 150) layer2Text = t;
                    }
                }

                // ──── Layer 4: 座標ベース ────
                let layer4Text = '';
                try {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        const allTextEls = Array.from(document.querySelectorAll(
                            'label, span, p, th, dt, td, div, h1, h2, h3, h4, h5, h6, strong, em, b'
                        ));
                        let bestMatch = null;
                        let bestDist = Infinity;
                        for (const textEl of allTextEls) {
                            if (textEl.querySelector('input, textarea, select')) continue;
                            const text = (textEl.innerText || textEl.textContent || '').trim();
                            if (text.length === 0 || text.length > 80) continue;
                            const textRect = textEl.getBoundingClientRect();
                            if (textRect.width === 0 || textRect.height === 0) continue;
                            const isAbove = textRect.bottom <= rect.top + 5 && textRect.left < rect.right && textRect.right > rect.left;
                            const isLeft = textRect.right <= rect.left + 5 && textRect.top < rect.bottom && textRect.bottom > rect.top;
                            if (isAbove || isLeft) {
                                const dist = Math.abs(textRect.bottom - rect.top) + Math.abs(textRect.left - rect.left);
                                if (dist < bestDist) { bestDist = dist; bestMatch = text; }
                            }
                        }
                        if (bestMatch) layer4Text = bestMatch;
                    }
                } catch (e) {}

                // ──── 必須判定 ────
                let isRequired = false;
                if (el.required || el.getAttribute('aria-required') === 'true') isRequired = true;

                return {
                    layer1: layer1Text.trim().replace(/\s+/g, ' '),
                    layer2: layer2Text.trim().replace(/\s+/g, ' '),
                    layer4: layer4Text.trim().replace(/\s+/g, ' '),
                    name: el.getAttribute('name') || '',
                    id: el.id || '',
                    autocomplete: el.getAttribute('autocomplete') || '',
                    type: el.type || el.tagName.toLowerCase(),
                    className: el.className || '',
                    tagName: el.tagName.toLowerCase(),
                    xpath: '',
                    isRequired
                };
            });
        }, formId);

        const fields = resolveFieldMappings(rawFields, mapping);
        const matched = fields.filter(f => f.matchedKey);

        // 結果表示
        fields.forEach(f => {
            const icon = f.matchedKey ? '✅' : '❓';
            const src = (f.matchSource || 'none').padEnd(10);
            const key = (f.matchedKey || 'UNMATCH').padEnd(18);
            console.log(`  ${icon} ${key} [${src}] L1="${(f.layer1||'').substring(0,20).padEnd(20)}" L2="${(f.layer2||'').substring(0,20).padEnd(20)}" name="${f.name}"`);
        });

        // 期待値との比較
        const matchedKeys = matched.map(f => f.matchedKey);
        const missing = expected.expectedKeys.filter(k => !matchedKeys.includes(k));
        const extra = matchedKeys.filter(k => !expected.expectedKeys.includes(k));

        if (missing.length === 0) {
            console.log(`  📊 ✅ ${matched.length}/${expected.total} マッチ — 期待値全カバー`);
            totalPassed++;
        } else {
            console.log(`  📊 ❌ ${matched.length}/${expected.total} マッチ — 未カバー: ${missing.join(', ')}`);
            totalFailed++;
        }
        if (extra.length > 0) {
            console.log(`  📊 ℹ️ 追加マッチ: ${extra.join(', ')}`);
        }
    }

    // ── サマリー ──
    console.log('\n\n' + '═'.repeat(60));
    console.log(`🏁 テスト結果: ${totalPassed} PASS / ${totalFailed} FAIL (全${totalPassed + totalFailed}フォーム)`);
    console.log('═'.repeat(60) + '\n');

    await browser.close();
    server.close();
})().catch(e => {
    console.error('❌ テスト失敗:', e.message);
    process.exit(1);
});
