/**
 * local_db.js - ローカルマスターキャッシュ（重複チェックDB）
 *
 * 仕組み:
 *   - `master_companies.json` をローカルに保持し、企業名・ドメインのインデックスを管理する。
 *   - 検索結果のURLがヒットした段階でこのDBを照合し、既存企業であれば
 *     HPの重いクロール処理をスキップする（高速化）。
 *   - スプレッドシートへの書き込み後に自動で追記される（常に最新状態を保つ）。
 *   - 除外リストに追加されたエントリも同一DBで管理する。
 *
 * データ形式 (master_companies.json):
 *   {
 *     "meta": {
 *       "lastUpdated": "2026-04-27T00:00:00.000Z",
 *       "totalCount": 1234,
 *       "version": "1.0.0"
 *     },
 *     "companies": [
 *       {
 *         "name": "株式会社サンプル",
 *         "normName": "さんぷる",        // 正規化済み企業名（照合用）
 *         "domain": "sample.co.jp",       // 正規化済みドメイン
 *         "source": "Webマーケティング",   // 取得元シート名 or "除外リスト"
 *         "addedAt": "2026-04-27T..."
 *       }
 *     ]
 *   }
 */

const fs = require('fs');
const path = require('path');

const DB_PATH = path.join(__dirname, 'master_companies.json');
const DB_VERSION = '1.0.0';

// ========== 正規化ユーティリティ ==========

/**
 * 企業名を正規化する（照合用）
 * - 法人格除去 (株式会社/合同会社/有限会社)
 * - 全角→半角変換
 * - 空白・記号除去
 * - 小文字化
 */
function normalizeName(name) {
    if (!name) return '';
    return name
        .replace(/株式会社|合同会社|有限会社|一般社団法人|特定非営利活動法人|NPO法人/g, '')
        .replace(/[Ａ-Ｚａ-ｚ０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
        .replace(/[（(].*?[)）]/g, '') // 括弧内除去
        .replace(/　/g, ' ')
        .replace(/＆/g, '&')
        .toLowerCase()
        .replace(/[\s・\-_\.&,、。]/g, '')
        .trim();
}

/**
 * URLからドメインを正規化する
 * - www. / corp. / en. / ja. / jp. など汎用サブドメインを除去
 */
function normalizeDomain(url) {
    if (!url) return '';
    try {
        const u = new URL(url.startsWith('http') ? url : `https://${url}`);
        let host = u.hostname.toLowerCase();
        host = host.replace(/^(www|corp|en|ja|jp|info|m|sp)\./i, '');
        return host;
    } catch {
        return url.toLowerCase().replace(/^(https?:\/\/)?(www\.)?/, '').split('/')[0];
    }
}

// ========== DB読み込み・初期化 ==========

/**
 * ローカルDBを読み込む
 * ファイルが存在しない場合は空のDBを返す（エラーにしない）
 */
function loadDB() {
    if (!fs.existsSync(DB_PATH)) {
        return {
            meta: {
                lastUpdated: new Date().toISOString(),
                totalCount: 0,
                version: DB_VERSION,
            },
            companies: [],
        };
    }
    try {
        const raw = fs.readFileSync(DB_PATH, 'utf-8');
        return JSON.parse(raw);
    } catch (e) {
        console.error(`[LocalDB] DBファイルの読み込みに失敗しました: ${e.message}`);
        return {
            meta: {
                lastUpdated: new Date().toISOString(),
                totalCount: 0,
                version: DB_VERSION,
            },
            companies: [],
        };
    }
}

/**
 * ローカルDBを保存する
 */
function saveDB(db) {
    db.meta.lastUpdated = new Date().toISOString();
    db.meta.totalCount = db.companies.length;
    db.meta.version = DB_VERSION;
    fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2), 'utf-8');
}

// ========== インデックス構築 ==========

/**
 * DBからインメモリインデックスを構築する
 * 検索実行前に一度呼び出すことで、O(1)での高速照合を実現する
 *
 * @returns {{ nameIndex: Map, domainIndex: Set }}
 */
function buildIndex(db) {
    const nameIndex = new Map(); // normName -> entry
    const domainIndex = new Set(); // domain

    for (const entry of db.companies) {
        if (entry.normName) nameIndex.set(entry.normName, entry);
        if (entry.domain) domainIndex.add(entry.domain);
    }

    return { nameIndex, domainIndex };
}

// ========== 重複チェック ==========

/**
 * 企業名またはURLが既存DBに含まれるか確認する
 *
 * @param {{ nameIndex: Map, domainIndex: Set }} index - buildIndex()の戻り値
 * @param {{ name?: string, url?: string }} candidate - チェック対象
 * @returns {{ isDuplicate: boolean, reason: string, matchedSource: string }}
 */
function checkDuplicate(index, { name, url }) {
    const { nameIndex, domainIndex } = index;

    // 1. ドメイン完全一致
    if (url) {
        const domain = normalizeDomain(url);
        if (domain && domainIndex.has(domain)) {
            return {
                isDuplicate: true,
                reason: `ドメイン一致: ${domain}`,
                matchedSource: '(ドメイン照合)',
            };
        }
    }

    // 2. 企業名の正規化完全一致
    if (name) {
        const normName = normalizeName(name);
        if (normName && nameIndex.has(normName)) {
            const entry = nameIndex.get(normName);
            return {
                isDuplicate: true,
                reason: `企業名一致: ${name}`,
                matchedSource: entry.source || '',
            };
        }

        // 3. 部分一致（3文字以上のケース）
        if (normName && normName.length >= 3) {
            for (const [existingNorm, entry] of nameIndex.entries()) {
                if (existingNorm.length >= 3 &&
                    (normName.includes(existingNorm) || existingNorm.includes(normName))) {
                    return {
                        isDuplicate: true,
                        reason: `企業名部分一致: ${name} ≈ ${entry.name}`,
                        matchedSource: entry.source || '',
                    };
                }
            }
        }
    }

    return { isDuplicate: false, reason: '', matchedSource: '' };
}

// ========== DB追記 ==========

/**
 * 新しい企業エントリをDBに追記する
 * 重複している場合はスキップする（冪等性の保証）
 *
 * @param {Object} db - loadDB()の戻り値
 * @param {{ nameIndex: Map, domainIndex: Set }} index - buildIndex()の戻り値
 * @param {Array<{ name: string, url: string, source: string }>} newEntries
 * @returns {number} 実際に追記された件数
 */
function addEntries(db, index, newEntries) {
    let addedCount = 0;
    const now = new Date().toISOString();

    for (const entry of newEntries) {
        const { isDuplicate } = checkDuplicate(index, { name: entry.name, url: entry.url });
        if (isDuplicate) continue;

        const normName = normalizeName(entry.name);
        const domain = normalizeDomain(entry.url);

        const newEntry = {
            name: entry.name || '',
            normName,
            domain,
            source: entry.source || 'unknown',
            addedAt: now,
        };

        db.companies.push(newEntry);
        if (normName) index.nameIndex.set(normName, newEntry);
        if (domain) index.domainIndex.add(domain);
        addedCount++;
    }

    return addedCount;
}

// ========== 公開API ==========

/**
 * DBを初期化してインデックスを返す（ツール起動時に1回呼び出す）
 *
 * @returns {{ db: Object, index: Object, stats: Object }}
 */
function initDB() {
    const db = loadDB();
    const index = buildIndex(db);

    const excludeCount = db.companies.filter(c => c.source === '除外リスト').length;
    const normalCount = db.companies.length - excludeCount;

    console.log(`[LocalDB] マスターDB読み込み完了: ${db.companies.length}件 (通常: ${normalCount}件 / 除外: ${excludeCount}件)`);
    console.log(`[LocalDB] 最終更新: ${db.meta.lastUpdated}`);

    return {
        db,
        index,
        stats: {
            total: db.companies.length,
            excludeCount,
            normalCount,
        },
    };
}

/**
 * 書き込み後に企業リストをDBに追記して保存する
 *
 * @param {Object} db - initDB()から受け取ったdb
 * @param {Object} index - initDB()から受け取ったindex
 * @param {Array} companies - writeCompaniesToSheet()に渡した企業配列
 * @param {string} sheetName - 書き込み先のシート名
 */
function persistNewCompanies(db, index, companies, sheetName) {
    const entries = companies.map(c => ({
        name: c.title || '',
        url: c.url || '',
        source: sheetName,
    }));

    const added = addEntries(db, index, entries);
    if (added > 0) {
        saveDB(db);
        console.log(`[LocalDB] ${added}件をローカルDBに追記・保存しました`);
    }
}

/**
 * DBファイルのパスを返す（外部からの参照用）
 */
function getDBPath() {
    return DB_PATH;
}

module.exports = {
    initDB,
    checkDuplicate,
    addEntries,
    persistNewCompanies,
    loadDB,
    saveDB,
    buildIndex,
    normalizeName,
    normalizeDomain,
    getDBPath,
};
