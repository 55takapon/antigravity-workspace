/**
 * fix_osaka_sheet.js - 既存シートの品質修正 & 最終チェック報告
 * v1.3.0 - 3重チェック体制
 */

const { getGoogleSheetsClient } = require('./sheets_writer');
const { isValidCompanyName, isJapanesePersonName, cleanRepresentativeName, cleanCompanyName, isNGIndustry } = require('./crawler');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

let SHEET_NAME = 'Webマーケティング'; // デフォルト

// コマンドライン引数からシート名を取得
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--sheet' && args[i + 1]) {
        SHEET_NAME = args[i + 1];
    }
}

// ═══════════════════════════════════════════
//  バリデーションユーティリティ
// ═══════════════════════════════════════════
// 代表者名バリデーション（cleanRepresentativeNameでクリーニング→人名判定）
// 戻り値: { valid: boolean, cleaned: string }
function validateRepName(name) {
    if (!name || name === 'ご担当者') return { valid: true, cleaned: name };
    const cleaned = cleanRepresentativeName(name);
    if (cleaned && cleaned !== name) {
        // ゴミ除去後に有効な人名が残った → クリーン済みで更新
        return { valid: false, cleaned: cleaned };
    }
    if (!cleaned) {
        // 人名ではない → ご担当者に修正
        return { valid: false, cleaned: 'ご担当者' };
    }
    // そのままOK
    return { valid: true, cleaned: name };
}

function normalizeCoreName(name) {
    if (!name) return '';
    return name
        .replace(/株式会社|合同会社|有限会社/g, '')
        .replace(/[Ａ-Ｚａ-ｚ０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
        .replace(/　/g, ' ').replace(/＆/g, '&')
        .toLowerCase().replace(/[\s・\-_.&]/g, '').trim();
}

function normalizeDomain(url) {
    if (!url) return '';
    try {
        const u = new URL(url);
        return u.hostname.replace(/^(www|corp|en|ja|jp|info)\./i, '').toLowerCase();
    } catch { return ''; }
}

// ═══════════════════════════════════════════
//  チェック層1: 企業名-URL整合性チェック
//  URLが第三者サイト（ポータル・求人・ニュース等）の場合、
//  記載された企業名は信頼できない → 削除
// ═══════════════════════════════════════════
const THIRD_PARTY_DOMAINS = [
    'lancers', 'crowdworks', 'coconala',          // クラウドソーシング
    'mynavi', 'doda', 'en-ambi', 'rikunabi',      // 求人
    'hellowork', 'indeed', 'wantedly',            // 求人
    'prtimes', 'atpress', 'news.livedoor',        // ニュース・PR
    'bizresearch', 'comperu', 'proni',             // 比較・ランキング
    'freelance-meikan', 'feedbook',               // フリーランス・ポータル
    'digikar.m3', 'marketimes',                   // メディア
    'line.me',                                    // LINE
];

function isThirdPartyUrl(url) {
    if (!url) return false;
    const domain = normalizeDomain(url);
    return THIRD_PARTY_DOMAINS.some(tp => domain.includes(tp));
}

// ═══════════════════════════════════════════
//  チェック層2: 大手企業除外
//  従業員20名以下のリストに入るべきでない企業
// ═══════════════════════════════════════════
const LARGE_CORP_NAMES = [
    'KDDI', 'NTT', 'ソフトバンク', 'docomo', 'au',
    'GMO', 'サイバーエージェント', 'リクルート', '楽天',
    'Yahoo', 'LINE', 'メルカリ', 'トヨタ', 'ソニー',
    'transcosmos', 'トランスコスモス',
    '博報堂', 'Hakuhodo', '電通', 'ADK',
    '日本ハム', '大阪ガス', 'ぐるなび',
];

function isLargeCorporation(name) {
    if (!name) return false;
    const lower = name.toLowerCase();
    return LARGE_CORP_NAMES.some(corp => lower.includes(corp.toLowerCase()));
}

// ═══════════════════════════════════════════
//  チェック層3: フォームURL妥当性チェック
// ═══════════════════════════════════════════
const INVALID_FORM_DOMAINS = [
    'line.me', 'twitter.com', 'x.com', 'facebook.com',
    'instagram.com', 'youtube.com', 'linkedin.com',
    'amazon.co.jp', 'google.com',
];

function isInvalidFormUrl(url) {
    if (!url) return false;
    if (/^javascript:/i.test(url) || /^mailto:/i.test(url) || /^tel:/i.test(url)) return true;
    try {
        const domain = normalizeDomain(url);
        return INVALID_FORM_DOMAINS.some(d => domain.includes(d));
    } catch {
        return true;
    }
}

// ═══════════════════════════════════════════
//  メイン処理
// ═══════════════════════════════════════════

async function main() {
    console.log('========================================');
    console.log('  大阪シート 品質修正ツール v1.3.0');
    console.log('  3重チェック体制');
    console.log(`  対象シート: ${SHEET_NAME}`);
    console.log('========================================\n');

    const sheets = await getGoogleSheetsClient();
    console.log('[接続] Google Sheets 接続完了\n');

    // 1. 全データ読み取り
    console.log('--- STEP 1: データ読み取り ---');
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    if (allRows.length <= 1) { console.log('データなし'); return; }

    const headerRow = allRows[0];
    const dataRows = allRows.slice(1);
    console.log(`[読取] ヘッダー: ${headerRow.join(' | ')}`);
    console.log(`[読取] データ行: ${dataRows.length}件\n`);

    const CI = { name: 2, rep: 3, url: 4, form: 5, emp: 9 };

    // 2. 3重チェック
    console.log('--- STEP 2: 3重チェック ---\n');
    const issues = [];
    const deleteRows = new Set();
    const fixRows = {};
    const seenDomains = new Map();
    const seenNormNames = new Map();

    for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i];
        const rowNum = i + 2;
        const rawName = (row[CI.name] || '').trim();
        // ★ v1.4.0: cleanCompanyNameを事前適用してから判定する
        //   「株式会社note様」等の敬称付き・ゴミ付き名前を先に除去してから検証する
        const name = cleanCompanyName(rawName) || rawName;
        const rep = (row[CI.rep] || '').trim();
        const url = (row[CI.url] || '').trim();
        const form = (row[CI.form] || '').trim();
        const emp = (row[CI.emp] || '').trim();
        const domain = normalizeDomain(url);
        const normName = normalizeCoreName(name);

        // ─── チェック層1: 企業名バリデーション（cleanCompanyName適用後の名前で判定）───
        if (!name || !isValidCompanyName(name)) {
            issues.push({ row: rowNum, type: '企業名無効', detail: `"${rawName}"${rawName !== name ? ` → clean:"${name}"` : ''}`, action: '削除' });
            deleteRows.add(i); continue;
        }
        // cleanCompanyNameで名前が変わった場合は修正としてシートを更新
        if (rawName !== name) {
            issues.push({ row: rowNum, type: '企業名クリーニング', detail: `"${rawName}" → "${name}"`, action: '修正' });
            if (!fixRows[i]) fixRows[i] = {};
            fixRows[i][CI.name] = name;
        }

        // ─── チェック層1.5: NG業種除外 ───
        const ngCheck = isNGIndustry(name);
        if (ngCheck.blocked) {
            issues.push({ row: rowNum, type: 'NG業種', detail: `"${name}" (${ngCheck.reason})`, action: '削除' });
            deleteRows.add(i); continue;
        }

        // ─── チェック層2: URL-企業名整合性 ───
        if (isThirdPartyUrl(url)) {
            issues.push({ row: rowNum, type: 'URL不整合', detail: `"${name}" のURL ${domain} は第三者サイト`, action: '削除' });
            deleteRows.add(i); continue;
        }

        // ─── チェック層3: 大手企業除外 ───
        if (isLargeCorporation(name)) {
            issues.push({ row: rowNum, type: '大手企業', detail: `"${name}" はターゲット外（大手）`, action: '削除' });
            deleteRows.add(i); continue;
        }

        // ─── チェック層4: 不自然な間借りドメイン除外 ───
        const INVALID_DOMAINS = ['hp.f-creation.co.jp', 'f-creation.co.jp'];
        if (domain) {
            if (INVALID_DOMAINS.includes(domain) || domain.startsWith('hp.')) {
                issues.push({ row: rowNum, type: 'URL乖離', detail: `"${name}" に対し ${domain} は不自然（間借り等）`, action: '削除' });
                deleteRows.add(i); continue;
            }
        }

        // ─── ドメイン重複チェック ───
        if (domain && seenDomains.has(domain)) {
            issues.push({ row: rowNum, type: 'ドメイン重複', detail: `"${name}" (${domain}) 行${seenDomains.get(domain)}と重複`, action: '削除' });
            deleteRows.add(i); continue;
        }
        if (domain) seenDomains.set(domain, rowNum);

        // ─── 企業名重複（正規化+部分一致） ───
        if (normName && normName.length >= 2 && seenNormNames.has(normName)) {
            issues.push({ row: rowNum, type: '名前重複', detail: `"${name}" 行${seenNormNames.get(normName)}と重複`, action: '削除' });
            deleteRows.add(i); continue;
        }
        let partialDup = false;
        if (normName && normName.length >= 3) {
            for (const [existing, existNo] of seenNormNames) {
                if (existing.length >= 3 && (normName.includes(existing) || existing.includes(normName))) {
                    issues.push({ row: rowNum, type: '部分一致', detail: `"${name}" 行${existNo}と部分一致`, action: '削除' });
                    deleteRows.add(i); partialDup = true; break;
                }
            }
        }
        if (partialDup) continue;
        if (normName && normName.length >= 2) seenNormNames.set(normName, rowNum);

        // ─── 代表者名チェック（cleanRepresentativeName→人名判定） ───
        if (rep && rep !== 'ご担当者') {
            const result = validateRepName(rep);
            if (!result.valid) {
                issues.push({ row: rowNum, type: '代表者名修正', detail: `"${rep}" → "${result.cleaned}"`, action: '修正' });
                if (!fixRows[i]) fixRows[i] = {};
                fixRows[i][CI.rep] = result.cleaned;
            }
        }

        // ─── フォームURL妥当性・必須チェック ───
        if (!form) {
            issues.push({ row: rowNum, type: 'フォームなし', detail: `"${name}" 問い合わせURLなしは無意味`, action: '削除' });
            deleteRows.add(i); continue;
        }
        if (form && isInvalidFormUrl(form)) {
            issues.push({ row: rowNum, type: 'フォーム不正', detail: `${form} はフォームではない`, action: '削除' });
            deleteRows.add(i); continue;
        }

        // ─── 従業員数記録 ───
        if (!emp || emp === '不明' || emp === 'null') {
            issues.push({ row: rowNum, type: '従業員数不明', detail: `"${name}"`, action: '記録のみ' });
        }
    }

    // 問題サマリー
    const issuesByType = {};
    for (const issue of issues) {
        if (!issuesByType[issue.type]) issuesByType[issue.type] = [];
        issuesByType[issue.type].push(issue);
    }

    console.log('┌──────────────────────────────────────┐');
    console.log('│      3重チェック結果                   │');
    console.log('├──────────────────────────────────────┤');
    for (const [type, typeIssues] of Object.entries(issuesByType)) {
        const actions = {};
        for (const i of typeIssues) { actions[i.action] = (actions[i.action] || 0) + 1; }
        const actStr = Object.entries(actions).map(([a, c]) => `${a}:${c}`).join(', ');
        console.log(`│  ${type}: ${typeIssues.length}件 (${actStr})`);
    }
    console.log(`│  ──────────────────────────────────`);
    console.log(`│  削除: ${deleteRows.size}件  修正: ${Object.keys(fixRows).length}件`);
    console.log('└──────────────────────────────────────┘\n');

    if (issues.filter(i => i.action !== '記録のみ').length > 0) {
        console.log('[問題詳細]');
        for (const issue of issues) {
            if (issue.action === '記録のみ') continue;
            const icon = issue.action === '削除' ? '🗑️' : '🔧';
            console.log(`  ${icon} [${issue.type}] ${issue.detail}`);
        }
        console.log('');
    }

    // 3. 修正実行
    if (deleteRows.size > 0 || Object.keys(fixRows).length > 0) {
        console.log('--- STEP 3: シート修正実行 ---\n');
        // 修正
        for (const [rowIdxStr, fixes] of Object.entries(fixRows)) {
            const rowIdx = parseInt(rowIdxStr);
            if (deleteRows.has(rowIdx)) continue;
            const sheetRow = rowIdx + 2;
            for (const [col, value] of Object.entries(fixes)) {
                const colLetter = String.fromCharCode(65 + parseInt(col));
                const cell = `${SHEET_NAME}!${colLetter}${sheetRow}`;
                await sheets.spreadsheets.values.update({
                    spreadsheetId: SPREADSHEET_ID,
                    range: cell,
                    valueInputOption: 'USER_ENTERED',
                    requestBody: { values: [[value]] },
                });
                console.log(`  [修正] ${cell} = "${value}"`);
            }
        }
        // 削除
        if (deleteRows.size > 0) {
            const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
            const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
            const sheetId = sheet.properties.sheetId;
            const sorted = [...deleteRows].sort((a, b) => b - a);
            await sheets.spreadsheets.batchUpdate({
                spreadsheetId: SPREADSHEET_ID,
                requestBody: {
                    requests: sorted.map(idx => ({
                        deleteDimension: { range: { sheetId, dimension: 'ROWS', startIndex: idx + 1, endIndex: idx + 2 } },
                    })),
                },
            });
            console.log(`  [削除] ${deleteRows.size}行を削除完了`);
        }
        console.log('');
    }

    // 4. 最終チェック
    console.log('--- STEP 4: 最終品質チェック ---\n');
    const final = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: SHEET_NAME });
    const finalData = final.data.values.slice(1);
    let fIssues = 0;
    const fDomains = new Set(), fNames = new Set();
    let empK = 0, empU = 0, repK = 0, repD = 0, formF = 0, formM = 0;
    const fInvalid = [], fDups = [], fThirdParty = [], fLarge = [], fBadRep = [];

    for (const row of finalData) {
        const nm = (row[CI.name] || '').trim();
        const rp = (row[CI.rep] || '').trim();
        const ur = (row[CI.url] || '').trim();
        const fm = (row[CI.form] || '').trim();
        const em = (row[CI.emp] || '').trim();
        const dm = normalizeDomain(ur);
        const nn = normalizeCoreName(nm);

        if (nm && !isValidCompanyName(nm)) { fInvalid.push(nm); fIssues++; }
        if (isThirdPartyUrl(ur)) { fThirdParty.push(`${nm} (${dm})`); fIssues++; }
        if (isLargeCorporation(nm)) { fLarge.push(nm); fIssues++; }
        if (dm && fDomains.has(dm)) { fDups.push(`${nm} (${dm})`); fIssues++; }
        fDomains.add(dm);
        if (nn && nn.length >= 2 && fNames.has(nn)) { fDups.push(`${nm} (名前)`); fIssues++; }
        fNames.add(nn);
        if (rp && rp !== 'ご担当者' && !isJapanesePersonName(rp)) { fBadRep.push(rp); fIssues++; }

        if (em && em !== '不明' && em !== 'null') empK++; else empU++;
        if (rp && rp !== 'ご担当者') repK++; else repD++;
        if (fm) formF++; else formM++;
    }

    console.log('┌───────────────────────────────────────────┐');
    console.log('│      最終品質チェック結果（必須報告）       │');
    console.log('├───────────────────────────────────────────┤');
    console.log(`│  修正前: ${dataRows.length}件 → 修正後: ${finalData.length}件 (${dataRows.length - finalData.length}件削除)`);
    console.log('│');
    console.log(`│  [企業名]     有効: ${finalData.length - fInvalid.length} / 無効: ${fInvalid.length}`);
    console.log(`│  [URL整合性]  第三者URL: ${fThirdParty.length}件`);
    console.log(`│  [大手企業]   混入: ${fLarge.length}件`);
    console.log(`│  [重複]       ${fDups.length}件`);
    console.log(`│  [代表者名]   フルネーム: ${repK} / ご担当者: ${repD} / 不正: ${fBadRep.length}`);
    console.log(`│  [従業員数]   取得: ${empK} / 不明: ${empU}`);
    console.log(`│  [フォーム]   検出: ${formF} / 未検出: ${formM}`);
    console.log(`│  [残存問題]   ${fIssues}件`);
    console.log('└───────────────────────────────────────────┘');

    if (fIssues === 0) console.log('\n✅ 品質チェック完了 — 問題なし');
    else console.log(`\n⚠️ 品質チェック完了 — ${fIssues}件の残存問題あり`);
    console.log(`\n  シートURL: https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit`);
    console.log('\n========================================');
    console.log('  完了');
    console.log('========================================');
}

main().catch(err => { console.error('Fatal error:', err); process.exit(1); });
