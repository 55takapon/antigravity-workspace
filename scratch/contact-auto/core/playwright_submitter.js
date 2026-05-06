/**
 * playwright_submitter.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Patchright（Playwright互換・ステルス版）による高精度フォーム入力＋自動送信
 * 
 * form-automationのprocessForm()をベースに以下を強化:
 *   - 5層フィールド認識エンジン統合
 *   - リトライ機構（指数バックオフ）
 *   - 送信結果検証パターン拡充
 *   - カタカナ⇔ひらがな変換
 *   - select/radio の知的選択
 * ─────────────────────────────────────────────────────────────────────────────
 */

const path = require('path');
const { analyzeFormFields, resolveFieldMappings, logUnmatchedFields } = require('./field_recognizer');

// ── カタカナ → ひらがな変換 ──
function katakanaToHiragana(src) {
    if (!src) return '';
    return src.replace(/[\u30a1-\u30f6]/g, m => String.fromCharCode(m.charCodeAt(0) - 0x60));
}

// ── select/radio のインテリジェント選択候補（500+URL調査レポート準拠） ──
// 上から順に優先してマッチ。「採用」「応募」を含む選択肢は自動除外
const SELECT_PREFERENCES = {
    inquiry_type: [
        // 協業・提案系（最優先）
        '協業', '業務提携', '業務提案', 'アライアンス', 'パートナー', 'パートナーシップ',
        'ご提案・協業', '外部パートナー', 'ベンダー',
        // Web・制作系（協業に次いで優先）
        'ウェブ', 'Web', 'WEB', 'webサイト', 'Webサイト', 'WEBサイト',
        'ホームページ', 'ホームページ制作', 'Web制作', 'WEB制作',
        'WEBサイト制作に関して', 'WEBサイト制作',
        // 依頼・相談系
        'お仕事のご依頼', '制作のご相談', '制作のご依頼', 'サービスについて',
        '製品・サービスに関するお問い合わせ', '導入のご相談', '資料請求',
        // 見積もり・その他
        'お見積りのご依頼', '見積もり', 'サービス紹介', 'セールス',
        // それ以外・その他（最終フォールバック）
        'それ以外のお問い合わせ', 'それ以外',
        'その他のお問い合わせ', 'その他'
    ],
    preferred_contact: [
        'メール', 'メールでのご連絡希望', 'メールで連絡を希望',
        'メールでの応答', 'e-mail', 'email', 'mail',
        'どちらでも可', 'どちらでも', 'どちらでもかまいません'
    ],
    preferred_time: [
        'いつでも', '不問', '指定なし', '希望なし',
        '午前（10時〜12時）', '午後（13時〜17時）', '午前', '午後'
    ],
    budget: [
        '50万円未満', '〜50万円', '未定', '検討中',
        '50万円〜100万円', '30万円未満', '不明'
    ],
    deadline: [
        '未定', '検討中', 'すぐ〜1ヶ月後', '2〜3ヶ月後',
        '3〜6ヶ月後', '急ぎ'
    ],
    referral: [
        '検索エンジン', 'インターネット検索', 'Google検索',
        'インターネット検索結果', 'Web検索', 'その他'
    ],
    industry: [
        'IT・Web', 'Web制作', '情報通信', 'サービス業',
        '広告・マーケティング', 'その他'
    ]
};

// ── 同意系チェックボックスのトリガーワード ──
const CONSENT_TRIGGERS = [
    '同意', '規約', '確認', '個人情報', 'プライバシー',
    '契約', '合意', '承諾', '了承', '同意する',
    'プライバシーポリシー', '個人情報保護', '入力内容を確認'
];

/**
 * Playwrightでフォームに入力＋送信
 * @param {import('patchright').Page} page
 * @param {string} url
 * @param {object} profile - パーソナライズ済みプロファイル
 * @param {object} mapping - マッピングJSON
 * @param {object} options
 * @returns {Promise<{success: boolean, status: string, reason: string}>}
 */
async function submitViaPlaywright(page, url, profile, mapping, options = {}) {
    const { dryRun = false, isAllFields = false, screenshotsDir = null, rowId = 'unknown', logsDir = null } = options;

    try {
        console.log(`  ⏳ ページを開いています...`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);

        // ──── Cookie同意バナー等のポップアップを自動クローズ ────
        try {
            const cookieBtn = page.locator('button:has-text("同意"), button:has-text("Accept"), button:has-text("許可"), a:has-text("同意")').first();
            if (await cookieBtn.isVisible({ timeout: 1000 }).catch(()=>false)) {
                await cookieBtn.evaluate(b => b.click()).catch(() => {});
                console.log('  🍪 Cookie同意バナーを自動クローズしました');
            }
        } catch (e) {}

        // ──── 5層フィールド認識 ────
        console.log('  🔍 5層フィールド認識エンジン起動...');
        let rawFields = await analyzeFormFields(page);
        let fields = resolveFieldMappings(rawFields, mapping);
        let activePage = page; // iframe対応: 入力対象のpageオブジェクト

        // フィールドが0件 → iframeのフォームを探す（HubSpot等の埋め込みフォーム対応）
        const mainFields = fields.filter(f => f.name && !['hidden','submit','button','reset','image'].includes(f.type));
        if (mainFields.length === 0) {
            console.log('  🔍 メインページにフィールドなし → iframeフォームを探索...');
            for (const frame of page.frames().slice(1)) {
                try {
                    const frameInputs = await frame.evaluate(() =>
                        document.querySelectorAll('input[name], textarea[name], select[name]').length
                    );
                    if (frameInputs > 0) {
                        console.log('  🖼️  iframeフォーム発見 (' + frameInputs + 'フィールド)');
                        rawFields = await analyzeFormFields(frame);
                        fields = resolveFieldMappings(rawFields, mapping);
                        activePage = frame;
                        break;
                    }
                } catch (e) { /* cross-origin iframe はスキップ */ }
            }
        }


        // 認識結果のサマリー
        const matched = fields.filter(f => f.matchedKey);
        const unmatched = fields.filter(f => !f.matchedKey && f.name && !['submit', 'button', 'image', 'hidden', 'reset'].includes(f.type));
        console.log(`  📊 認識結果: ${matched.length}マッチ / ${unmatched.length}未マッチ`);

        // 未マッチフィールドをログ保存
        if (unmatched.length > 0 && logsDir) {
            const logFile = logUnmatchedFields(url, unmatched, logsDir);
            console.log(`  📝 未マッチパターン保存: ${logFile}`);
        }

        // ──── フィールド入力 ────
        let filledCount = 0;
        for (const field of fields) {
            const textToMatch = `${field.layer1} ${field.layer2} ${field.layer4} ${field.name}`.toLowerCase();

            // 同意系チェックボックス/ラジオ
            if (field.type === 'checkbox' || field.type === 'radio') {
                if (CONSENT_TRIGGERS.some(kw => textToMatch.includes(kw)) || field.name?.includes('acceptance')) {
                    try {
                        const sel = field.name ? `[name="${field.name}"]` : `xpath=${field.xpath}`;
                        try { await page.locator(sel).first().check({ timeout: 1000, force: true }); }
                        catch (e) { await page.locator(sel).first().evaluate(el => el.click()).catch(() => {}); }
                        console.log(`  ☑️  同意チェック: ${field.layer1 || field.name}`);
                    } catch (e) {
                        console.log(`     ⚠️ 同意チェック失敗: ${field.layer1 || field.name}`);
                    }
                    continue;
                }
            }

            if (!field.matchedKey || profile[field.matchedKey] === undefined) {
                if (field.name && !['submit', 'button', 'image', 'hidden', 'reset', 'checkbox', 'radio'].includes(field.type)) {
                    if (field.isRequired) {
                        console.log(`  ❓ 未マッチ（必須）: name="${field.name}" | L1="${field.layer1}" | L2="${field.layer2}" | L4="${field.layer4}"`);
                    }
                }
                continue;
            }

            // 必須/任意の制御
            // 選択系（inquiry_typeなど）や基本情報（name, email等）は必須(isRequired)でなくても常に入力する。
            const alwaysFill = [
                'name', 'name_sei', 'name_mei', 'kana', 'kana_sei', 'kana_mei',
                'company', 'department', 'email', 'phone', 'phone_1', 'phone_2', 'phone_3',
                'address', 'zipcode', 'zipcode_1', 'zipcode_2', 'prefecture', 'url',
                'message', 'subject', 'inquiry_type', 
                'preferred_contact', 'preferred_time', 
                'budget', 'referral', 'industry'
            ];
            if (!isAllFields && !field.isRequired && !alwaysFill.includes(field.matchedKey)) {
                continue;
            }

            let fillVal = String(profile[field.matchedKey]);

            // ひらがな指定の場合は変換
            const lbl = (field.layer1 || '').toLowerCase();
            const nm = (field.name || '').toLowerCase();
            if (lbl.includes('ひらがな') || lbl.includes('ふりがな') || nm.includes('hiragana')) {
                fillVal = katakanaToHiragana(fillVal);
            }

            const src = field.matchSource === 'mapping' ? 'MAP' : field.matchSource === 'semantic' ? 'SEM' : 'AUTO';
            console.log(`  ✏️  [${src}] "${field.layer1 || field.name}" → ${field.matchedKey} = "${fillVal.substring(0, 40)}"`);

            try {
                const sel = field.name ? `[name="${field.name}"]` : `xpath=${field.xpath}`;

                if (field.tagName === 'select') {
                    const locator = page.locator(sel).first();
                    await fillSelect(locator, profile, field.matchedKey);
                } else if (field.type === 'radio') {
                    await fillRadio(page, field, profile, field.matchedKey);
                } else if (field.type === 'checkbox') {
                    const locator = page.locator(sel).first();
                    if (['inquiry_type', 'preferred_contact', 'budget', 'referral', 'industry'].includes(field.matchedKey)) {
                        try { await locator.check({ timeout: 1000, force: true }); }
                        catch (e) { await locator.evaluate(el => el.click()).catch(() => {}); }
                        filledCount++;
                        console.log(`  ☑️  チェックボックス選択: ${field.layer1 || field.name}`);
                    }
                } else {
                    // 同一nameが複数ある場合（確認用email等）は全件入力
                    const allLocators = page.locator(sel);
                    const cnt = await allLocators.count();
                    for (let i = 0; i < cnt; i++) {
                        await allLocators.nth(i).fill(fillVal, { timeout: 3000 });
                    }
                    filledCount++;
                }
            } catch (e) {
                console.log(`     ⚠️  入力失敗: ${e.message.substring(0, 60)}`);
            }
        }

        console.log(`  📝 入力完了: ${filledCount}フィールド`);

        // スクリーンショット（送信前）
        if (screenshotsDir) {
            await page.evaluate(() => window.scrollTo(0, 0));
            const shotPath = path.join(screenshotsDir, `filled_row_${rowId}.png`);
            await page.screenshot({ path: shotPath, fullPage: true });
            console.log(`  📸 スクリーンショット: ${shotPath}`);
        }

        // ──── CF7正規タグ注入（Playwrightルート用） ────
        // CF7フォームの場合、フィールド名がカスタム名（field-a等）でも
        // メールテンプレートの [your-name] [your-email] [your-subject] [your-message] が
        // リテラル表示されないよう、hidden inputとして正規タグを注入する
        const isCF7Form = await page.locator('form.wpcf7-form, .wpcf7 form').count() > 0;
        if (isCF7Form) {
            const cf7Tags = {
                'your-name':    profile.name || '',
                'your-email':   profile.email || '',
                'your-subject': '',
                'your-message': profile.message || ''
            };
            const injected = await page.evaluate((tags) => {
                const form = document.querySelector('form.wpcf7-form') ||
                             document.querySelector('.wpcf7 form');
                if (!form) return [];
                const added = [];
                for (const [name, value] of Object.entries(tags)) {
                    if (value === null || value === undefined) continue;
                    // 既に同名フィールドがあればスキップ
                    if (form.querySelector(`[name="${name}"]`)) continue;
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = name;
                    input.value = value;
                    form.appendChild(input);
                    added.push(name);
                }
                return added;
            }, cf7Tags);
            if (injected.length > 0) {
                console.log(`  🛡️  [CF7正規タグ注入] ${injected.join(', ')} をhidden追加`);
            }
        }

        if (dryRun) {
            return { success: true, status: '未', reason: 'DryRun' };
        }

        // ──── 送信 ────
        return await submitForm(activePage, page, screenshotsDir, rowId, profile);

    } catch (e) {
        console.log(`  ❌ エラー: ${e.message}\n${e.stack}`);
        return { success: false, status: '×', reason: `エラー: ${e.message.substring(0, 50)}` };
    }
}

/**
 * フォームの送信ボタンをクリックして結果を検証
 * 
 * エビデンスランク:
 *   S: CF7 REST API mail_sent（cf7_http_submitterが担当）
 *   A: 成功テキスト検出 or URL遷移 → 〇
 *   B: 確認ページ通過+ページ変化 → △（要確認）
 *   C: エラーなし+ページ変化あり → △（要確認）
 *   D: 判定不能 → 未（手動確認キュー）
 */
async function submitForm(activePage, mainPage, screenshotsDir, rowId, profile) {
    console.log('  📤 送信ボタンを検索...');

    // フォーム内のボタンを優先して検索（検索・ハンバーガー等の誤認識を防ぐ）
    const submitBtn = await (async () => {
        // 1st: フォーム内の送信系ボタンを優先
        const EXCLUDE_TEXTS = /^(検索|search|menu|メニュー|閉じる|close|back|戻る|キャンセル|cancel|×)$/i;
        const formBtns = await activePage.evaluate(() => {
            const form = document.querySelector('form');
            if (!form) return null;
            const candidates = form.querySelectorAll(
                'input[type="submit"], button[type="submit"], button:not([type]), button[type="button"]'
            );
            return [...candidates].map((el, idx) => ({
                idx,
                text: el.textContent.trim(),
                value: el.value || '',
                cls: el.className || ''
            }));
        });

        if (formBtns) {
            for (const btn of formBtns) {
                const t = btn.text || btn.value || '';
                if (!EXCLUDE_TEXTS.test(t)) {
                    const loc = activePage.locator('form').locator(
                        'input[type="submit"], button[type="submit"], button:not([type])'
                    ).nth(btn.idx);
                    if (await loc.isVisible({ timeout: 1000 }).catch(() => false)) {
                        console.log('  🎯 フォーム内送信ボタン確定: ' + (t||'（ラベルなし）'));
                        return loc;
                    }
                }
            }
        }

        // 2nd: フォールバック - 幅広いセレクタで検索（送信ぽいテキストのみ）
        const fallback = activePage.locator(
            'input[type="submit"], input[value*="送信"], input[value*="確認"], input[value*="SEND"], input[value*="Send"], ' +
            'input[type="image"], img[alt*="送信"], ' +
            'button:has-text("送信"), button:has-text("確認する"), button:has-text("SEND"), button:has-text("Send"), ' +
            'div.btn_submit, div.submit-btn, [class*="submit_btn"], [class*="btn-submit"], ' +
            'a:has-text("送信する"), a:has-text("確認"), div.js-send'
        ).first();
        return fallback;
    })();

    if (!await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        return { success: false, status: '×', reason: '送信ボタンが見つかりません' };
    }

    // 送信前のURL・ページテキストを記録（ページ変化の検出用）
    const urlBefore = mainPage.url();
    const textBefore = await activePage.evaluate(() => document.body.textContent || '');

    try {
        await submitBtn.click({ timeout: 5000 });
    } catch (e) {
        console.log('  ⚠️ ボタンが隠れているため強制クリックを実行します');
        await submitBtn.evaluate(b => b.click()).catch(() => {});
    }
    console.log('  📤 送信ボタンクリック');

    // ──── Rank A: CF7 AJAX応答 ────
    try {
        await activePage.waitForFunction(() => {
            const el = document.querySelector('.wpcf7-response-output');
            return el && el.textContent.trim().length > 0 && el.offsetParent !== null;
        }, { timeout: 10000 });

        const responseText = await activePage.locator('.wpcf7-response-output').textContent({ timeout: 3000 });
        console.log(`  📩 CF7応答: ${responseText}`);
        if (/ありがとう|送信されました|sent|thank/i.test(responseText)) {
            await saveResultScreenshot(mainPage, screenshotsDir, rowId);
            console.log(`  ✅ [Rank A] CF7 AJAX成功応答`);
            return { success: true, status: '〇', reason: 'CF7 AJAX成功', evidence: 'A' };
        }
        // CF7がエラーを返した場合
        if (/エラー|error|入力/i.test(responseText)) {
            await saveResultScreenshot(mainPage, screenshotsDir, rowId);
            return { success: false, status: '×', reason: `CF7エラー: ${responseText.substring(0, 50)}` };
        }
    } catch {
        console.log(`  ℹ️  CF7応答なし（通常フォームと判定）`);
    }

    // ──── 2段階確認ページの処理 ────
    let wentThroughConfirm = false;
    await mainPage.waitForTimeout(3000);
    const finalSubmit = activePage.locator(
        'button:has-text("送信"), input[value*="送信"], a:has-text("送信"), ' +
        'button:has-text("SEND"), input[value*="SEND"], a:has-text("SEND"), ' +
        'button:has-text("Send"), input[value*="Send"], a:has-text("Send"), ' +
        'button[type="submit"]:not(:has-text("修正")):not(:has-text("戻")), ' +
        'input[type="submit"]:not([value*="修正"]):not([value*="戻"])'
    ).first();

    if (await finalSubmit.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('  📤 確認ページの送信ボタンをクリック');
        try {
            await finalSubmit.click({ timeout: 5000 });
        } catch (e) {
            console.log('  ⚠️ ボタンが隠れているため強制クリックを実行します');
            await finalSubmit.evaluate(b => b.click()).catch(() => {});
        }
        await mainPage.waitForTimeout(4000);
        wentThroughConfirm = true;
    }

    // ──── 送信結果を検証（バリデーションエラーリカバリーループ付き） ────
    let result = await verifySubmission(activePage, mainPage, urlBefore, textBefore, wentThroughConfirm, profile);

    // verifySubmission が null を返した = バリデーションエラーリカバリー後 → 再送信
    if (result === null) {
        console.log('  🔄 エラーリカバリー後に再送信します...');
        await mainPage.waitForTimeout(1000);
        const retryBtn = await (async () => {
            const formBtns = await activePage.evaluate(() => {
                const form = document.querySelector('form');
                if (!form) return null;
                return [...form.querySelectorAll('input[type="submit"], button[type="submit"], button:not([type])')].map((el, idx) => ({ idx, text: el.textContent.trim(), value: el.value || '' }));
            });
            if (formBtns) {
                const EXCLUDE = /^(検索|search|menu|メニュー|閉じる|close|back|戻る|キャンセル|cancel|×)$/i;
                for (const btn of formBtns) {
                    if (!EXCLUDE.test(btn.text || btn.value || '')) {
                        return activePage.locator('form').locator('input[type="submit"], button[type="submit"], button:not([type])').nth(btn.idx);
                    }
                }
            }
            return activePage.locator('input[type="submit"], button[type="submit"]').first();
        })();

        if (await retryBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
            try { await retryBtn.click({ timeout: 5000 }); }
            catch (e) { await retryBtn.evaluate(b => b.click()).catch(() => {}); }
            await mainPage.waitForTimeout(4000);
            result = await verifySubmission(activePage, mainPage, urlBefore, textBefore, false, profile);
            if (result === null) result = { success: false, status: '×', reason: 'リカバリー後も送信失敗', evidence: 'error' };
        } else {
            result = { success: false, status: '×', reason: 'リカバリー後の再送信ボタンなし', evidence: 'error' };
        }
    }

    // 送信後スクリーンショット（エビデンス）
    await saveResultScreenshot(mainPage, screenshotsDir, rowId);

    return result;
}

/**
 * 送信後スクリーンショットを保存（エビデンス用）
 */
async function saveResultScreenshot(mainPage, screenshotsDir, rowId) {
    if (!screenshotsDir) return;
    try {
        await mainPage.evaluate(() => window.scrollTo(0, 0));
        await mainPage.waitForTimeout(300);
        const shotPath = path.join(screenshotsDir, `result_row_${rowId}.png`);
        await mainPage.screenshot({ path: shotPath, fullPage: true });
        console.log(`  📸 エビデンス保存: ${shotPath}`);
    } catch (e) {
        console.log(`  ⚠️ スクリーンショット失敗: ${e.message.substring(0, 40)}`);
    }
}

/**
 * 送信結果を検証 — 3段階判定（〇 / △ / 未）
 * 
 * 〇: 明確な成功エビデンスあり（Rank A）
 * △: 成功の可能性が高いが確証なし（Rank B/C）→ 手動確認を推奨
 * 未: 判定不能（Rank D）→ 手動確認必須
 * ×: 明確なエラー検出
 */
async function verifySubmission(activePage, mainPage, urlBefore, textBefore, wentThroughConfirm, profile) {
    const pageText = await activePage.evaluate(() => document.body.textContent || '');
    const currentUrl = mainPage.url();

    // ──── エラー検出（最優先） ────
    const errorPatterns = [
        { text: 'エラーが発生', weight: 'hard' },
        { text: '入力に誤りがあります', weight: 'hard' },
        { text: '必須項目が入力されていません', weight: 'hard' },
        { text: '必須項目', weight: 'soft' },
        { text: '入力してください', weight: 'soft' },
        { text: '正しく入力', weight: 'soft' },
        { text: 'エラー', weight: 'soft' },
        { text: 'error', weight: 'soft' }
    ];

    for (const { text, weight } of errorPatterns) {
        if (pageText.includes(text)) {
            // 「エラー」が送信前にもあった場合は除外（フォームページ自体に含まれるケース）
            if (weight === 'soft' && textBefore.includes(text)) continue;
            console.log(`  ❌ エラー検出: "${text}" → エラーフィールドを特定して再入力を試みます`);

            // ── バリデーションエラーリカバリー: エラー箇所を特定して再入力 ──
            const recovered = await (async () => {
                try {
                    // エラー表示のある入力フィールドを探す
                    const errorFields = await activePage.evaluate(() => {
                        const selectors = [
                            '.error input, .error textarea, .error select',
                            '.is-error input, .is-error textarea, .is-error select',
                            'input:invalid, textarea:invalid, select:invalid',
                            '[aria-invalid="true"]',
                            '.field-error input, .field-error textarea',
                            '.has-error input, .has-error textarea',
                        ];
                        const found = [];
                        for (const sel of selectors) {
                            document.querySelectorAll(sel).forEach(el => {
                                if (!found.find(f => f.name === el.name)) {
                                    found.push({ name: el.name, type: el.type, tagName: el.tagName.toLowerCase() });
                                }
                            });
                        }
                        // Snow Monkey Forms / フレームワーク独自エラー: エラーメッセージ要素の近くの入力を探す
                        if (found.length === 0) {
                            const errContainers = document.querySelectorAll('.smf-error-messages, [class*="error-message"], [class*="errorMessage"], [class*="error_message"]');
                            errContainers.forEach(ec => {
                                const parent = ec.closest('[class*="smf-"], [class*="field"], [class*="form-group"], .form-item, .input-wrap');
                                if (parent) {
                                    const inp = parent.querySelector('input, textarea, select');
                                    if (inp && !found.find(f => f.name === inp.name)) {
                                        found.push({ name: inp.name, type: inp.type, tagName: inp.tagName.toLowerCase() });
                                    }
                                }
                            });
                        }
                        return found;
                    });

                    if (errorFields.length > 0) {
                        console.log(`  🔧 エラーフィールド ${errorFields.length}件 を再入力します`);
                        for (const ef of errorFields) {
                            // field_recognizer のマッピングを使って値を決定
                            const name = (ef.name || '').toLowerCase();
                            let fillValue = null;
                            if (/name|氏名|fullname/.test(name)) {
                                if (name.includes('sei') || name.includes('last') || name === 'lastname') fillValue = profile.name_sei || profile.name;
                                else if (name.includes('mei') || name.includes('first') || name === 'firstname') fillValue = profile.name_mei || profile.name;
                                else fillValue = profile.name;
                            }
                            else if (/company|会社/.test(name)) fillValue = profile.company;
                            else if (/email|mail/.test(name)) fillValue = profile.email;
                            else if (/tel|phone|電話|携帯/.test(name)) fillValue = profile.phone;
                            else if (/message|本文|内容|備考/.test(name)) fillValue = profile.message;
                            else if (/zip|postal|郵便/.test(name)) fillValue = profile.zipcode || '';
                            else if (/address|住所/.test(name)) fillValue = profile.address || '';
                            
                            if (fillValue) {
                                const sel = ef.name ? `[name="${ef.name}"]` : null;
                                if (sel) {
                                    try {
                                        await activePage.locator(sel).first().fill(String(fillValue), { timeout: 2000 });
                                        console.log(`  ✏️  再入力: ${ef.name} = ${String(fillValue).substring(0, 30)}`);
                                    } catch (e) { /* skip */ }
                                }
                            }
                        }
                        return true;
                    }
                } catch (e) { /* リカバリー失敗はスルー */ }
                return false;
            })();

            if (!recovered) {
                return { success: false, status: '×', reason: `バリデーションエラー: ${text}`, evidence: 'error' };
            }
            // 回復後に再送信
            return null; // 呼び出し元でnullを受け取ったら再送信ループへ
        }
    }

    // ──── Rank A: 成功テキスト検出 ────
    const successPatterns = [
        'ありがとうございます', '送信されました', '送信完了', '送信いたしました',
        'お問い合わせを受け付けました', '受け付けました', '確認メールをお送り',
        'thank you', 'successfully sent', 'お問合せを受け付け',
        '完了しました', '送信が完了', 'お申し込みありがとうございます',
        'フォームが送信されました', 'お問い合わせいただきありがとうございます',
        'メールを送信しました', '受付が完了', '受付完了'
    ];

    for (const pattern of successPatterns) {
        if (pageText.includes(pattern) && !textBefore.includes(pattern)) {
            console.log(`  ✅ [Rank A] 成功テキスト検出: "${pattern}"`);
            return { success: true, status: '〇', reason: '', evidence: 'A' };
        }
    }

    // ──── Rank A: URL遷移で完了判定 ────
    const successUrlPatterns = [
        /\/thanks/i, /\/thank-you/i, /\/complete/i, /\/done/i,
        /\/success/i, /\/finish/i, /\/sent/i
    ];

    if (currentUrl !== urlBefore) {
        for (const pattern of successUrlPatterns) {
            if (pattern.test(currentUrl)) {
                console.log(`  ✅ [Rank A] 成功URL遷移: ${currentUrl}`);
                return { success: true, status: '〇', reason: '', evidence: 'A' };
            }
        }
    }

    // ──── Rank B: 確認ページ通過+URL変化 ────
    if (wentThroughConfirm && currentUrl !== urlBefore) {
        console.log(`  ⚠️ [Rank B] 確認ページ通過+URL変化 → 要手動確認`);
        return { success: true, status: '△', reason: '確認ページ通過（要手動確認）', evidence: 'B' };
    }

    // ──── Rank C: ページ変化あり（テキスト大幅変更 or URL変化） ────
    const textChanged = Math.abs(pageText.length - textBefore.length) > 100 ||
                         (currentUrl !== urlBefore);
    if (textChanged) {
        console.log(`  ⚠️ [Rank C] ページ変化検出 → 要手動確認`);
        return { success: true, status: '△', reason: 'ページ変化あり（要手動確認）', evidence: 'C' };
    }

    // ──── Rank D: 判定不能 → 「未」として記録 ────
    console.log(`  ❓ [Rank D] 判定不能 → 手動確認必須`);
    return { success: false, status: '未', reason: '送信結果判定不能（要手動確認）', evidence: 'D' };
}

/**
 * selectフィールドの知的選択
 */
async function fillSelect(locator, profile, matchedKey) {
    let selected = false;
    if (profile[matchedKey]) {
        try {
            await locator.selectOption({ label: profile[matchedKey] }, { timeout: 1000 });
            selected = true;
        } catch { }
    }
    if (!selected) {
        const optionsText = await locator.evaluate(el => Array.from(el.options).map(o => o.text));
        const prefs = SELECT_PREFERENCES[matchedKey] || SELECT_PREFERENCES.inquiry_type;
        for (const pref of prefs) {
            const match = optionsText.find(opt => opt.includes(pref));
            if (match) {
                if (match.includes('営業') && matchedKey !== 'preferred_contact') break;
                await locator.selectOption({ label: match }, { timeout: 1000 });
                console.log(`     → 選択: ${match}`);
                break;
            }
        }
    }
}

/**
 * radioフィールドの知的選択（強化版）
 * - name属性からmatchedKeyを自動推定するフォールバック付き
 */
async function fillRadio(page, field, profile, matchedKey) {
    const radioGroup = page.locator(`input[type="radio"][name="${field.name}"]`);
    const count = await radioGroup.count();
    let clicked = false;

    // matchedKeyが不明なら、フィールドのname/layerから推定
    let resolvedKey = matchedKey;
    if (!resolvedKey || !SELECT_PREFERENCES[resolvedKey]) {
        const nameStr = (field.name || '').toLowerCase();
        const labelStr = `${field.layer1 || ''} ${field.layer2 || ''} ${field.layer4 || ''}`.toLowerCase();
        const combined = nameStr + ' ' + labelStr;
        if (/contact.?way|contact.?method|renraku|reply.?method|renkaku/.test(combined)) {
            resolvedKey = 'preferred_contact';
        } else if (/time|jikan|jikantai/.test(combined)) {
            resolvedKey = 'preferred_time';
        } else if (/referral|kikkake|source|channel/.test(combined)) {
            resolvedKey = 'referral';
        } else if (/budget|yosan/.test(combined)) {
            resolvedKey = 'budget';
        } else if (/industry|gyoushu/.test(combined)) {
            resolvedKey = 'industry';
        } else {
            resolvedKey = 'inquiry_type'; // デフォルト
        }
        console.log(`     → ラジオ推定キー: ${resolvedKey}`);
    }

    const prefs = SELECT_PREFERENCES[resolvedKey] || SELECT_PREFERENCES.inquiry_type;
    for (const pref of prefs) {
        for (let i = 0; i < count; i++) {
            const r = radioGroup.nth(i);
            const val = await r.getAttribute('value') || '';
            let labelText = val;
            const id = await r.getAttribute('id');
            if (id) {
                const lbl = await page.locator(`label[for="${id}"]`).textContent().catch(() => '');
                if (lbl) labelText += ' ' + lbl;
            }
            // value属性もチェック（labelがないCF7パターン対応）
            if (labelText.includes(pref) || val.includes(pref)) {
                try { await r.check({ timeout: 1000, force: true }); }
                catch (e) { await r.evaluate(el => el.click()).catch(() => {}); }
                console.log(`     → ラジオ選択: "${pref}" (value=${val})`);
                clicked = true;
                break;
            }
        }
        if (clicked) break;
    }

    // フォールバック: 最初のラジオをチェック（「採用」「応募」系は除く）
    if (!clicked && count > 0) {
        const firstVal = await radioGroup.first().getAttribute('value') || '';
        const exclude = ['採用', '応募', 'recruit', 'career', 'job',
                         '越境', '海外', '輸出', 'グローバル', 'BtoB展開', 'EC',
                         '海外BtoB', '越境EC', 'BtoB'];
        if (!exclude.some(e => firstVal.includes(e))) {
            try { await radioGroup.first().check({ timeout: 1000, force: true }); }
            catch (e) { await radioGroup.first().evaluate(el => el.click()).catch(() => {}); }
            console.log(`     → ラジオ フォールバック選択: 先頭 (value=${firstVal})`);
        } else {
            // 除外キーワードが先頭にある場合、「その他/それ以外」系を探す
            let altClicked = false;
            for (let i = 0; i < count; i++) {
                const r = radioGroup.nth(i);
                const val = await r.getAttribute('value') || '';
                if (['その他', 'それ以外', 'その他のお問い合わせ', 'それ以外のお問い合わせ'].some(kw => val.includes(kw))) {
                    try { await r.check({ timeout: 1000, force: true }); }
                    catch (e) { await r.evaluate(el => el.click()).catch(() => {}); }
                    console.log(`     → ラジオ 除外回避: 「その他/それ以外」を選択 (value=${val})`);
                    altClicked = true;
                    break;
                }
            }
            if (!altClicked) console.log(`     ⚠️  先頭ラジオが除外対象のためスキップ`);
        }
    }
}

module.exports = { submitViaPlaywright, katakanaToHiragana, SELECT_PREFERENCES };
