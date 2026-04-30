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
        // その他（最終フォールバック）
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

        // ──── 5層フィールド認識 ────
        console.log('  🔍 5層フィールド認識エンジン起動...');
        const rawFields = await analyzeFormFields(page);
        const fields = resolveFieldMappings(rawFields, mapping);

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
            const alwaysFill = ['message', 'subject'];
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
                const locator = page.locator(sel).first();

                if (field.tagName === 'select') {
                    await fillSelect(locator, profile, field.matchedKey);
                } else if (field.type === 'radio') {
                    await fillRadio(page, field, profile, field.matchedKey);
                } else if (field.type === 'checkbox') {
                    if (isConsent || ['inquiry_type', 'preferred_contact', 'budget', 'referral', 'industry'].includes(field.matchedKey)) {
                        try { await locator.check({ timeout: 1000, force: true }); }
                        catch (e) { await locator.evaluate(el => el.click()).catch(() => {}); }
                        filledCount++;
                        if (!isConsent) console.log(`  ☑️  チェックボックス選択: ${field.layer1 || field.name}`);
                    }
                } else {
                    await locator.fill(fillVal, { timeout: 3000 });
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
        return await submitForm(page, screenshotsDir, rowId);

    } catch (e) {
        console.log(`  ❌ エラー: ${e.message}`);
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
async function submitForm(page, screenshotsDir, rowId) {
    console.log('  📤 送信ボタンを検索...');
    const submitBtn = page.locator(
        'input[type="submit"], button:has-text("送信"), button:has-text("確認"), button[type="submit"], input[value*="送信"], input[value*="確認"]'
    ).first();

    if (!await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        return { success: false, status: '×', reason: '送信ボタンが見つかりません' };
    }

    // 送信前のURL・ページテキストを記録（ページ変化の検出用）
    const urlBefore = page.url();
    const textBefore = await page.evaluate(() => document.body.textContent || '');

    await submitBtn.click();
    console.log('  📤 送信ボタンクリック');

    // ──── Rank A: CF7 AJAX応答 ────
    try {
        await page.waitForFunction(() => {
            const el = document.querySelector('.wpcf7-response-output');
            return el && el.textContent.trim().length > 0 && el.offsetParent !== null;
        }, { timeout: 10000 });

        const responseText = await page.locator('.wpcf7-response-output').textContent({ timeout: 3000 });
        console.log(`  📩 CF7応答: ${responseText}`);
        if (/ありがとう|送信されました|sent|thank/i.test(responseText)) {
            await saveResultScreenshot(page, screenshotsDir, rowId);
            console.log(`  ✅ [Rank A] CF7 AJAX成功応答`);
            return { success: true, status: '〇', reason: 'CF7 AJAX成功', evidence: 'A' };
        }
        // CF7がエラーを返した場合
        if (/エラー|error|入力/i.test(responseText)) {
            await saveResultScreenshot(page, screenshotsDir, rowId);
            return { success: false, status: '×', reason: `CF7エラー: ${responseText.substring(0, 50)}` };
        }
    } catch {
        console.log(`  ℹ️  CF7応答なし（通常フォームと判定）`);
    }

    // ──── 2段階確認ページの処理 ────
    let wentThroughConfirm = false;
    await page.waitForTimeout(3000);
    const finalSubmit = page.locator(
        'input[type="submit"], button:has-text("送信"), button[type="submit"], input[value*="送信"]'
    ).first();

    if (await finalSubmit.isVisible({ timeout: 2000 }).catch(() => false)) {
        console.log('  📤 確認ページの送信ボタンをクリック');
        await finalSubmit.click();
        await page.waitForTimeout(4000);
        wentThroughConfirm = true;
    }

    // ──── 送信結果を検証 ────
    const result = await verifySubmission(page, urlBefore, textBefore, wentThroughConfirm);

    // 送信後スクリーンショット（エビデンス）
    await saveResultScreenshot(page, screenshotsDir, rowId);

    return result;
}

/**
 * 送信後スクリーンショットを保存（エビデンス用）
 */
async function saveResultScreenshot(page, screenshotsDir, rowId) {
    if (!screenshotsDir) return;
    try {
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.waitForTimeout(300);
        const shotPath = path.join(screenshotsDir, `result_row_${rowId}.png`);
        await page.screenshot({ path: shotPath, fullPage: true });
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
async function verifySubmission(page, urlBefore, textBefore, wentThroughConfirm) {
    const pageText = await page.evaluate(() => document.body.textContent || '');
    const currentUrl = page.url();

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
            console.log(`  ❌ エラー検出: "${text}"`);
            return { success: false, status: '×', reason: `バリデーションエラー: ${text}`, evidence: 'error' };
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
        const exclude = ['採用', '応募', 'recruit', 'career', 'job'];
        if (!exclude.some(e => firstVal.includes(e))) {
            try { await radioGroup.first().check({ timeout: 1000, force: true }); }
            catch (e) { await radioGroup.first().evaluate(el => el.click()).catch(() => {}); }
            console.log(`     → ラジオ フォールバック選択: 先頭 (value=${firstVal})`);
        }
    }
}

module.exports = { submitViaPlaywright, katakanaToHiragana, SELECT_PREFERENCES };
