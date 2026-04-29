/**
 * sheets_writer.js
 * Google Sheets 安全追記モジュール
 *
 * 【設計原則】
 * - C列（company_name列）を末尾からスキャンして最終非空白行を特定する
 * - sheet.rowCount / getLastRow() 等のメタデータは一切使用しない
 * - 書き込み前に開始行を確認ログに出力する
 * - 上書き事故を構造的に防止する
 */

'use strict';

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

// ═══════════════════════════════════════════
//  定数
// ═══════════════════════════════════════════

const CREDENTIALS_PATH = path.join(__dirname, 'google_credentials.json');

// C列 = 3列目（company_name）= 最終行スキャン基準列
const SCAN_COLUMN_INDEX = 3;

// ヘッダー行数（スキャン開始をヘッダーの次の行にするため）
const HEADER_ROWS = 1;

// 推奨カラム順（SKILL.md Step 12 準拠）
const COLUMNS = [
    'company_name',
    'official_url',
    'normalized_domain',
    'duplicate_status',
    'duplicate_reason',
    'source_portal_url',
    'profile_page_url',
    'representative_name',
    'representative_status',
    'capital_text',
    'capital_amount_jpy',
    'capital_status',
    'employee_text',
    'employee_count',
    'employee_status',
    'address',
    'business_description',
    'service_description',
    'matched_keywords',
    'negative_keywords',
    'keyword_status',
    'contact_form_url',
    'contact_status',
    'official_url_status',
    'source_urls',
    'notes',
    'retrieved_at',
];

// ═══════════════════════════════════════════
//  認証
// ═══════════════════════════════════════════

async function getAuthClient() {
    const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
    const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    return auth.getClient();
}

// ═══════════════════════════════════════════
//  コア: C列スキャンによる安全な最終行特定
// ═══════════════════════════════════════════

/**
 * C列（company_name列）を末尾からスキャンし、最終非空白行番号を返す。
 * sheet.rowCount / getLastRow() は使用しない。
 *
 * @param {object} sheets - Google Sheets API クライアント
 * @param {string} spreadsheetId
 * @param {string} sheetName
 * @returns {Promise<number>} 最終非空白行番号（1始まり）。データなし時は HEADER_ROWS。
 */
async function findLastDataRow(sheets, spreadsheetId, sheetName) {
    // C列全体を取得（最大10万行まで）
    const range = `'${sheetName}'!C:C`;
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range,
        valueRenderOption: 'UNFORMATTED_VALUE',
    });

    const values = res.data.values || [];

    // 末尾から順に非空白セルを探す
    for (let i = values.length - 1; i >= HEADER_ROWS; i--) {
        const cell = values[i][0];
        if (cell !== undefined && cell !== null && String(cell).trim() !== '') {
            return i + 1; // 1始まり行番号
        }
    }

    // データが1件もない場合 → ヘッダー行の次が書き込み開始行
    return HEADER_ROWS;
}

// ═══════════════════════════════════════════
//  ヘッダー書き込み（初回のみ）
// ═══════════════════════════════════════════

/**
 * シートにヘッダー行が存在しなければ書き込む。
 */
async function ensureHeader(sheets, spreadsheetId, sheetName) {
    const range = `'${sheetName}'!A1:${columnLetter(COLUMNS.length)}1`;
    const res = await sheets.spreadsheets.values.get({ spreadsheetId, range });
    const existing = (res.data.values || [[]])[0] || [];

    if (existing.length === 0 || existing[0] !== 'company_name') {
        await sheets.spreadsheets.values.update({
            spreadsheetId,
            range,
            valueInputOption: 'RAW',
            requestBody: { values: [COLUMNS] },
        });
        console.log(`[SheetsWriter] ヘッダーを書き込みました: ${sheetName}`);
    }
}

// ═══════════════════════════════════════════
//  メイン: 安全追記
// ═══════════════════════════════════════════

/**
 * 企業データをGoogle Sheetsに安全追記する。
 *
 * @param {object} options
 * @param {string} options.spreadsheetId - 書き込み先スプレッドシートID
 * @param {string} options.sheetName     - 書き込み先シート名
 * @param {Array<object>} options.records - 書き込む企業データ配列
 * @returns {Promise<{written: number, startRow: number}>}
 */
async function appendRecords({ spreadsheetId, sheetName, records }) {
    if (!records || records.length === 0) {
        console.log('[SheetsWriter] 書き込む件数が0件です。スキップ。');
        return { written: 0, startRow: null };
    }

    const authClient = await getAuthClient();
    const sheets = google.sheets({ version: 'v4', auth: authClient });

    // ヘッダー確認
    await ensureHeader(sheets, spreadsheetId, sheetName);

    // ── 最終行をC列スキャンで特定 ──────────────────────────
    const lastDataRow = await findLastDataRow(sheets, spreadsheetId, sheetName);
    const startRow = lastDataRow + 1;
    // ────────────────────────────────────────────────────────

    // 書き込み前ログ（必須）
    console.log(`[SheetsWriter] ──────────────────────────────────`);
    console.log(`[SheetsWriter] シート      : ${sheetName}`);
    console.log(`[SheetsWriter] C列最終行   : ${lastDataRow}`);
    console.log(`[SheetsWriter] 書き込み開始行: ${startRow}`);
    console.log(`[SheetsWriter] 書き込み件数 : ${records.length}`);
    console.log(`[SheetsWriter] ──────────────────────────────────`);

    // データを2次元配列に変換
    const rows = records.map(rec => COLUMNS.map(col => {
        const val = rec[col];
        if (Array.isArray(val)) return val.join(', ');
        if (val === null || val === undefined) return '';
        return String(val);
    }));

    const endCol = columnLetter(COLUMNS.length);
    const range = `'${sheetName}'!A${startRow}:${endCol}${startRow + rows.length - 1}`;

    await sheets.spreadsheets.values.update({
        spreadsheetId,
        range,
        valueInputOption: 'USER_ENTERED',
        requestBody: { values: rows },
    });

    console.log(`[SheetsWriter] ✅ 書き込み完了: ${records.length}件 → 行${startRow}〜${startRow + records.length - 1}`);

    return { written: records.length, startRow };
}

// ═══════════════════════════════════════════
//  ユーティリティ
// ═══════════════════════════════════════════

/**
 * 列番号（1始まり）をアルファベット列記号に変換
 * 例: 1→A, 26→Z, 27→AA
 */
function columnLetter(n) {
    let result = '';
    while (n > 0) {
        const rem = (n - 1) % 26;
        result = String.fromCharCode(65 + rem) + result;
        n = Math.floor((n - 1) / 26);
    }
    return result;
}

// ═══════════════════════════════════════════
//  エクスポート
// ═══════════════════════════════════════════

module.exports = { appendRecords, findLastDataRow, COLUMNS };
