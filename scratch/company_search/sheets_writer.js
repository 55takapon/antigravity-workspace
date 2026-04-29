/**
 * sheets_writer.js - Google Sheets書き込みモジュール
 *
 * 既存SpreadsheetのService Account (form_automation/google_credentials.json) を再利用。
 * 既存フォーマット（A:№〜I:送信不可理由）に追加列（J〜M）を加えて書き込む。
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

// テンプレートシート名
const TEMPLATE_SHEET_NAME = 'list-format';

// 追加列ヘッダー（テンプレートにない列）
const EXTRA_HEADERS = ['従業員数', '資本金', 'キーワードHIT', 'HIT詳細', '取得日時'];

// 全ヘッダー定義（参照用）
const HEADERS = [
    '№',                    // A
    'エリア',               // B
    '企業名',               // C
    '代表者名',             // D
    'URL',                  // E
    '問い合わせフォームURL', // F
    '送信日',               // G
    '送信○×',              // H
    '送信不可理由',         // I
    '従業員数',             // J（追加）
    '資本金',               // K（追加）
    'キーワードHIT',        // L（追加）
    'HIT詳細',             // M（追加）
    '取得日時',            // N（追加）
];

/**
 * Google Sheets APIクライアントを取得
 */
async function getGoogleSheetsClient() {
    // まず同ディレクトリ、次にform_automationフォルダを確認
    let credPath = path.join(__dirname, 'google_credentials.json');
    if (!fs.existsSync(credPath)) {
        credPath = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
    }
    if (!fs.existsSync(credPath)) {
        throw new Error('google_credentials.json が見つかりません。company_search/ またはform_automation/ に配置してください。');
    }

    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    console.log(`[Sheets] サービスアカウント: ${credentials.client_email}`);

    const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    return google.sheets({ version: 'v4', auth });
}

/**
 * 除外リストをSheetsから読み込む
 * @returns {Set<string>} 除外企業名・URLのセット
 */
async function loadExcludeList(sheets, config) {
    const excludeConfig = config.exclude;
    if (!excludeConfig?.spreadsheet_id || !excludeConfig?.sheet_name) {
        console.log('[除外リスト] 設定なし。スキップ。');
        return { names: new Set(), domains: new Set() };
    }

    try {
        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: excludeConfig.spreadsheet_id,
            range: excludeConfig.sheet_name,
        });
        const rows = response.data.values || [];
        const names = new Set();
        const domains = new Set();

        for (const row of rows) {
            // B列: 企業名、D列: URL
            if (row[1]) names.add(row[1].trim());
            if (row[3]) {
                try {
                    const hostname = new URL(row[3]).hostname.replace(/^www\./, '').toLowerCase();
                    domains.add(hostname);
                } catch { }
            }
        }

        console.log(`[除外リスト] ${names.size}社 / ${domains.size}ドメイン 読み込み完了`);
        return { names, domains };
    } catch (err) {
        console.error(`[除外リスト] 読み込みエラー: ${err.message}`);
        return { names: new Set(), domains: new Set() };
    }
}

/**
 * 既存シートから登録済みURLを取得（重複チェック用）
 * @returns {Set<string>} 登録済みドメインのセット
 */
async function loadExistingUrls(sheets, spreadsheetId, sheetName) {
    const domains = new Set();
    try {
        const response = await sheets.spreadsheets.values.get({
            spreadsheetId,
            range: `${sheetName}!E:E`,  // URL列
        });
        const rows = response.data.values || [];
        for (const row of rows) {
            if (row[0] && row[0].startsWith('http')) {
                try {
                    const hostname = new URL(row[0]).hostname.replace(/^www\./, '').toLowerCase();
                    domains.add(hostname);
                } catch { }
            }
        }
    } catch {
        // シートが存在しない場合は空セットを返す
    }
    return domains;
}

/**
 * テンプレートシート「list-format」をコピーして新規シートを作成
 * 列幅・書式・ドロップダウン・条件付き書式がすべて引き継がれる
 */
async function ensureSheet(sheets, spreadsheetId, sheetName) {
    try {
        // シート一覧を取得
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
        const existingSheet = spreadsheet.data.sheets.find(s => s.properties.title === sheetName);

        if (existingSheet) {
            console.log(`[Sheets] シート "${sheetName}" は既に存在します`);
            return;
        }

        // テンプレートシートを探す
        const templateSheet = spreadsheet.data.sheets.find(s => s.properties.title === TEMPLATE_SHEET_NAME);

        if (templateSheet) {
            // === テンプレートコピー方式（推奨） ===
            const templateSheetId = templateSheet.properties.sheetId;

            // テンプレートシートを複製
            const copyResult = await sheets.spreadsheets.sheets.copyTo({
                spreadsheetId,
                sheetId: templateSheetId,
                requestBody: {
                    destinationSpreadsheetId: spreadsheetId,
                },
            });

            const newSheetId = copyResult.data.sheetId;

            // 複製されたシートの名前を変更
            await sheets.spreadsheets.batchUpdate({
                spreadsheetId,
                requestBody: {
                    requests: [{
                        updateSheetProperties: {
                            properties: {
                                sheetId: newSheetId,
                                title: sheetName,
                            },
                            fields: 'title',
                        },
                    }],
                },
            });

            console.log(`[Sheets] テンプレート "${TEMPLATE_SHEET_NAME}" をコピーして "${sheetName}" を作成しました`);

            // テンプレートの既存データ（連番以外）をクリア（B2以降）
            try {
                await sheets.spreadsheets.values.batchClear({
                    spreadsheetId,
                    requestBody: {
                        ranges: [
                            `${sheetName}!B2:M1000`,  // B〜M列のデータをクリア（A列の連番は保持）
                        ],
                    },
                });
            } catch { }

        } else {
            // === フォールバック: テンプレートが見つからない場合は従来方式 ===
            console.log(`[Sheets] テンプレート "${TEMPLATE_SHEET_NAME}" が見つかりません。空のシートを作成します。`);

            await sheets.spreadsheets.batchUpdate({
                spreadsheetId,
                requestBody: {
                    requests: [{
                        addSheet: {
                            properties: { title: sheetName },
                        },
                    }],
                },
            });

            // 全ヘッダーを書き込み
            await sheets.spreadsheets.values.update({
                spreadsheetId,
                range: `${sheetName}!A1`,
                valueInputOption: 'USER_ENTERED',
                requestBody: {
                    values: [HEADERS],
                },
            });

            console.log(`[Sheets] シート "${sheetName}" を作成しました（フォールバック）`);
        }

    } catch (err) {
        console.error(`[Sheets] シート作成エラー: ${err.message}`);
        throw err;
    }
}

/**
 * 企業データをSheetsに書き込む
 * @param {Array} companies - 企業データの配列
 */
async function writeCompaniesToSheet(sheets, spreadsheetId, sheetName, companies, config) {
    if (companies.length === 0) {
        console.log('[Sheets] 書き込みデータなし');
        return;
    }

    // シートが存在しなければ作成
    await ensureSheet(sheets, spreadsheetId, sheetName);

    // 既存データの行数を確認（追記位置の決定）
    // B列（エリア）で判定。A列は連番プリセットがあるため使わない
    let startRow = 2; // デフォルト（ヘッダーの次）
    try {
        const existingData = await sheets.spreadsheets.values.get({
            spreadsheetId,
            range: `${sheetName}!C:C`,
        });
        const rows = existingData.data.values || [];
        // 実データがある行の次から書き込む
        startRow = rows.length + 1;
        if (startRow < 2) startRow = 2;
    } catch { }

    // === 行数不足時の自動追加 (Grid Limit対策) ===
    try {
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
        const targetSheet = spreadsheet.data.sheets.find(s => s.properties.title === sheetName);
        if (targetSheet) {
            const sheetId = targetSheet.properties.sheetId;
            const rowCount = targetSheet.properties.gridProperties.rowCount;
            const requiredRows = startRow + companies.length;
            
            if (requiredRows > rowCount) {
                const addRows = requiredRows - rowCount + 50; // 余分に50行追加
                console.log(`[Sheets] シート行が不足しています。${addRows}行を追加します。`);
                await sheets.spreadsheets.batchUpdate({
                    spreadsheetId,
                    requestBody: {
                        requests: [{
                            appendDimension: {
                                sheetId,
                                dimension: 'ROWS',
                                length: addRows
                            }
                        }]
                    }
                });
            }
        }
    } catch (e) {
        console.error(`[Sheets] 行追加に失敗（無視して継続）: ${e.message}`);
    }

    const now = new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' });

    // 資本金を数値（円）に変換するヘルパー
    const parseCapital = (raw) => {
        if (!raw) return 0;
        const str = String(raw).replace(/,/g, '').replace(/\s/g, '');
        let num = parseFloat(str) || 0;
        if (str.includes('億')) num *= 100000000;
        else if (str.includes('万')) num *= 10000;
        return num;
    };

    // データ行を作成
    const rows = companies.map((company, idx) => {
        const empCount = company.crawlData?.employeeCount;
        const capNum = parseCapital(company.crawlData?.capitalRaw);
        
        // ★ 自動✕判定（従業員20名以上、または資本金1000万円以上）
        let autoEvaluation = '';
        let autoReason = '';
        if ((empCount !== null && empCount >= 20) || capNum >= 10000000) {
            autoEvaluation = '✕';
            if (empCount >= 20) autoReason = '【自動判定】従業員20名以上';
            else if (capNum >= 10000000) autoReason = '【自動判定】資本金1000万円以上';
        }

        return [
            startRow - 1 + idx,                        // A: №
            config.search.region || '',                 // B: エリア
            company.title || '',                        // C: 企業名
            company.crawlData?.representative || '',    // D: 代表者名
            company.url || '',                          // E: URL
            company.crawlData?.contactFormUrl || '',     // F: 問い合わせフォームURL
            '',                                         // G: 送信日（空白）
            autoEvaluation,                             // H: 送信○×（条件に合致すれば✕）
            autoReason,                                 // I: 送信不可理由（自動判定理由または空白）
            empCount !== null ? empCount : '不明',      // J: 従業員数
            company.crawlData?.capitalRaw || '不明',     // K: 資本金
            company.crawlData?.keywordHitFlag ? '○' : '×',  // L: キーワードHIT
            (company.crawlData?.keywordHits || []).join(', '),  // M: HIT詳細
            now,                                        // N: 取得日時
        ];
    });

    // バッチ書き込み
    const range = `${sheetName}!A${startRow}`;
    await sheets.spreadsheets.values.update({
        spreadsheetId,
        range,
        valueInputOption: 'USER_ENTERED',
        requestBody: {
            values: rows,
        },
    });

    console.log(`[Sheets] ${rows.length}件を行${startRow}〜${startRow + rows.length - 1}に書き込みました`);
}

module.exports = {
    getGoogleSheetsClient,
    loadExcludeList,
    loadExistingUrls,
    ensureSheet,
    writeCompaniesToSheet,
    HEADERS,
};
