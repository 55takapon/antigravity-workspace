/**
 * run_form_session.js
 * ─────────────────────────────────────────────────────────────────────────────
 * 「入力はAIが担当、送信ボタンはユーザーが押す」セッション型フォーム入力スクリプト
 *
 * 使い方:
 *   node run_form_session.js \
 *     --sheets <スプレッドシートID> \
 *     --sheet-name <シート名> \
 *     --rows <開始行>-<終了行>  (例: --rows 2-3)
 *     [--profile <プロファイルJSONファイル名>]
 *     [--mapping <マッピングJSONファイル名>]
 *     [--all-fields]
 *
 * 禁止事項:
 *   - 送信ボタンは絶対に押さない（ユーザーが手動で押す）
 *   - 送信日（G列）が入力済みの行はスキップ
 *   - 送信不可理由（I列）に「営業NG」等のコメントがある行はスキップ
 * ─────────────────────────────────────────────────────────────────────────────
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const fs   = require('fs');
const path = require('path');
const readline = require('readline');
const { google } = require('googleapis');

// ── スキップ対象キーワード（I列・送信不可理由列） ──────────────────────────
const SKIP_KEYWORDS_IN_REASON_COL = [
    '営業NG', '営業ng', 'NG', '送信不可', 'スキップ', '除外', 'フォームなし',
    '閉鎖', '削除', 'リンク切れ', 'エラー', '対象外'
];

// ── 営業NGページキーワード（フォームページのテキスト検出用） ──────────────
const SALES_NG_KEYWORDS = [
    '営業お断り', '営業禁止', '営業目的', 'セールス禁止', 'セールスお断り',
    '営業・勧誘', '営業活動', '売り込み禁止', '売り込みお断り',
    '営業メール禁止', '営業電話禁止', '営業以外', '営業のお電話',
    '営業・セールス', '一切お断り', '固くお断り', '営業行為はご遠慮',
    'セールス行為はご遠慮', '勧誘はご遠慮', '売り込みはご遠慮'
];

// ── エントリポイント ──────────────────────────────────────────────────────────
async function main() {
    const args = process.argv.slice(2);

    let spreadsheetId = null;
    let sheetName     = null;
    let rowStart      = null;
    let rowEnd        = null;
    let profileFile   = 'web-company_profile.json';
    let mappingFile   = 'web-company_mapping.json';
    const isAllFields = args.includes('--all-fields');

    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--sheets'     && args[i+1]) spreadsheetId = args[i+1];
        if (args[i] === '--sheet-name' && args[i+1]) sheetName     = args[i+1];
        if (args[i] === '--profile'    && args[i+1]) profileFile   = args[i+1];
        if (args[i] === '--mapping'    && args[i+1]) mappingFile   = args[i+1];
        if (args[i] === '--rows'       && args[i+1]) {
            const m = args[i+1].match(/^(\d+)-(\d+)$/);
            if (m) { rowStart = parseInt(m[1]); rowEnd = parseInt(m[2]); }
        }
    }

    if (!spreadsheetId || !sheetName || !rowStart || !rowEnd) {
        console.error('使い方: node run_form_session.js --sheets <ID> --sheet-name <NAME> --rows <START>-<END>');
        console.error('例:    node run_form_session.js --sheets 1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk --sheet-name 260325test --rows 2-3');
        process.exit(1);
    }

    const profilePath = path.join(__dirname, profileFile);
    const mappingPath = path.join(__dirname, mappingFile);
    if (!fs.existsSync(profilePath)) { console.error(`❌ ${profileFile} が見つかりません`); process.exit(1); }
    if (!fs.existsSync(mappingPath)) { console.error(`❌ ${mappingFile} が見つかりません`); process.exit(1); }

    const baseProfile = JSON.parse(fs.readFileSync(profilePath, 'utf-8'));
    const mapping     = JSON.parse(fs.readFileSync(mappingPath, 'utf-8'));

    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📋 フォーム入力セッション開始');
    console.log(`   スプレッドシート: ${spreadsheetId}`);
    console.log(`   シート名:         ${sheetName}`);
    console.log(`   対象行:           ${rowStart}〜${rowEnd}`);
    console.log(`   プロファイル:     ${profileFile}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    // Google Sheets 読み込み
    const sheetsClient = await getGoogleSheetsClient();
    const { headers, rows } = await readSheet(sheetsClient, spreadsheetId, sheetName);

    const colIdx     = (name) => headers.indexOf(name);
    const urlCol     = colIdx('問い合わせフォームURL');
    const dateCol    = colIdx('送信日');
    const statusCol  = colIdx('送信○×');
    const reasonCol  = colIdx('送信不可理由');
    const companyCol = colIdx('企業名');
    const repCol     = colIdx('代表者名');

    if (urlCol < 0) { console.error('❌ 列「問い合わせフォームURL」が見つかりません'); process.exit(1); }

    // ── 対象行を絞り込む（rowStart〜rowEnd, 1-indexed シート行） ──────────
    // rows配列は 0-indexed、シート行は header=1なので data行=i+2
    const targets = [];
    for (let i = 0; i < rows.length; i++) {
        const sheetRow = i + 2; // 1=header
        if (sheetRow < rowStart || sheetRow > rowEnd) continue;

        const row        = rows[i];
        const formUrl    = urlCol   >= 0 ? (row[urlCol]    || '').trim() : '';
        const dateVal    = dateCol  >= 0 ? (row[dateCol]   || '').trim() : '';
        const reasonVal  = reasonCol >= 0 ? (row[reasonCol] || '').trim() : '';
        const companyName = companyCol >= 0 ? (row[companyCol] || '') : '';
        const repName     = repCol     >= 0 ? (row[repCol]     || '') : '';

        // ── スキップ判定 ──
        if (dateVal) {
            console.log(`⏭️  行${sheetRow}「${companyName}」送信日(${dateVal})が入力済み → スキップ`);
            continue;
        }
        if (SKIP_KEYWORDS_IN_REASON_COL.some(kw => reasonVal.includes(kw))) {
            console.log(`⏭️  行${sheetRow}「${companyName}」送信不可理由に「${reasonVal}」あり → スキップ`);
            continue;
        }
        if (!formUrl || !formUrl.startsWith('http')) {
            console.log(`⏭️  行${sheetRow}「${companyName}」フォームURLなし → スキップ`);
            continue;
        }

        targets.push({ sheetRow, formUrl, companyName, repName, row });
    }

    if (targets.length === 0) {
        console.log('✅ 対象行がありません（すべてスキップ対象でした）');
        return;
    }

    console.log(`\n📌 入力対象: ${targets.length}件\n`);

    // ── スクリーンショットフォルダ作成 ──────────────────────────────────────
    const screenshotsDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotsDir)) fs.mkdirSync(screenshotsDir);

    // ── ブラウザ起動 ──────────────────────────────────────────────────────────
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();

    // ── 1件ずつ処理 ──────────────────────────────────────────────────────────
    const results = [];

    for (const target of targets) {
        const { sheetRow, formUrl, companyName, repName } = target;

        console.log(`\n${'─'.repeat(60)}`);
        console.log(`📝 行${sheetRow}: ${companyName} (${repName || '代表者名不明'})`);
        console.log(`🔗 URL: ${formUrl}`);
        console.log(`${'─'.repeat(60)}`);

        // プロファイルをパーソナライズ
        const profile = buildPersonalizedProfile(baseProfile, { company: companyName, rep_name: repName });

        const page = await context.newPage();
        const result = await fillFormOnly(page, formUrl, profile, mapping, sheetRow, companyName, isAllFields, screenshotsDir);

        if (result.skipped) {
            console.log(`⏭️  スキップ: ${result.reason}`);
            await page.close();
            results.push({ sheetRow, status: '×', reason: result.reason });
            continue;
        }

        // ── 入力完了 → ユーザーへ指示 ────────────────────────────────────────
        console.log('\n');
        console.log('╔════════════════════════════════════════════════════════╗');
        console.log('║  ✅ 入力が完了しました！                               ║');
        console.log('║                                                        ║');
        console.log('║  ブラウザを確認して、送信ボタンを押してください。      ║');
        console.log('║  ※ 送信後、このターミナルに戻って Enter を押すと      ║');
        console.log('║     次の行に進みます。                                 ║');
        console.log('╚════════════════════════════════════════════════════════╝');
        console.log('');

        const userAnswer = await promptUser('  → 送信しましたか？ [y=送信済み / n=送信しなかった / s=スキップ]: ');

        let finalStatus, finalReason;
        if (userAnswer === 'y') {
            finalStatus = '〇';
            finalReason = '';
            // シートの送信日を今日の日付で更新
            const today = new Date().toLocaleDateString('ja-JP', { year:'numeric', month:'2-digit', day:'2-digit' }).replace(/\//g, '/');
            await updateSheetRow(sheetsClient, spreadsheetId, sheetName, sheetRow, {
                statusCol, reasonCol, dateCol,
                status: '〇', reason: '', date: today
            });
            console.log(`   ✅ シート行${sheetRow}を更新しました（送信日: ${today}）`);
        } else if (userAnswer === 'n') {
            finalStatus = '×';
            finalReason = 'ユーザーが送信しなかった';
            console.log(`   ❌ 送信なし。送信不可として記録します。`);
        } else {
            finalStatus = '未';
            finalReason = 'スキップ';
            console.log(`   ⏭️  スキップ`);
        }

        results.push({ sheetRow, status: finalStatus, reason: finalReason });
        await page.close();
    }

    await browser.close();

    // ── 最終サマリー ─────────────────────────────────────────────────────────
    console.log('\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📊 セッション完了サマリー');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    for (const r of results) {
        const icon = r.status === '〇' ? '✅' : r.status === '×' ? '❌' : '⏭️ ';
        console.log(`  ${icon} 行${r.sheetRow}: ${r.status} ${r.reason ? '(' + r.reason + ')' : ''}`);
    }
    console.log('');
}

// ── フォームを入力するだけ（送信はしない） ───────────────────────────────────
async function fillFormOnly(page, url, profile, mapping, idString, companyName, isAllFields, screenshotsDir) {
    try {
        console.log(`  ⏳ ページを開いています...`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);

        // ── 営業NGチェック ──
        const pageText = await page.evaluate(() => document.body.textContent || '');
        for (const kw of SALES_NG_KEYWORDS) {
            if (pageText.includes(kw)) {
                return { skipped: true, reason: `営業お断り記載あり（${kw}）` };
            }
        }

        // ── フォームフィールドを解析 ──
        const fieldsData = await page.evaluate(() => {
            const inputs = Array.from(document.querySelectorAll(
                'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="image"]), textarea, select'
            ));
            return inputs.map(el => {
                let labelText = '';
                if (el.labels && el.labels.length > 0) labelText = el.labels[0].innerText || el.labels[0].textContent;
                if (!labelText && el.getAttribute('aria-label')) labelText = el.getAttribute('aria-label');
                if (!labelText && el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) labelText = label.innerText || label.textContent;
                }
                if (!labelText && el.getAttribute('placeholder')) labelText = el.getAttribute('placeholder');
                let parentForReq = el.closest('td, th, div, p, li, label, dd');
                if (!labelText && parentForReq) {
                    labelText = (parentForReq.innerText || parentForReq.textContent || '').substring(0, 100);
                }
                let isRequired = false;
                if (el.required || el.getAttribute('aria-required') === 'true' || el.hasAttribute('required')) isRequired = true;
                const classString = (el.className || '') + (el.labels && el.labels.length > 0 ? ' ' + el.labels[0].className : '');
                if (classString.toLowerCase().includes('required') || classString.toLowerCase().includes('hissu')) isRequired = true;
                if (!isRequired) {
                    const widerParent = el.closest('tr, li, dl, .form-group, .row') || parentForReq;
                    if (widerParent) {
                        const tc = widerParent.innerText || widerParent.textContent || '';
                        if (tc.includes('必須') || tc.toLowerCase().includes('required')) isRequired = true;
                    }
                }
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
                    id: el.id, name: el.getAttribute('name') || '',
                    type: el.type || el.tagName.toLowerCase(),
                    tagName: el.tagName.toLowerCase(),
                    labelText: (labelText || '').trim().replace(/\s+/g, ' '),
                    xpath: getXPath(el), isRequired
                };
            });
        });

        // ── マッピングエントリをキーワード長の降順でソート ──
        const mappingEntries = Object.entries(mapping).sort((a, b) => {
            const maxLenA = Math.max(...a[1].map(k => k.length));
            const maxLenB = Math.max(...b[1].map(k => k.length));
            return maxLenB - maxLenA;
        });

        let filledCount = 0;
        for (const field of fieldsData) {
            let matchedKey = null;
            const textToMatch = `${field.labelText} ${field.name}`.toLowerCase();

            // チェックボックス・ラジオの同意系は自動チェック
            if (field.type === 'checkbox' || field.type === 'radio') {
                const autoTriggers = ['同意', '規約', '確認', '個人情報', 'プライバシー', '契約', '合意'];
                if (autoTriggers.some(kw => textToMatch.includes(kw))) {
                    try {
                        const sel = field.name ? `[name="${field.name}"]` : `xpath=${field.xpath}`;
                        await page.locator(sel).first().check({ timeout: 2000 });
                        console.log(`  ☑️  同意チェック: ${field.labelText || field.name}`);
                    } catch(e) {}
                    continue;
                }
            }

            // フィールドにマッチするキー検索
            outerLoop:
            for (const [key, keywords] of mappingEntries) {
                for (const keyword of keywords) {
                    if (textToMatch.includes(keyword.toLowerCase())) {
                        matchedKey = key;
                        break outerLoop;
                    }
                }
            }

            if (matchedKey && profile[matchedKey] !== undefined) {
                // 姓名・フリガナ・電話・郵便番号の分割処理
                if (matchedKey === 'name') {
                    if (field.name.match(/sei|last|1/i) || field.id.match(/sei|last|1/i)) matchedKey = 'name_sei';
                    else if (field.name.match(/mei|first|2/i) || field.id.match(/mei|first|2/i)) matchedKey = 'name_mei';
                } else if (matchedKey === 'kana') {
                    if (field.name.match(/sei|last|1/i) || field.id.match(/sei|last|1/i)) matchedKey = 'kana_sei';
                    else if (field.name.match(/mei|first|2/i) || field.id.match(/mei|first|2/i)) matchedKey = 'kana_mei';
                } else if (matchedKey === 'phone') {
                    if (field.name.match(/1|first/i) || field.id.match(/1|first/i)) matchedKey = 'phone_1';
                    else if (field.name.match(/2|mid/i)   || field.id.match(/2|mid/i))   matchedKey = 'phone_2';
                    else if (field.name.match(/3|last/i)  || field.id.match(/3|last/i))  matchedKey = 'phone_3';
                } else if (matchedKey === 'zipcode') {
                    if (field.name.match(/1|first/i) || field.id.match(/1|first/i)) matchedKey = 'zipcode_1';
                    else if (field.name.match(/2|last/i)  || field.id.match(/2|last/i))  matchedKey = 'zipcode_2';
                }

                const alwaysFill = ['message', 'subject'];
                if (!isAllFields && !field.isRequired && !alwaysFill.includes(matchedKey)) {
                    console.log(`  ⬜ スキップ（任意）: ${field.labelText || field.name} → ${matchedKey}`);
                    continue;
                }

                let fillVal = String(profile[matchedKey]);
                // ひらがな・ふりがなの指定があれば変換
                const lbl = (field.labelText || '').toLowerCase();
                const nm = (field.name || '').toLowerCase();
                if (lbl.includes('ひらがな') || lbl.includes('ふりがな') || nm.includes('hiragana')) {
                    fillVal = katakanaToHiragana(fillVal);
                }

                const valStr = fillVal.substring(0, 40);
                console.log(`  ✏️  入力: "${field.labelText || field.name}" → ${matchedKey} = "${valStr}"`);
                try {
                    const sel = field.name ? `[name="${field.name}"]` : `xpath=${field.xpath}`;
                    const locator = page.locator(sel).first();

                    if (field.tagName === 'select') {
                        let selected = false;
                        if (profile[matchedKey]) {
                            try { await locator.selectOption({ label: profile[matchedKey] }, { timeout: 1000 }); selected = true; } catch(e) {}
                        }
                        if (!selected) {
                            const optionsText = await locator.evaluate(el => Array.from(el.options).map(o => o.text));
                            let prefs;
                            if (matchedKey === 'preferred_contact') prefs = ['メール', 'メールでの応答', 'e-mail', 'email'];
                            else if (matchedKey === 'preferred_time') prefs = ['いつでも', '不問', '午前', '午後'];
                            else prefs = ['協業', '業務提携', 'アライアンス', 'パートナー', '提案', 'ビジネス', 'その他', 'その他のお問い合わせ'];
                            for (const pref of prefs) {
                                const match = optionsText.find(opt => opt.includes(pref));
                                if (match) {
                                    if (match.includes('営業') && matchedKey !== 'preferred_contact') break;
                                    await locator.selectOption({ label: match }, { timeout: 1000 });
                                    console.log(`     → 選択: ${match}`);
                                    selected = true;
                                    break;
                                }
                            }
                        }
                    } else if (field.type === 'radio') {
                        const radioGroup = page.locator(`input[type="radio"][name="${field.name}"]`);
                        const count = await radioGroup.count();
                        let clicked = false;
                        let prefs;
                        if (matchedKey === 'preferred_contact') prefs = ['メール', 'e-mail', 'email', 'メールアドレス'];
                        else if (matchedKey === 'preferred_time') prefs = ['いつでも', '不問', '午前', '午後'];
                        else prefs = ['協業', '業務提携', 'アライアンス', 'パートナー', '提案', 'ビジネス', 'その他', 'その他のお問い合わせ'];
                        for (const pref of prefs) {
                            for (let ri = 0; ri < count; ri++) {
                                const r = radioGroup.nth(ri);
                                let labelText = await r.getAttribute('value') || '';
                                const id = await r.getAttribute('id');
                                if (id) {
                                    const lbl = await page.locator(`label[for="${id}"]`).textContent().catch(() => '');
                                    labelText += ' ' + lbl;
                                }
                                if (labelText.includes(pref)) {
                                    await r.check({ timeout: 1000 });
                                    console.log(`     → ラジオ選択: ${pref}`);
                                    clicked = true;
                                    break;
                                }
                            }
                            if (clicked) break;
                        }
                    } else if (field.type !== 'checkbox') {
                        await locator.fill(String(profile[matchedKey]), { timeout: 3000 });
                        filledCount++;
                    }
                } catch(e) {
                    console.log(`     ⚠️  入力失敗: ${e.message.substring(0, 60)}`);
                }
            } else if (field.name && !['submit','button','image','hidden','reset'].includes(field.type)) {
                console.log(`  ❓ 未マッチ: type:${field.type} name:"${field.name}" label:"${field.labelText}"`);
            }
        }

        // スクリーンショット（入力後・送信前）
        await page.evaluate(() => window.scrollTo(0, 0));
        const shotPath = path.join(screenshotsDir, `filled_row_${idString}.png`);
        await page.screenshot({ path: shotPath, fullPage: true });
        console.log(`\n  📸 スクリーンショット保存: ${shotPath}`);
        console.log(`  📝 入力フィールド数: ${filledCount}件`);

        return { skipped: false };

    } catch(e) {
        console.error(`  ❌ エラー: ${e.message}`);
        return { skipped: true, reason: 'エラー: ' + e.message.substring(0, 50) };
    }
}

// ── カタカナをひらがなに変換 ──────────────────────────────────────────────
function katakanaToHiragana(src) {
    if (!src) return '';
    return src.replace(/[\u30a1-\u30f6]/g, function(match) {
        var chr = match.charCodeAt(0) - 0x60;
        return String.fromCharCode(chr);
    });
}

// ── プロファイルをパーソナライズ ──────────────────────────────────────────────
function buildPersonalizedProfile(base, rowData) {
    const p = Object.assign({}, base);
    // メッセージ内のプレースホルダー置換
    if (p.message) {
        p.message = p.message
            .replace(/\{\{company\}\}/g, rowData.company || '')
            .replace(/\{\{rep_name\}\}/g,  rowData.rep_name  || '')
            .replace(/代表取締役\s*ご担当者/g, 'ご担当者')
            .replace(/代表取締役\s*担当者/g, 'ご担当者');
    }

    // 姓名分割
    if (p.name) {
        const parts = p.name.trim().split(/\s+/);
        p.name_sei = parts[0] || '';
        p.name_mei = parts.slice(1).join(' ') || '';
    }
    // フリガナ分割
    if (p.kana) {
        const parts = p.kana.trim().split(/\s+/);
        p.kana_sei = parts[0] || '';
        p.kana_mei = parts.slice(1).join(' ') || '';
    }
    // 電話番号分割
    if (p.phone) {
        const parts = p.phone.split('-');
        p.phone_1 = parts[0] || '';
        p.phone_2 = parts[1] || '';
        p.phone_3 = parts[2] || '';
    }
    // 郵便番号（住所から抽出）
    if (p.address) {
        const zipMatch = p.address.match(/(\d{3})[-ー](\d{4})/);
        if (zipMatch) {
            p.zipcode   = zipMatch[1] + '-' + zipMatch[2];
            p.zipcode_1 = zipMatch[1];
            p.zipcode_2 = zipMatch[2];
            p.address   = p.address.replace(/〒?\s*\d{3}[-ー]\d{4}\s*/, '').trim();
        }
    }
    return p;
}

// ── ユーザー入力待ち ──────────────────────────────────────────────────────────
function promptUser(question) {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    return new Promise(resolve => {
        rl.question(question, answer => {
            rl.close();
            resolve(answer.trim().toLowerCase());
        });
    });
}

// ── Google Sheets API ──────────────────────────────────────────────────────────
async function getGoogleSheetsClient() {
    const credPath = path.join(__dirname, 'google_credentials.json');
    if (!fs.existsSync(credPath)) {
        console.error('❌ google_credentials.json が見つかりません（SHEETS_API_SETUP.md を参照）');
        process.exit(1);
    }
    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    return google.sheets({ version: 'v4', auth });
}

async function readSheet(sheets, spreadsheetId, sheetName) {
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range: `'${sheetName}'`,
    });
    const values = response.data.values || [];
    if (values.length === 0) return { headers: [], rows: [] };
    const headers = values[0];
    const rows    = values.slice(1);
    console.log(`  📊 シート読み込み完了: ${rows.length}行 / ${headers.length}列`);
    return { headers, rows };
}

async function updateSheetRow(sheets, spreadsheetId, sheetName, rowNum, { statusCol, reasonCol, dateCol, status, reason, date }) {
    const colLetter = (idx) => {
        let result = '';
        idx += 1;
        while (idx > 0) {
            result = String.fromCharCode(65 + ((idx - 1) % 26)) + result;
            idx = Math.floor((idx - 1) / 26);
        }
        return result;
    };
    const updates = [];
    if (statusCol >= 0) updates.push({ range: `'${sheetName}'!${colLetter(statusCol)}${rowNum}`, values: [[status]] });
    if (reasonCol >= 0) updates.push({ range: `'${sheetName}'!${colLetter(reasonCol)}${rowNum}`, values: [[reason]] });
    if (dateCol   >= 0) updates.push({ range: `'${sheetName}'!${colLetter(dateCol)}${rowNum}`,   values: [[date]] });
    if (updates.length > 0) {
        await sheets.spreadsheets.values.batchUpdate({
            spreadsheetId,
            requestBody: { valueInputOption: 'USER_ENTERED', data: updates },
        });
    }
}

main().catch(err => {
    console.error('\n❌ Fatal error:', err.message);
    process.exit(1);
});
