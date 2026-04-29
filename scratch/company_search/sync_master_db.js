/**
 * sync_master_db.js - スプレッドシート→ローカルDB 一括同期スクリプト
 *
 * 役割:
 *   スプレッドシートの全シート（過去データ・除外リスト含む）から
 *   企業名（C列）・URL（E列）を取得し、ローカルの master_companies.json を
 *   初期化・再構築する。
 *
 * 実行タイミング:
 *   - 初回セットアップ時（必須）
 *   - スプレッドシート側で手動変更（追加・削除・除外リスト更新）があった後
 *   - 定期メンテナンス時（月1回推奨）
 *
 * 使い方:
 *   node sync_master_db.js               # 全シートを同期
 *   node sync_master_db.js --dry-run     # 実際には保存しない（確認用）
 *
 * 除外リスト対応:
 *   シート名「除外リスト」に記載された企業は source="除外リスト" として
 *   DBに取り込まれ、以降の検索で自動的にブロックされます。
 *   「除外リスト」の列構成は B列:企業名 / D列:URL を想定しています。
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');
const { loadDB, saveDB, buildIndex, addEntries, getDBPath } = require('./local_db');

const CREDENTIALS_PATH = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
const CONFIG_PATH = path.join(__dirname, 'config.yaml');

const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');

// 「除外リスト」シートの列定義
// B列(index 1) = 企業名, D列(index 3) = URL
const EXCLUDE_SHEET_NAME = '除外リスト';
const EXCLUDE_NAME_COL = 1;  // B列
const EXCLUDE_URL_COL = 3;   // D列

// 通常シートの列定義
// C列(index 2) = 企業名, E列(index 4) = URL
const NORMAL_NAME_COL = 2;  // C列
const NORMAL_URL_COL = 4;   // E列

// 同期対象外のシート（テンプレートや管理用）
const SKIP_SHEETS = ['list-format'];

async function main() {
    console.log('========================================');
    console.log('  ローカルDB 全シート同期ツール');
    console.log(`  モード: ${isDryRun ? 'ドライラン（保存しない）' : '本番（保存する）'}`);
    console.log('========================================\n');

    // 1. Google Sheets 接続
    let credPath = path.join(__dirname, 'google_credentials.json');
    if (!fs.existsSync(credPath)) {
        credPath = CREDENTIALS_PATH;
    }
    if (!fs.existsSync(credPath)) {
        console.error('google_credentials.json が見つかりません。');
        process.exit(1);
    }

    const auth = new google.auth.GoogleAuth({
        keyFile: credPath,
        scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });
    const sheets = google.sheets({ version: 'v4', auth });

    // 2. スプレッドシートIDを config.yaml から取得
    let spreadsheetId = '';
    try {
        const yaml = require('js-yaml');
        const config = yaml.load(fs.readFileSync(CONFIG_PATH, 'utf-8'));
        spreadsheetId = config.output?.spreadsheet_id || config.exclude?.spreadsheet_id || '';
    } catch (e) {
        console.error(`[設定] config.yaml の読み込みに失敗: ${e.message}`);
    }

    if (!spreadsheetId) {
        // フォールバック: ハードコード（config.yamlが読めない場合）
        spreadsheetId = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
        console.warn(`[設定] config.yaml からスプレッドシートIDを取得できませんでした。デフォルトIDを使用します: ${spreadsheetId}`);
    }

    console.log(`[接続] スプレッドシート: ${spreadsheetId}\n`);

    // 3. 全シート一覧を取得
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
    const allSheets = spreadsheet.data.sheets.map(s => s.properties.title);
    console.log(`[シート一覧] ${allSheets.length}枚: ${allSheets.join(', ')}\n`);

    // 4. 新しいDBを構築（既存DBは上書きする）
    const db = {
        meta: {
            lastUpdated: new Date().toISOString(),
            totalCount: 0,
            version: '1.0.0',
        },
        companies: [],
    };
    const index = buildIndex(db);

    let totalAdded = 0;
    const summary = [];

    // 5. 各シートを読み込んで追記
    for (const sheetName of allSheets) {
        if (SKIP_SHEETS.includes(sheetName)) {
            console.log(`[スキップ] "${sheetName}" (テンプレートシート)`);
            continue;
        }

        const isExcludeSheet = sheetName === EXCLUDE_SHEET_NAME;
        const nameCol = isExcludeSheet ? EXCLUDE_NAME_COL : NORMAL_NAME_COL;
        const urlCol = isExcludeSheet ? EXCLUDE_URL_COL : NORMAL_URL_COL;
        const maxCol = Math.max(nameCol, urlCol) + 1;
        const colRange = `A:${String.fromCharCode(65 + maxCol - 1)}`; // A:D や A:E など

        try {
            const res = await sheets.spreadsheets.values.get({
                spreadsheetId,
                range: `${sheetName}!${colRange}`,
            });

            const rows = res.data.values || [];
            if (rows.length <= 1) {
                console.log(`[${sheetName}] データなし（ヘッダーのみ）`);
                summary.push({ sheet: sheetName, count: 0, added: 0, source: isExcludeSheet ? '除外リスト' : sheetName });
                continue;
            }

            // ヘッダー行（1行目）を除いてエントリを作成
            const entries = [];
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const name = (row[nameCol] || '').trim();
                const url = (row[urlCol] || '').trim();
                if (!name && !url) continue;
                entries.push({
                    name,
                    url,
                    source: isExcludeSheet ? EXCLUDE_SHEET_NAME : sheetName,
                });
            }

            const added = addEntries(db, index, entries);
            totalAdded += added;
            console.log(`[${sheetName}] ${rows.length - 1}件読み込み → ${added}件をDBに追加${isExcludeSheet ? ' (除外リスト)' : ''}`);
            summary.push({ sheet: sheetName, count: rows.length - 1, added, source: isExcludeSheet ? '除外リスト' : sheetName });

        } catch (e) {
            console.error(`[${sheetName}] 読み込みエラー: ${e.message}`);
            summary.push({ sheet: sheetName, count: 0, added: 0, error: e.message });
        }
    }

    // 6. 結果サマリー
    console.log('\n========================================');
    console.log('  同期結果サマリー');
    console.log('========================================');
    console.log(`合計追加数: ${totalAdded}件`);
    console.log(`DBパス: ${getDBPath()}\n`);
    console.log('シート別内訳:');
    for (const s of summary) {
        const tag = s.source === '除外リスト' ? '[除外]' : '     ';
        const err = s.error ? ` ⚠️ エラー: ${s.error}` : '';
        console.log(`  ${tag} ${s.sheet}: ${s.count}件読み込み / ${s.added}件追加${err}`);
    }

    const excludeCount = db.companies.filter(c => c.source === '除外リスト').length;
    const normalCount = db.companies.length - excludeCount;
    console.log(`\n  DB合計: ${db.companies.length}件（通常: ${normalCount}件 / 除外: ${excludeCount}件）`);

    // 7. 保存
    if (!isDryRun) {
        saveDB(db);
        console.log(`\n✅ master_companies.json に保存しました: ${getDBPath()}`);
    } else {
        console.log('\n[ドライラン] 保存をスキップしました。');
    }
}

main().catch(e => {
    console.error('Fatal error:', e);
    process.exit(1);
});
