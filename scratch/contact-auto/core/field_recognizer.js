/**
 * field_recognizer.js
 * ─────────────────────────────────────────────────────────────────────────────
 * 5層フィールド認識エンジン
 * 
 * Layer 1: 標準認識（label, aria-label, for属性, placeholder）
 * Layer 2: DOM周辺走査（sibling, parent dt/th, closest tr/li/dl）
 * Layer 3: 属性意味推定（name/id のセマンティック解析, autocomplete属性）
 * Layer 4: 座標ベース近接テキスト（getBoundingClientRect → 上方・左方の最寄り）
 * Layer 5: マッピングJSON照合
 * ─────────────────────────────────────────────────────────────────────────────
 */

const fs = require('fs');
const path = require('path');

// ── name/id属性から意味を推定するためのセマンティックマップ ──
// ★ 順序が重要: 特定的なキー（email, phone等）を先、汎用（name, message）を後に配置
// ★ 11カテゴリ（500+URL調査レポート準拠）+ 補助カテゴリ
const SEMANTIC_ATTR_MAP_ORDERED = [
    // --- カテゴリ2: 連絡先 ---
    ['email', [
        /e?[_-]?mail/i, /your[_-]?email/i, /contact[_-]?email/i,
        /^em$/i, /mail[_-]?address/i, /email[_-]?confirm/i
    ]],
    ['phone', [
        /^(your[_-]?)?tel$/i, /^phone$/i, /denwa/i, /^tel$/i,
        /tel[_-]?\d/i, /phone[_-]?\d/i, /telephone/i
    ]],
    ['fax', [
        /^fax$/i, /fax[_-]?number/i, /fax[_-]?no/i
    ]],
    // --- カテゴリ3: 会社・組織 ---
    ['company', [
        /company/i, /^organization$/i, /corp/i, /kaisha/i, /kigyou/i,
        /^org$/i, /firm/i, /goshamei/i, /kishamei/i, /^houjin/i,
        /iin[_-]?mei/i, /jimusho/i,
        // 業種特化型（500+URL調査追加分）
        /iin[_-]?name/i, /hospital[_-]?name/i, /clinic[_-]?name/i, // 医院名
        /office[_-]?name/i, /law[_-]?office/i, /jimusho[_-]?mei/i, // 事務所名
        /^shop[_-]?name$/i, /^store[_-]?name$/i, /^mise[_-]?mei$/i  // 店舗名
    ]],
    ['department', [
        /department/i, /division/i, /section/i, /^position$/i,
        /busho/i, /yakushoku/i, /^role$/i
    ]],
    // --- カテゴリ4: URL ---
    ['url', [
        /^url$/i, /^website$/i, /^homepage$/i, /site[_-]?url/i, /web[_-]?url/i,
        /portfolio[_-]?url/i, /current[_-]?url/i, /existing[_-]?url/i,
        /kaizen[_-]?url/i, /service[_-]?url/i, /ref[_-]?url/i,
        /参考[_-]?url/i, /改善[_-]?url/i
    ]],
    // --- カテゴリ5: 住所 ---
    ['address', [
        /^address$/i, /jusho/i, /^location$/i, /^addr$/i
    ]],
    ['zipcode', [
        /zip/i, /postal/i, /postcode/i, /yuubin/i
    ]],
    ['prefecture', [
        /^prefecture$/i, /^pref$/i, /todouhuken/i, /^region$/i, /^state$/i
    ]],
    // --- カテゴリ6: 件名 ---
    ['subject', [
        /^subject$/i, /^title$/i, /kenmei/i, /^subj$/i
    ]],
    // --- カテゴリ7: 問い合わせ種別 ---
    ['inquiry_type', [
        /inquiry[_-]?type/i, /contact[_-]?type/i, /^category$/i, /shubetsu/i,
        /item[_-]?type/i
    ]],
    // --- カテゴリ8: プロジェクト詳細 ---
    ['budget', [
        /budget/i, /yosan/i, /^price$/i, /cost/i
    ]],
    ['deadline', [
        /deadline/i, /schedule/i, /nouki/i, /^timing$/i, /seisaku[_-]?jiki/i,
        /seisaku[_-]?jiki/i, /kiboujiki/i, /noki/i, /^when$/i,
        /制作[_-]?時期/i, /納期/i
    ]],
    // カテゴリ8追加: ページ数
    ['page_count', [
        /page[_-]?count/i, /num[_-]?page/i, /^pages$/i, /page[_-]?su/i
    ]],
    // カテゴリ8追加: プラン・コース（追加サンプルから発見）
    ['plan', [
        /^plan$/i, /^course$/i, /kibou[_-]?plan/i, /^grade$/i, /^package$/i
    ]],
    // 追加サンプル: ウェブミーティング希望
    ['meeting', [
        /meeting/i, /zoom/i, /web[_-]?meeting/i, /online[_-]?meeting/i,
        /misutingu/i
    ]],
    // --- カテゴリ9: 流入経路 ---
    ['referral', [
        /referral/i, /how[_-]?did/i, /kikkake/i, /^source$/i, /channel/i
    ]],
    // --- カテゴリ10: 連絡方法 ---
    ['preferred_contact', [
        /preferred/i, /contact[_-]?method/i, /renraku/i
    ]],
    ['preferred_time', [
        /^time$/i, /jikantai/i, /kibou[_-]?jikan/i
    ]],
    // --- 業種 ---
    ['industry', [
        /^industry$/i, /business[_-]?type/i, /gyoushu/i, /gyoukai/i
    ]],
    // --- カテゴリ1: 氏名（name系は必ず後半に配置） ---
    ['kana', [
        /kana/i, /furigana/i, /yomi/i, /^reading$/i, /ruby/i
    ]],
    ['name_sei', [
        /^sei$/i, /last[_-]?name/i, /family[_-]?name/i, /^surname$/i, /^lname$/i,
        /name[_-]?1$/i
    ]],
    ['name_mei', [
        /^mei$/i, /first[_-]?name/i, /given[_-]?name/i, /^fname$/i,
        /name[_-]?2$/i
    ]],
    // --- カテゴリ5: 本文（汎用なので後半） ---
    ['message', [
        /^message$/i, /^body$/i, /^inquiry$/i, /^content$/i, /^comment$/i,
        /naiyou/i, /^detail$/i, /^msg$/i, /^description$/i, /soudan/i
    ]],
    // name は最も汎用的なので最後
    ['name', [
        /^(your[_-]?)?name$/i, /^full[_-]?name$/i, /^shimei$/i, /^onamae$/i,
        /^customer[_-]?name$/i, /^contact[_-]?name$/i, /^nm$/i,
        /^tantousha$/i, /^担当者$/i
    ]]
];
// 後方互換用（export）
const SEMANTIC_ATTR_MAP = Object.fromEntries(SEMANTIC_ATTR_MAP_ORDERED);

// ── autocomplete属性マッピング ──
const AUTOCOMPLETE_MAP = {
    'name': 'name',
    'given-name': 'name_mei',
    'family-name': 'name_sei',
    'email': 'email',
    'tel': 'phone',
    'organization': 'company',
    'street-address': 'address',
    'address-line1': 'address',
    'postal-code': 'zipcode',
    'address-level1': 'prefecture'
};

/**
 * ブラウザページ内でフィールド情報を5層で収集する
 * @param {import('patchright').Page} page
 * @returns {Promise<Array>} フィールド情報の配列
 */
async function analyzeFormFields(page) {
    return await page.evaluate(() => {
        // ── スキャン範囲をCF7フォーム内に限定 ──
        // 1. wpcf7クラスのフォームを優先
        let scanRoot = document.querySelector('form.wpcf7-form, div.wpcf7 form, .wpcf7');
        // 2. なければmain/article内の最も要素数が多いformを選択
        if (!scanRoot) {
            const contentArea = document.querySelector('main, article, #main, #content, .content');
            const forms = Array.from((contentArea || document).querySelectorAll('form'));
            if (forms.length > 0) {
                let maxCount = 0;
                forms.forEach(f => {
                    const cnt = f.querySelectorAll('input, textarea, select').length;
                    if (cnt > maxCount) { maxCount = cnt; scanRoot = f; }
                });
            }
        }
        // 3. それでもなければdocument全体（フォールバック）
        const root = scanRoot || document;
        const inputs = Array.from(root.querySelectorAll(
            'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="image"]):not([name="s"]):not([name="search"]):not([name="q"]), textarea, select'
        ));

        return inputs.map(el => {
            // ──────── Layer 1: 標準認識 ────────
            let layer1Text = '';
            // 1a. <label> タグ
            if (el.labels && el.labels.length > 0) {
                layer1Text = el.labels[0].innerText || el.labels[0].textContent || '';
            }
            // 1b. aria-label
            if (!layer1Text && el.getAttribute('aria-label')) {
                layer1Text = el.getAttribute('aria-label');
            }
            // 1c. for属性で紐づくlabel
            if (!layer1Text && el.id) {
                const label = document.querySelector(`label[for="${el.id}"]`);
                if (label) layer1Text = label.innerText || label.textContent || '';
            }
            // 1d. placeholder
            if (!layer1Text && el.getAttribute('placeholder')) {
                layer1Text = el.getAttribute('placeholder');
            }

            // ──────── Layer 2: DOM周辺走査 ────────
            let layer2Text = '';
            // 2a. 直前のsiblingテキスト
            let prev = el.previousElementSibling;
            if (!prev) {
                // inputが<td>や<div>内の場合、親の前のsiblingを見る
                const parent = el.parentElement;
                if (parent) prev = parent.previousElementSibling;
            }
            if (prev) {
                const t = (prev.innerText || prev.textContent || '').trim();
                if (t.length > 0 && t.length < 100) layer2Text = t;
            }
            // 2b. 親のdt/thタグ
            if (!layer2Text) {
                const dd = el.closest('dd, td');
                if (dd) {
                    const dt = dd.previousElementSibling;
                    if (dt && (dt.tagName === 'DT' || dt.tagName === 'TH')) {
                        layer2Text = (dt.innerText || dt.textContent || '').trim();
                    }
                }
            }
            // 2c. closest tr/li/dl/div.form-group のテキスト
            if (!layer2Text) {
                const container = el.closest('tr, li, dl, .form-group, .form-item, .form-row, .field, .input-group');
                if (container) {
                    // containerのテキストからinput自身のテキストを除く
                    const clone = container.cloneNode(true);
                    clone.querySelectorAll('input, textarea, select').forEach(e => e.remove());
                    const t = (clone.innerText || clone.textContent || '').trim().replace(/\s+/g, ' ');
                    if (t.length > 0 && t.length < 150) layer2Text = t;
                }
            }

            // ──────── Layer 3: 属性情報（サーバー側で解析） ────────
            const attrInfo = {
                name: el.getAttribute('name') || '',
                id: el.id || '',
                autocomplete: el.getAttribute('autocomplete') || '',
                type: el.type || el.tagName.toLowerCase(),
                className: el.className || ''
            };

            // ──────── Layer 4: 座標ベース近接テキスト ────────
            let layer4Text = '';
            try {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    // 入力欄の左上を基準に、上方と左方のテキスト要素を探す
                    const allTextEls = Array.from(document.querySelectorAll(
                        'label, span, p, th, dt, td, div, h1, h2, h3, h4, h5, h6, strong, em, b'
                    ));
                    let bestMatch = null;
                    let bestDist = Infinity;

                    for (const textEl of allTextEls) {
                        // input/textarea/selectを含む要素はスキップ
                        if (textEl.querySelector('input, textarea, select')) continue;
                        const text = (textEl.innerText || textEl.textContent || '').trim();
                        if (text.length === 0 || text.length > 80) continue;

                        const textRect = textEl.getBoundingClientRect();
                        if (textRect.width === 0 || textRect.height === 0) continue;

                        // 上方（同じX軸範囲、Y座標が上）または左方（同じY軸範囲、X座標が左）
                        const isAbove = textRect.bottom <= rect.top + 5 && 
                                       textRect.left < rect.right && textRect.right > rect.left;
                        const isLeft = textRect.right <= rect.left + 5 && 
                                      textRect.top < rect.bottom && textRect.bottom > rect.top;

                        if (isAbove || isLeft) {
                            const dist = Math.abs(textRect.bottom - rect.top) + Math.abs(textRect.left - rect.left);
                            if (dist < bestDist) {
                                bestDist = dist;
                                bestMatch = text;
                            }
                        }
                    }
                    if (bestMatch) layer4Text = bestMatch;
                }
            } catch (e) { /* getBoundingClientRect may fail in edge cases */ }

            // ──────── 必須判定 ────────
            let isRequired = false;
            if (el.required || el.getAttribute('aria-required') === 'true') isRequired = true;
            const classStr = (el.className || '') + (el.labels && el.labels.length > 0 ? ' ' + el.labels[0].className : '');
            if (classStr.toLowerCase().includes('required') || classStr.toLowerCase().includes('hissu')) isRequired = true;
            if (!isRequired) {
                const widerParent = el.closest('tr, li, dl, .form-group, .form-row, .field') || el.parentElement;
                if (widerParent) {
                    const tc = widerParent.innerText || widerParent.textContent || '';
                    if (tc.includes('必須') || tc.toLowerCase().includes('required')) isRequired = true;
                }
            }
            if (!isRequired && layer1Text) {
                const l1 = layer1Text.trim();
                if (l1.endsWith('*') || l1.endsWith('＊') || l1.includes('※必須') || l1.includes('*必須') || l1.includes('＊必須')) isRequired = true;
            }

            // ──────── XPath ────────
            function getXPath(element) {
                if (element.id !== '') return 'id("' + element.id + '")';
                if (element === document.body) return element.tagName;
                let ix = 0;
                const siblings = element.parentNode ? element.parentNode.childNodes : [];
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
                }
                return '';
            }

            return {
                // Layer 1
                layer1: layer1Text.trim().replace(/\s+/g, ' '),
                // Layer 2
                layer2: layer2Text.trim().replace(/\s+/g, ' '),
                // Layer 3 (attributes)
                ...attrInfo,
                // Layer 4
                layer4: layer4Text.trim().replace(/\s+/g, ' '),
                // Meta
                tagName: el.tagName.toLowerCase(),
                xpath: getXPath(el),
                isRequired
            };
        });
    });
}

/**
 * 5層の情報を統合してマッピングキーを決定する
 * @param {Array} fieldsData - analyzeFormFieldsの返り値
 * @param {object} mapping - マッピングJSON
 * @returns {Array} マッチ結果付きフィールド配列
 */
function resolveFieldMappings(fieldsData, mapping) {
    // _meta等の非配列エントリをフィルタし、キーワード長の降順でソート
    const mappingEntries = Object.entries(mapping)
        .filter(([key, val]) => Array.isArray(val))
        .sort((a, b) => {
            const maxLenA = Math.max(...a[1].map(k => k.length));
            const maxLenB = Math.max(...b[1].map(k => k.length));
        return maxLenB - maxLenA;
    });

    const mapped = fieldsData.map(field => {
        let matchedKey = null;
        let matchSource = null;

        // ─── Step 1: テキスト層のみでマッピングJSONマッチ（name/id属性は含めない） ───
        const textLayers = `${field.layer1} ${field.layer2} ${field.layer4}`.toLowerCase();

        if (textLayers.trim()) {
            for (const [key, keywords] of mappingEntries) {
                for (const keyword of keywords) {
                    if (textLayers.includes(keyword.toLowerCase())) {
                        matchedKey = key;
                        matchSource = 'mapping';
                        break;
                    }
                }
                if (matchedKey) break;
            }
        }

        // ─── Step 2: マッチ失敗時 → 属性セマンティック解析（name/id属性のみ） ───
        if (!matchedKey) {
            for (const [profileKey, patterns] of SEMANTIC_ATTR_MAP_ORDERED) {
                for (const pattern of patterns) {
                    if (pattern.test(field.name) || pattern.test(field.id)) {
                        matchedKey = profileKey;
                        matchSource = 'semantic';
                        break;
                    }
                }
                if (matchedKey) break;
            }
        }

        // ─── Step 3: autocomplete属性 ───
        if (!matchedKey && field.autocomplete && AUTOCOMPLETE_MAP[field.autocomplete]) {
            matchedKey = AUTOCOMPLETE_MAP[field.autocomplete];
            matchSource = 'autocomplete';
        }

        // ─── Step 4: tagName/type による最終推定 ───
        // selectでinquiry_typeのテキストが近くにある場合
        if (!matchedKey && field.tagName === 'select') {
            const selectText = `${field.layer1} ${field.layer2} ${field.layer4}`.toLowerCase();
            if (selectText.includes('種別') || selectText.includes('種類') || selectText.includes('項目') || selectText.includes('ご用件')) {
                matchedKey = 'inquiry_type';
                matchSource = 'mapping';
            }
        }

        // ─── Step 5: 姓名・フリガナ・電話・郵便番号の分割判定 ───
        if (matchedKey) {
            if (matchedKey === 'name') {
                if (/sei|last|1$/i.test(field.name) || /sei|last|1$/i.test(field.id)) matchedKey = 'name_sei';
                else if (/mei|first|2$/i.test(field.name) || /mei|first|2$/i.test(field.id)) matchedKey = 'name_mei';
            } else if (matchedKey === 'kana') {
                if (/sei|last|1$/i.test(field.name) || /sei|last|1$/i.test(field.id)) matchedKey = 'kana_sei';
                else if (/mei|first|2$/i.test(field.name) || /mei|first|2$/i.test(field.id)) matchedKey = 'kana_mei';
            } else if (matchedKey === 'phone') {
                if (/[_-]?1$|first/i.test(field.name) || /[_-]?1$|first/i.test(field.id)) matchedKey = 'phone_1';
                else if (/[_-]?2$|mid/i.test(field.name) || /[_-]?2$|mid/i.test(field.id)) matchedKey = 'phone_2';
                else if (/[_-]?3$|last/i.test(field.name) || /[_-]?3$|last/i.test(field.id)) matchedKey = 'phone_3';
            } else if (matchedKey === 'zipcode') {
                if (/[_-]?1$|first/i.test(field.name) || /[_-]?1$|first/i.test(field.id)) matchedKey = 'zipcode_1';
                else if (/[_-]?2$|last/i.test(field.name) || /[_-]?2$|last/i.test(field.id)) matchedKey = 'zipcode_2';
            }
        }

        return {
            ...field,
            matchedKey,
            matchSource
        };
    });

    // ─── Step 6: 姓名の孤立判定と統合 ───
    // name_sei はあるが name_mei が無い（またはその逆）場合、単一の name に戻す
    const hasSei = mapped.some(f => f.matchedKey === 'name_sei' || f.matchedKey === 'kana_sei');
    const hasMei = mapped.some(f => f.matchedKey === 'name_mei' || f.matchedKey === 'kana_mei');
    if (hasSei !== hasMei) {
        mapped.forEach(f => {
            if (f.matchedKey === 'name_sei' || f.matchedKey === 'name_mei') f.matchedKey = 'name';
            if (f.matchedKey === 'kana_sei' || f.matchedKey === 'kana_mei') f.matchedKey = 'kana';
        });
    }

    return mapped;
}

/**
 * マッチしなかったフィールドをログに保存（パターン学習用）
 */
function logUnmatchedFields(url, unmatchedFields, logsDir) {
    if (unmatchedFields.length === 0) return;

    const logEntry = {
        url,
        timestamp: new Date().toISOString(),
        fields: unmatchedFields.map(f => ({
            name: f.name,
            id: f.id,
            type: f.type,
            layer1: f.layer1,
            layer2: f.layer2,
            layer4: f.layer4,
            isRequired: f.isRequired
        }))
    };

    const logFile = path.join(logsDir, `unmatched_${Date.now()}.json`);
    fs.writeFileSync(logFile, JSON.stringify(logEntry, null, 2), 'utf-8');
    return logFile;
}

module.exports = { analyzeFormFields, resolveFieldMappings, logUnmatchedFields, SEMANTIC_ATTR_MAP, AUTOCOMPLETE_MAP };
