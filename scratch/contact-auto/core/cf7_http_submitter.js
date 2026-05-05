/**
 * cf7_http_submitter.js
 * ─────────────────────────────────────────────────────────────────────────────
 * WordPress Contact Form 7 特化 HTTP直接送信エンジン
 * 
 * 仕組み:
 *   1. GETでフォームページを取得
 *   2. wpcf7の存在を検出（<form class="wpcf7-form"> / wpcf7のscript）
 *   3. hidden fields (_wpcf7, _wpcf7_version, _wpcf7_locale, _wpcf7_unit_tag, _wpcf7_container_post) を抽出
 *   4. フォームのfield名を抽出（name属性）
 *   5. POSTペイロードを構築
 *   6. CF7のREST APIエンドポイントにPOST送信
 *   7. レスポンスで成功/失敗を判定
 * ─────────────────────────────────────────────────────────────────────────────
 */

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

// playwright_submitterのSELECT_PREFERENCESを共有
const { SELECT_PREFERENCES } = require('./playwright_submitter');

/**
 * ページがCF7フォームかどうかを検出する
 * @param {string} html - ページのHTML
 * @returns {{ isCF7: boolean, formData: object|null }}
 */
function detectCF7(html) {
    const $ = cheerio.load(html);

    // CF7マーカー検出
    const cf7Form = $('form.wpcf7-form, .wpcf7 form, form[action*="wpcf7"]');
    if (cf7Form.length === 0) {
        return { isCF7: false, formData: null };
    }

    const form = cf7Form.first();

    // hidden fields抽出
    const hiddenFields = {};
    form.find('input[type="hidden"]').each((_, el) => {
        const name = $(el).attr('name');
        const value = $(el).attr('value') || '';
        if (name) hiddenFields[name] = value;
    });

    // wpcf7 IDの取得
    const wpcf7Id = hiddenFields['_wpcf7'] || '';
    if (!wpcf7Id) {
        // data-wpcf7-id属性から取得を試みる
        const dataId = form.attr('data-wpcf7-id') || form.closest('.wpcf7').attr('data-wpcf7-id') || '';
        if (dataId) hiddenFields['_wpcf7'] = dataId;
    }

    // 全フィールドのname属性を取得
    const formFields = [];
    form.find('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select').each((_, el) => {
        const name = $(el).attr('name');
        const type = $(el).attr('type') || el.tagName.toLowerCase();
        const placeholder = $(el).attr('placeholder') || '';
        const isRequired = $(el).attr('aria-required') === 'true' || $(el).is('[required]');

        // select: 選択肢テキストを収集
        let options = [];
        if (el.tagName.toLowerCase() === 'select') {
            $(el).find('option').each((_, opt) => {
                const val = $(opt).attr('value') || '';
                const text = $(opt).text().trim();
                if (val && val !== '' && val !== '0') options.push({ value: val, text });
            });
        }

        // radio: value属性とlabelを収集（同nameグループごとに最初の1件を代表として収集）
        let radioValues = [];
        if (type === 'radio') {
            const val = $(el).attr('value') || '';
            const id = $(el).attr('id') || '';
            let labelText = val;
            if (id) {
                const lbl = form.find(`label[for="${id}"]`).text().trim();
                if (lbl) labelText = lbl;
            }
            radioValues.push({ value: val, text: labelText });
        }

        // checkbox: value属性を取得
        let checkboxValue = '';
        if (type === 'checkbox') {
            checkboxValue = $(el).attr('value') || '1';
        }

        // CF7のfield名パターン: your-name, your-email, your-message 等
        if (name) {
            formFields.push({ name, type, placeholder, isRequired, options, radioValues, checkboxValue });
        }
    });

    // action URL（CF7 REST API）
    const actionAttr = form.attr('action') || '';
    let restEndpoint = '';
    if (wpcf7Id || hiddenFields['_wpcf7']) {
        const id = wpcf7Id || hiddenFields['_wpcf7'];
        // CF7 REST API: /wp-json/contact-form-7/v1/contact-forms/{id}/feedback
        // ベースURLをaction属性やページURLから推定
        restEndpoint = `/wp-json/contact-form-7/v1/contact-forms/${id}/feedback`;
    }

    return {
        isCF7: true,
        formData: {
            wpcf7Id: hiddenFields['_wpcf7'] || '',
            hiddenFields,
            formFields,
            actionUrl: actionAttr,
            restEndpoint
        }
    };
}

/**
 * CF7フォームのfield名をプロファイルキーにマッピングする
 * CF7の命名規則: your-name, your-email, your-message, your-company, etc.
 */
const CF7_FIELD_MAP = {
    // 名前系
    'your-name': 'name', 'your_name': 'name', 'name': 'name', 'fullname': 'name',
    'your-sei': 'name_sei', 'sei': 'name_sei', 'last-name': 'name_sei', 'lastname': 'name_sei',
    'your-mei': 'name_mei', 'mei': 'name_mei', 'first-name': 'name_mei', 'firstname': 'name_mei',
    // フリガナ
    'your-kana': 'kana', 'kana': 'kana', 'furigana': 'kana', 'yomi': 'kana',
    'kana-sei': 'kana_sei', 'kana_sei': 'kana_sei',
    'kana-mei': 'kana_mei', 'kana_mei': 'kana_mei',
    // メール
    'your-email': 'email', 'email': 'email', 'mail': 'email', 'your_email': 'email',
    'your-email-confirm': 'email', 'email-confirm': 'email', // 確認用も同じ値
    // 電話
    'your-tel': 'phone', 'tel': 'phone', 'phone': 'phone', 'your_tel': 'phone',
    'tel-1': 'phone_1', 'tel1': 'phone_1', 'tel_1': 'phone_1',
    'tel-2': 'phone_2', 'tel2': 'phone_2', 'tel_2': 'phone_2',
    'tel-3': 'phone_3', 'tel3': 'phone_3', 'tel_3': 'phone_3',
    // 会社（業種特化型の表記追加）
    'your-company': 'company', 'company': 'company', 'company-name': 'company', 'organization': 'company',
    'iin-name': 'company', 'hospital-name': 'company', 'clinic-name': 'company', // 医院名
    'jimusho-mei': 'company', 'law-office': 'company', 'office-name': 'company', // 事務所名
    'shop-name': 'company', 'store-name': 'company', 'mise-mei': 'company',      // 店舗名
    // 部署
    'department': 'department', 'your-department': 'department', 'position': 'department',
    // 件名
    'your-subject': 'subject', 'subject': 'subject',
    // メッセージ
    'your-message': 'message', 'message': 'message', 'inquiry': 'message', 'content': 'message',
    // URL（改善対象・参考URLも追加）
    'your-url': 'url', 'url': 'url', 'website': 'url', 'site-url': 'url',
    'portfolio-url': 'url', 'current-url': 'url', 'existing-url': 'url',
    'ref-url': 'url', 'service-url': 'url',
    // 住所
    'your-address': 'address', 'address': 'address',
    // 郵便番号
    'zipcode': 'zipcode', 'postal-code': 'zipcode', 'zip': 'zipcode',
    // 都道府県
    'prefecture': 'prefecture',
    // 問い合わせ種別（select/radio）
    'inquiry-type': 'inquiry_type', 'menu-type': 'inquiry_type', 'contact-type': 'inquiry_type',
    'contact_type': 'inquiry_type', 'inquiry_type': 'inquiry_type',
    'category': 'inquiry_type', 'shubetsu': 'inquiry_type', 'kind': 'inquiry_type',
    'type': 'inquiry_type', 'item': 'inquiry_type', 'genre': 'inquiry_type',
    // 連絡方法（radio）
    'contact-way': 'preferred_contact', 'contact_way': 'preferred_contact',
    'contact-method': 'preferred_contact', 'renraku': 'preferred_contact',
    'reply-method': 'preferred_contact', 'replymethod': 'preferred_contact',
    // 連絡時間帯（radio/select）
    'contact-time': 'preferred_time', 'preferred-time': 'preferred_time',
    'jikantai': 'preferred_time', 'kibou-jikan': 'preferred_time',
    // 流入経路（select）
    'referral': 'referral', 'how-did': 'referral', 'kikkake': 'referral',
    'source': 'referral', 'channel': 'referral',
    // 業種（select）
    'industry': 'industry', 'gyoushu': 'industry', 'business-type': 'industry',
    // 予算（select）
    'budget': 'budget', 'yosan': 'budget',
    // 納期・制作時期（select）
    'deadline': 'deadline', 'nouki': 'deadline', 'schedule': 'deadline',
    'seisaku-jiki': 'deadline', 'kibou-jiki': 'deadline', 'timing': 'deadline',
    // ページ数（カテゴリ8追加）
    'page-count': 'page_count', 'pages': 'page_count', 'page-su': 'page_count',
    // プラン・コース（追加サンプルから発見）
    'plan': 'plan', 'course': 'plan', 'grade': 'plan', 'package': 'plan',
    // ウェブミーティング希望（チェックボックス）
    'meeting': 'meeting', 'web-meeting': 'meeting', 'zoom': 'meeting'
};

/**
 * CF7送信エビデンスをJSONログとして保存
 */
function saveSubmissionLog(logsDir, pageUrl, { payload, endpoint, response, result, rowId }) {
    if (!logsDir) return;
    try {
        const dir = path.join(logsDir, 'cf7_evidence');
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

        const ts = new Date().toISOString().replace(/[:.]/g, '-');
        const domain = new URL(pageUrl).hostname.replace(/\./g, '_');
        const filename = `${ts}_row${rowId || 'unknown'}_${domain}.json`;

        const log = {
            timestamp: new Date().toISOString(),
            rowId: rowId || 'unknown',
            pageUrl,
            endpoint,
            payloadFields: payload ? (() => {
                try {
                    const obj = {};
                    for (const [k, v] of payload.entries()) obj[k] = v;
                    return obj;
                } catch { return null; }
            })() : null,
            apiResponse: response,
            result: {
                success: result.success,
                status: result.status,
                reason: result.reason || '',
                evidence: result.evidence || 'S'
            }
        };

        // messageフィールドは先頭80文字に切り詰め（ログ肥大化防止）
        if (log.payloadFields && log.payloadFields['your-message']) {
            log.payloadFields['your-message'] = log.payloadFields['your-message'].substring(0, 80) + '...';
        }
        if (log.payloadFields && log.payloadFields['message']) {
            log.payloadFields['message'] = log.payloadFields['message'].substring(0, 80) + '...';
        }

        fs.writeFileSync(path.join(dir, filename), JSON.stringify(log, null, 2), 'utf-8');
        console.log(`  📋 CF7エビデンスログ保存: ${filename}`);
    } catch (e) {
        console.log(`  ⚠️ ログ保存失敗: ${e.message.substring(0, 40)}`);
    }
}

/**
 * CF7フォームにHTTP直接送信
 * @param {string} pageUrl - フォームページURL
 * @param {object} profile - 送信者プロファイル
 * @param {object} options - オプション
 * @returns {Promise<{success: boolean, status: string, reason: string}>}
 */
async function submitCF7(pageUrl, profile, options = {}) {
    const { dryRun = false, timeout = 15000, logsDir = null, rowId = null } = options;

    try {
        // ──── Step 1: GETでページを取得 ────
        const getResponse = await axios.get(pageUrl, {
            timeout,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8'
            }
        });

        const cookies = getResponse.headers['set-cookie'] || [];
        const cookieString = cookies.map(c => c.split(';')[0]).join('; ');

        // ──── Step 2: CF7検出 ────
        const { isCF7, formData } = detectCF7(getResponse.data);
        if (!isCF7 || !formData) {
            return { success: false, status: '×', reason: 'CF7フォーム検出失敗' };
        }

        console.log(`  🔍 CF7検出: ID=${formData.wpcf7Id}, フィールド数=${formData.formFields.length}`);

        // ──── Step 3: POSTペイロード構築 ────
        const payload = new URLSearchParams();

        // hidden fields を追加
        for (const [key, val] of Object.entries(formData.hiddenFields)) {
            payload.append(key, val);
        }

        // フォームフィールドをプロファイルからマッピング
        let mappedCount = 0;
        let unmappedFields = [];

        // radioはname属性が同じものがグループ → 1グループ1エントリにまとめる
        const radioGroups = {};
        const normalFields = [];
        for (const field of formData.formFields) {
            if (field.type === 'radio') {
                if (!radioGroups[field.name]) radioGroups[field.name] = [];
                if (field.radioValues.length > 0) radioGroups[field.name].push(...field.radioValues);
            } else {
                normalFields.push(field);
            }
        }
        // radioグループを1つのフィールドとしてnormalFieldsに追加
        for (const [name, radioVals] of Object.entries(radioGroups)) {
            normalFields.push({ name, type: 'radio', options: radioVals, isRequired: false, placeholder: '' });
        }

        for (const field of normalFields) {
            const profileKey = CF7_FIELD_MAP[field.name.toLowerCase()];

            if (field.type === 'select' || field.type === 'radio') {
                // select/radio: SELECT_PREFERENCESで自動選択
                const key = profileKey || 'inquiry_type';
                const prefs = SELECT_PREFERENCES[key] || SELECT_PREFERENCES.inquiry_type;
                const opts = field.options || [];
                let chosen = null;
                for (const pref of prefs) {
                    const hit = opts.find(o => o.text.includes(pref) || o.value.includes(pref));
                    if (hit) { chosen = hit; break; }
                }
                if (chosen) {
                    payload.append(field.name, chosen.value || chosen.text);
                    mappedCount++;
                    console.log(`  ✏️  ${field.name} [${field.type}] → "${chosen.text}" (${chosen.value || chosen.text})`);
                } else if (opts.length > 0) {
                    // フォールバック: 最初の選択肢を使う（空値は除く）
                    payload.append(field.name, opts[0].value || opts[0].text);
                    console.log(`  ✏️  ${field.name} [${field.type}] フォールバック → "${opts[0].text}"`);
                    mappedCount++;
                }
            } else if (profileKey && profile[profileKey] !== undefined && profile[profileKey] !== '') {
                payload.append(field.name, String(profile[profileKey]));
                mappedCount++;
                console.log(`  ✏️  ${field.name} → ${profileKey}`);
            } else if (field.type === 'checkbox') {
                // 同意系チェックボックス等は、HTMLで定義されたvalueを送る
                const val = field.checkboxValue || '1';
                payload.append(field.name, val);
                console.log(`  ☑️  チェックボックス送信: ${field.name} = "${val}"`);
            } else if (field.isRequired) {
                unmappedFields.push(field.name);
                console.log(`  ❓ 未マッチ（必須）: ${field.name}`);
            }
        }

        // ── CF7デフォルトテンプレート正規タグの完全補完 ──
        // CF7のメールテンプレートはデフォルトで以下の4タグを使う:
        //   差出人: [your-name] <[your-email]>
        //   題名:   [your-subject]
        //   本文:   [your-message]
        //
        // ⚠️ C-04ルール: your-subject は「フォームHTML内に your-subject フィールドが
        //   存在しなくても」必ず空文字で常時送信する。
        //   CF7メールテンプレートは [your-subject] を参照しているため、
        //   フォーム側フィールドが未定義の場合でもリテラルがそのまま届く。
        //   → detectedFieldNames チェックを your-subject には適用しない。
        //
        // ※ your-subject を空文字にする理由:
        //   本文冒頭の【タイトル】で件名情報は受信者に伝わる設計のため、
        //   題名に値を入れると二重表記になり受信者に不自然な印象を与える。
        //
        // ※ その他3タグ（your-name/your-email/your-message）は
        //   フォームに存在しないフィールドを送ると CF7 が
        //   「未定義の値がこの項目を通じて送信されました」エラーを返すため、
        //   detectedFieldNames で存在チェックを行う。
        const detectedFieldNames = new Set(formData.formFields.map(f => f.name.toLowerCase()));

        // ★ your-subject: フォーム定義の有無にかかわらず常時空文字で送信（C-04）
        if (!payload.has('your-subject')) {
            payload.append('your-subject', '');
            console.log(`  🛡️  [CF7正規タグ] your-subject を常時空値送信（リテラル防止 / C-04）`);
        }

        // その他3タグは detectedFieldNames で存在確認してから補完
        const CF7_CANONICAL_TAGS = {
            'your-name':    profile.name || '',
            'your-email':   profile.email || '',
            'your-message': profile.message || ''
        };
        for (const [tagName, val] of Object.entries(CF7_CANONICAL_TAGS)) {
            if (!payload.has(tagName) && detectedFieldNames.has(tagName)) {
                payload.append(tagName, val);
                if (val) {
                    console.log(`  🛡️  [CF7正規タグ補完] ${tagName} を追加送信`);
                } else {
                    console.log(`  🛡️  [CF7正規タグ補完] ${tagName} を空値送信（リテラル防止）`);
                }
            }
        }

        if (unmappedFields.length > 0) {
            return {
                success: false,
                status: '×',
                reason: `CF7必須フィールド未マッチ: ${unmappedFields.join(', ')}`
            };
        }

        if (dryRun) {
            console.log(`  🔍 [DryRun] CF7 HTTP送信をスキップ（${mappedCount}フィールドマッチ）`);
            return { success: true, status: '未', reason: 'DryRun - CF7 HTTP送信対象' };
        }

        // ──── Step 4: REST APIにPOST ────
        // ベースURLを推定
        const urlObj = new URL(pageUrl);
        const baseUrl = `${urlObj.protocol}//${urlObj.host}`;
        const endpoint = `${baseUrl}${formData.restEndpoint}`;

        console.log(`  📤 CF7 HTTP送信: ${endpoint}`);

        // CF7 v5.7以降は multipart/form-data が必須
        // FormData（Node.js標準）でmultipartを構築
        const { FormData } = require('undici');
        const formDataMultipart = new FormData();
        for (const [key, val] of payload.entries()) {
            formDataMultipart.append(key, val);
        }

        const postResponse = await axios.post(endpoint, formDataMultipart, {
            timeout,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Referer': pageUrl,
                'Origin': baseUrl,
                'Cookie': cookieString,
                'Accept': 'application/json, */*'
                // Content-Typeはaxiosがmultipart/form-dataを自動設定
            }
        });

        // ──── Step 5: レスポンス判定 ────
        const resData = postResponse.data;
        if (typeof resData === 'object') {
            // CF7 REST APIのレスポンス形式: { status: "mail_sent", message: "..." }
            if (resData.status === 'mail_sent') {
                console.log(`  ✅ CF7送信成功: ${resData.message || ''}`);
                const result = { success: true, status: '〇', reason: '', evidence: 'S' };
                saveSubmissionLog(logsDir, pageUrl, { payload, endpoint, response: resData, result, rowId });
                return result;
            } else if (resData.status === 'validation_failed') {
                const errors = (resData.invalid_fields || []).map(f => f.message).join('; ');
                console.log(`  ❌ CF7バリデーションエラー: ${errors}`);
                const result = { success: false, status: '×', reason: `CF7バリデーション: ${errors}` };
                saveSubmissionLog(logsDir, pageUrl, { payload, endpoint, response: resData, result, rowId });
                return result;
            } else if (resData.status === 'spam') {
                console.log(`  ❌ CF7スパム判定`);
                const result = { success: false, status: '×', reason: 'CF7スパム判定' };
                saveSubmissionLog(logsDir, pageUrl, { payload, endpoint, response: resData, result, rowId });
                return result;
            } else {
                console.log(`  ⚠️ CF7不明レスポンス: ${JSON.stringify(resData).substring(0, 100)}`);
                const result = { success: false, status: '×', reason: `CF7不明: ${resData.status || 'unknown'}` };
                saveSubmissionLog(logsDir, pageUrl, { payload, endpoint, response: resData, result, rowId });
                return result;
            }
        }

        // 非JSON応答（旧バージョンCF7、action属性でのPOST等）
        const resText = String(resData);
        if (resText.includes('ありがとう') || resText.includes('送信されました') || resText.includes('thank')) {
            return { success: true, status: '〇', reason: '' };
        }

        return { success: false, status: '×', reason: 'CF7レスポンス不明' };

    } catch (err) {
        const msg = err.response
            ? `HTTP ${err.response.status}: ${(err.response.data?.message || '').substring(0, 50)}`
            : err.message.substring(0, 80);
        console.log(`  ❌ CF7 HTTPエラー: ${msg}`);
        return { success: false, status: '×', reason: `CF7 HTTPエラー: ${msg}` };
    }
}

/**
 * URLのHTMLからCF7かどうかを事前判定（軽量チェック）
 */
async function isCF7Page(url) {
    try {
        const { data } = await axios.get(url, {
            timeout: 10000,
            headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }
        });
        const { isCF7 } = detectCF7(data);
        return isCF7;
    } catch {
        return false;
    }
}

module.exports = { detectCF7, submitCF7, isCF7Page, CF7_FIELD_MAP };
