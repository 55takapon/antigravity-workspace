/**
 * schema.js - 全スクリプトの唯一の列定義とユーティリティ
 *
 * 【設計原則】
 * - 列インデックスのハードコードを排除する
 * - ドメイン正規化ロジックを一箇所に集約する
 * - 全スクリプトはこのファイルを require() して列を参照する
 *
 * ※ このファイルを変更する場合は、全スクリプトへの影響を確認すること
 */

'use strict';

const path = require('path');
const fs = require('fs');

// ═══════════════════════════════════════════
//  スプレッドシート定義
// ═══════════════════════════════════════════

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

const TARGET_SHEETS = [
    'Webマーケティング',
    'Webマーケティング_名古屋',
    'クリニック専門支援',
    'Web奉行',
];

// ═══════════════════════════════════════════
//  列定義（0始まり）
// ═══════════════════════════════════════════

const COL = {
    NO:             0,  // A: №
    AREA:           1,  // B: エリア
    COMPANY_NAME:   2,  // C: 企業名
    REPRESENTATIVE: 3,  // D: 代表者名
    URL:            4,  // E: URL
    FORM_URL:       5,  // F: 問い合わせフォームURL
    SEND_DATE:      6,  // G: 送信日
    SEND_STATUS:    7,  // H: 送信○×
    REJECT_REASON:  8,  // I: 送信不可理由
    EMPLOYEES:      9,  // J: 従業員数
    CAPITAL:       10,  // K: 資本金
    KW_HIT:        11,  // L: キーワードHIT
    HIT_DETAIL:    12,  // M: HIT詳細
    RETRIEVED_AT:  13,  // N: 取得日時
    CATEGORY:      14,  // O: 種類（web_production/hybrid/web_marketing/業種違い）
    SOURCE:        15,  // P: シード元（Web奉行/PRONIアイミツ等）
};

// ═══════════════════════════════════════════
//  NG理由プレフィックス
// ═══════════════════════════════════════════

const NG_PREFIX = {
    STATIC:   '【静的NG】',  // apply_auto_reject.js が書き込む
    DYNAMIC:  '【動的NG】',  // check_ng_forms.js が書き込む
    MANUAL:   '【手動承認】', // 人間が「NGではない」と判断した場合に入力
};

// レガシープレフィックス（旧 company_search/ のスクリプトが書き込んだもの）
const LEGACY_PREFIXES = [
    '【自動判定】',
    '【営業NG】',
    '【品質不足】',
];

// ═══════════════════════════════════════════
//  鉄則: I列の状態判定
// ═══════════════════════════════════════════

/**
 * I列の値から、そのセルが「スクリプトによる書き込みが許可されるか」を判定する。
 *
 * 鉄則: 空欄のみ書き込み可。それ以外は絶対に触らない。
 *
 * @param {string} cellValue - I列の現在値
 * @returns {boolean} true = 書き込み可能（空欄）、false = 書き込み禁止
 */
function isWritable(cellValue) {
    return !cellValue || String(cellValue).trim() === '';
}

/**
 * I列の値から、その行が「送信対象」かどうかを判定する。
 * sort_by_category.js が使用する。
 *
 * @param {string} cellValue - I列の現在値
 * @returns {boolean} true = 送信対象、false = 送信不可
 */
function isSendable(cellValue) {
    const v = (cellValue || '').trim();
    if (v === '') return true;                          // 空欄 = 送信対象
    if (v === 'OK') return true;                        // 人間が明示的にOK
    if (v.startsWith(NG_PREFIX.MANUAL)) return true;    // 【手動承認】= 送信対象
    return false;                                       // それ以外は全て送信不可
}

// ═══════════════════════════════════════════
//  ドメイン正規化（唯一の実装）
// ═══════════════════════════════════════════

/**
 * URLからドメインを正規化して返す。
 * www. を除去し、小文字化する。
 *
 * @param {string} url
 * @returns {string} 正規化されたドメイン。無効な場合は空文字列。
 */
function normalizeDomain(url) {
    if (!url) return '';
    try {
        const u = new URL(url.startsWith('http') ? url : 'https://' + url);
        return u.hostname.replace(/^www\./, '').toLowerCase();
    } catch {
        // URLパースに失敗した場合はベストエフォートで抽出
        return url.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0].toLowerCase();
    }
}

// ═══════════════════════════════════════════
//  exclude_domains.txt 操作
// ═══════════════════════════════════════════

const EXCLUDE_DOMAINS_PATH = path.join(__dirname, '..', 'company_search', 'exclude_domains.txt');

/**
 * exclude_domains.txt を読み込んで Set で返す。
 * @returns {Set<string>}
 */
function loadExcludeDomains() {
    const domains = new Set();
    if (!fs.existsSync(EXCLUDE_DOMAINS_PATH)) {
        console.warn(`[schema] exclude_domains.txt が見つかりません: ${EXCLUDE_DOMAINS_PATH}`);
        return domains;
    }
    const content = fs.readFileSync(EXCLUDE_DOMAINS_PATH, 'utf-8');
    for (const line of content.split('\n')) {
        const d = line.trim();
        if (d) domains.add(d);
    }
    return domains;
}

/**
 * exclude_domains.txt に新しいドメインを追記する。
 * @param {string[]} newDomains
 */
function appendExcludeDomains(newDomains) {
    const existing = loadExcludeDomains();
    let addedCount = 0;
    for (const d of newDomains) {
        if (d && !existing.has(d)) {
            existing.add(d);
            addedCount++;
        }
    }
    if (addedCount > 0) {
        fs.writeFileSync(EXCLUDE_DOMAINS_PATH, Array.from(existing).sort().join('\n'), 'utf-8');
        console.log(`[schema] exclude_domains.txt 更新: +${addedCount}件 (合計${existing.size}件)`);
    }
}

// ═══════════════════════════════════════════
//  Google Sheets API クライアント
// ═══════════════════════════════════════════

const { google } = require('googleapis');

async function getGoogleSheetsClient() {
    let credPath = path.join(__dirname, 'google_credentials.json');
    if (!fs.existsSync(credPath)) {
        credPath = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
    }
    if (!fs.existsSync(credPath)) {
        credPath = path.join(__dirname, '..', 'company_search', 'google_credentials.json');
    }
    if (!fs.existsSync(credPath)) {
        throw new Error('google_credentials.json が見つかりません。');
    }

    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    console.log(`[Sheets] サービスアカウント: ${credentials.client_email}`);

    const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    return google.sheets({ version: 'v4', auth });
}

// ═══════════════════════════════════════════
//  資本金パーサー（唯一の実装）
// ═══════════════════════════════════════════

/**
 * 資本金テキストを円（数値）に変換する。
 * @param {string} raw - 例: "1,000万円", "3億円", "5000000"
 * @returns {number} 円換算の数値。パース不能な場合は0。
 */
function parseCapital(raw) {
    if (!raw || raw === '不明') return 0;
    const str = String(raw).replace(/,/g, '').replace(/\s/g, '');
    let num = parseFloat(str) || 0;
    if (str.includes('億')) num *= 100000000;
    else if (str.includes('万')) num *= 10000;
    return num;
}

// ═══════════════════════════════════════════
//  エクスポート
// ═══════════════════════════════════════════

module.exports = {
    SPREADSHEET_ID,
    TARGET_SHEETS,
    COL,
    NG_PREFIX,
    LEGACY_PREFIXES,
    isWritable,
    isSendable,
    normalizeDomain,
    loadExcludeDomains,
    appendExcludeDomains,
    getGoogleSheetsClient,
    parseCapital,
    EXCLUDE_DOMAINS_PATH,
};
