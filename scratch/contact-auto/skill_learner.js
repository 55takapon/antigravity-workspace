#!/usr/bin/env node
/**
 * skill_learner.js
 * ─────────────────────────────────────────────────────────────────────────────
 * contact-auto 日次スキル自動学習エンジン
 *
 * 動作フロー:
 *   1. 当日の logs/unmatched_fields/*.json を読み込む
 *   2. 未マッチフィールドを集計（name/id/layer1/layer2/type）
 *   3. 既存カテゴリへの帰属をヒューリスティックで推定
 *   4. 出現頻度に応じて自動パッチ（field_recognizer.js + CF7_FIELD_MAP）
 *   5. SKILL.md の「日次発見パターン」セクションを更新
 *   6. 変更サマリーを出力
 *
 * 使い方:
 *   node skill_learner.js [--date YYYY-MM-DD] [--dry-run] [--min-count N]
 *
 * contact_auto.js から自動起動される（バッチ末尾に組み込み済み）
 * ─────────────────────────────────────────────────────────────────────────────
 */

'use strict';
const fs = require('fs');
const path = require('path');

// ── CLI引数 ──
const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const MIN_COUNT = parseInt(args.find((_, i) => args[i - 1] === '--min-count') || '1', 10);
const TARGET_DATE = args.find((_, i) => args[i - 1] === '--date') ||
    new Date().toISOString().slice(0, 10); // デフォルト: 今日

const BASE_DIR = __dirname;
const LOGS_DIR = path.join(BASE_DIR, 'logs', 'unmatched_fields');
const RECOGNIZER_PATH = path.join(BASE_DIR, 'core', 'field_recognizer.js');
const CF7_PATH = path.join(BASE_DIR, 'core', 'cf7_http_submitter.js');
const SKILL_MD_PATH = path.join(BASE_DIR, '..', '..', '.agent', 'skills', 'contact-auto', 'SKILL.md');

// ── カテゴリ推定ルール（優先順）──
// [カテゴリキー, labelパターン[], nameパターン[]]
const CATEGORY_RULES = [
    ['email',            [/メール/,/mail/i,/e-mail/i,/eメール/],        [/mail/i,/email/i,/^em$/i]],
    ['phone',            [/電話/,/tel/i,/phone/i],                      [/tel/i,/phone/i,/denwa/i]],
    ['fax',              [/fax/i,/ファックス/],                           [/fax/i]],
    ['company',          [/会社/,/企業/,/法人/,/医院/,/事務所/,/店舗/,/組織/,/屋号/],[/company/i,/corp/i,/org/i,/iin/i,/jimusho/i,/shop/i]],
    ['department',       [/部署/,/部門/,/役職/,/所属/],                  [/department/i,/division/i,/busho/i,/yakushoku/i]],
    ['meeting',          [/ミーティング/,/Zoom/,/オンライン面談/,/ウェブ会議/], [/meeting/i,/zoom/i,/web.?meeting/i,/kaigi/i]],
    ['plan',             [/プラン/,/コース/,/plan/i,/course/i],          [/^plan$/i,/^course$/i,/grade/i]],
    ['url',              [/URL/,/ウェブサイト/,/サイト/,/ホームページ/,/HP/],[/url/i,/website/i,/homepage/i,/site/i]],
    ['address',          [/住所/,/所在地/,/ご住所/],                      [/address/i,/jusho/i]],
    ['zipcode',          [/郵便番号/,/〒/,/zip/i],                       [/zip/i,/postal/i,/yuubin/i]],
    ['prefecture',       [/都道府県/,/prefecture/i],                     [/prefecture/i,/pref/i]],
    ['subject',          [/件名/,/題名/,/タイトル/,/subject/i],          [/subject/i,/title/i,/kenmei/i]],
    ['inquiry_type',     [/種別/,/分類/,/お問い合わせ内容/,/相談内容/,/項目/],[/inquiry.?type/i,/contact.?type/i,/category/i,/shubetsu/i]],
    ['budget',           [/予算/,/ご予算/,/budget/i],                    [/budget/i,/yosan/i,/cost/i]],
    ['deadline',         [/納期/,/制作時期/,/希望納期/,/timing/i],       [/deadline/i,/nouki/i,/schedule/i,/seisaku.?jiki/i]],
    ['page_count',       [/ページ数/,/ページ/],                          [/page.?count/i,/pages/i]],
    ['referral',         [/きっかけ/,/流入/,/どこで知/,/お知りになった/], [/referral/i,/kikkake/i,/source/i,/how.?did/i]],
    ['preferred_contact',[/連絡方法/,/ご連絡方法/,/希望連絡/],           [/contact.?method/i,/contact.?way/i,/renraku/i]],
    ['preferred_time',   [/連絡時間/,/時間帯/,/ご希望時間/],             [/time/i,/jikantai/i]],
    ['industry',         [/業種/,/業界/,/industry/i],                   [/industry/i,/gyoushu/i,/business.?type/i]],
    // 氏名系（最後: 汎用）
    ['kana',             [/フリガナ/,/ふりがな/,/かな/,/カナ/,/読み/],  [/kana/i,/furigana/i,/yomi/i]],
    ['name_sei',         [/^姓$/,/^せい$/,/^セイ$/,/名字/,/苗字/],     [/^sei$/i,/last.?name/i,/family.?name/i]],
    ['name_mei',         [/^名$/,/^めい$/,/^メイ$/,/名前\(名\)/],       [/^mei$/i,/first.?name/i,/given.?name/i]],
    ['name',             [/お名前/,/氏名/,/担当者/,/ご担当/,/name/i],   [/name/i,/shimei/i,/onamae/i,/tantousha/i]],
    ['message',          [/内容/,/メッセージ/,/本文/,/ご相談/,/詳細/],  [/message/i,/body/i,/inquiry/i,/content/i,/soudan/i]],
];

/**
 * ラベル文字列からカテゴリを推定
 */
function guessCategory(field) {
    const label = [field.layer1 || '', field.layer2 || '', field.layer4 || ''].join(' ').trim();
    const nameId = [field.name || '', field.id || ''].join(' ').trim().toLowerCase();

    for (const [cat, labelPats, namePats] of CATEGORY_RULES) {
        for (const p of labelPats) if (p.test(label)) return cat;
        for (const p of namePats) if (p.test(nameId)) return cat;
    }
    return null; // 推定不能
}

/**
 * 当日のunmatchedログファイルを収集
 */
function collectTodayLogs(logsDir, date) {
    if (!fs.existsSync(logsDir)) return [];
    return fs.readdirSync(logsDir)
        .filter(f => f.endsWith('.json') && !fs.statSync(path.join(logsDir, f)).isDirectory())
        .filter(f => {
            const stat = fs.statSync(path.join(logsDir, f));
            // ローカル日付で比較（JST対応）
            const d = stat.mtime;
            const localDate = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
            return localDate === date;
        })
        .map(f => {
            try {
                let raw = fs.readFileSync(path.join(logsDir, f), 'utf-8');
                if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1); // BOM除去
                return JSON.parse(raw);
            }
            catch (e) {
                console.error(`  ⚠️ JSONパースエラー (${f}):`, e.message);
                return null;
            }
        })
        .filter(Boolean);
}

/**
 * 未マッチフィールドを集計し、カテゴリ推定付きで返す
 * @returns {Array<{name, id, label, type, category, count, urls}>}
 */
function aggregateUnmatched(logs) {
    const map = new Map(); // key: name|id

    for (const log of logs) {
        for (const field of (log.fields || [])) {
            const key = `${field.name || ''}|${field.id || ''}`;
            if (!map.has(key)) {
                map.set(key, {
                    name: field.name || '',
                    id: field.id || '',
                    label: [field.layer1, field.layer2, field.layer4].filter(Boolean).join(' / '),
                    type: field.type || 'text',
                    category: guessCategory(field),
                    count: 0,
                    urls: new Set(),
                    isRequired: field.isRequired || false
                });
            }
            const entry = map.get(key);
            entry.count++;
            if (log.url) entry.urls.add(new URL(log.url).hostname);
        }
    }

    return Array.from(map.values())
        .map(e => ({ ...e, urls: Array.from(e.urls) }))
        .sort((a, b) => b.count - a.count);
}

/**
 * field_recognizer.js のSEMANTIC_ATTR_MAPに新規パターンを追記
 * 追記先: 対応カテゴリの配列末尾
 */
function patchFieldRecognizer(recognizerPath, patches) {
    if (patches.length === 0) return 0;
    let code = fs.readFileSync(recognizerPath, 'utf-8');
    let patched = 0;

    for (const { category, namePattern } of patches) {
        // すでに登録済みかチェック
        if (code.includes(namePattern)) continue;

        // カテゴリブロックを探して末尾に追加
        const targetComment = `['${category}', [`;
        const insertAfter = new RegExp(`(\\['${category}', \\[[^\\]]*?)\\]\\]`, 's');
        if (insertAfter.test(code)) {
            // 末尾のパターンの前に追加
            code = code.replace(insertAfter, (m, before) => {
                return `${before},\n        ${namePattern}\n    ]]`;
            });
            patched++;
        }
    }

    if (patched > 0 && !DRY_RUN) {
        fs.writeFileSync(recognizerPath, code, 'utf-8');
    }
    return patched;
}

/**
 * CF7_FIELD_MAPに新規エントリを追記
 */
function patchCF7Map(cf7Path, patches) {
    if (patches.length === 0) return 0;
    let code = fs.readFileSync(cf7Path, 'utf-8');
    let patched = 0;
    const newLines = [];

    for (const { fieldName, category } of patches) {
        // すでに登録済みかチェック
        const escaped = fieldName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        if (new RegExp(`['"]${escaped}['"]`).test(code)) continue;
        newLines.push(`    '${fieldName}': '${category}', // 自動学習追加`);
        patched++;
    }

    if (newLines.length > 0) {
        // CF7_FIELD_MAPの末尾（"};" の直前）に追記
        const insertMarker = '};\n\n/**\n * CF7フォームにHTTP直接送信';
        const block = newLines.join('\n');
        code = code.replace(insertMarker, `${block}\n${insertMarker}`);
        if (!DRY_RUN) {
            fs.writeFileSync(cf7Path, code, 'utf-8');
        }
    }
    return patched;
}

/**
 * SKILL.md の「日次発見パターン」セクションを更新（upsert）
 */
function updateSkillMd(skillMdPath, date, discovered) {
    if (!fs.existsSync(skillMdPath)) return;
    let md = fs.readFileSync(skillMdPath, 'utf-8');

    const sectionHeader = '## 日次発見パターンログ';
    const todayEntry = buildSkillMdEntry(date, discovered);

    if (md.includes(sectionHeader)) {
        const dayHeader = `### ${date}`;
        if (md.includes(dayHeader)) {
            // ── dedup: 既存テーブルと新テーブルのフィールド名セットを比較 ──
            const existingMatch = md.match(new RegExp(`### ${date}[\\s\\S]*?(?=###|$)`, 'm'));
            if (existingMatch) {
                const existingNames = [...existingMatch[0].matchAll(/\| `([^`]+)` \|/g)].map(m => m[1]).sort().join(',');
                const newNames = [...todayEntry.matchAll(/\| `([^`]+)` \|/g)].map(m => m[1]).sort().join(',');
                if (existingNames === newNames) {
                    console.log(`  ℹ️  ${date} のエントリは既に最新です。重複追記をスキップ。`);
                    return; // dedup: 同一内容なので更新不要
                }
            }
            // 当日エントリを丸ごと置換
            const dayRe = new RegExp(`### ${date}[\\s\\S]*?(?=###|$)`, 'm');
            md = md.replace(dayRe, todayEntry + '\n\n');
        } else {
            // セクション先頭に追記（新しい日を上に）
            md = md.replace(sectionHeader, `${sectionHeader}\n\n> ⚠️ このセクションは \`skill_learner.js\` が自動更新する。重複追記は dedup で防止済み（v0.7〜）。\n\n${todayEntry}\n\n`);
        }
    } else {
        // セクション自体がない → 末尾に追加
        md += `\n\n${sectionHeader}\n\n${todayEntry}`;
    }

    if (!DRY_RUN) {
        fs.writeFileSync(skillMdPath, md, 'utf-8');
    }
}

function buildSkillMdEntry(date, discovered) {
    const rows = discovered.map(d => {
        const cat = d.category ? `✅ ${d.category}` : '❓ 未推定';
        const status = d.autoPatched ? '🔧 自動パッチ済' : (d.category ? '📋 候補あり' : '⚠️ 要確認');
        return `| \`${d.name || d.id}\` | ${d.label || '—'} | ${d.type} | ${cat} | ${d.count} | ${status} |`;
    }).join('\n');

    return `### ${date}

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
${rows || '| (未マッチなし) | — | — | — | — | — |'}`;
}

/**
 * nameとlabelからfield_recognizerのパターン文字列を生成
 */
function buildRegexPattern(fieldName) {
    // 特殊文字をエスケープしてパターン化
    const safe = fieldName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // ハイフン・アンダースコアを [_-]? に正規化
    const normalized = safe.replace(/[-_]/g, '[_-]?');
    return `/^${normalized}$/i`;
}

// ══════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════
async function main() {
    console.log('\n' + '═'.repeat(60));
    console.log(`🧠 skill_learner — 日次スキル自動学習`);
    console.log(`   対象日: ${TARGET_DATE} | MIN_COUNT: ${MIN_COUNT} | DRY_RUN: ${DRY_RUN}`);
    console.log('═'.repeat(60) + '\n');

    // Step 1: 当日ログ収集
    const logs = collectTodayLogs(LOGS_DIR, TARGET_DATE);
    console.log(`📂 当日の未マッチログ: ${logs.length}件`);

    if (logs.length === 0) {
        console.log('  ℹ️  本日の未マッチフィールドなし。学習スキップ。\n');
        return;
    }

    // Step 2: 集計・カテゴリ推定
    const allFields = aggregateUnmatched(logs);
    const targets = allFields.filter(f => f.count >= MIN_COUNT);

    console.log(`\n📊 集計結果: ${allFields.length}種類のフィールド, 閾値(${MIN_COUNT}件)以上: ${targets.length}件`);
    console.log('\n  フィールド名                   ラベル                     推定カテゴリ  件数');
    console.log('  ' + '─'.repeat(80));

    for (const f of targets) {
        const cat = f.category ? f.category.padEnd(16) : '❓ 未推定'.padEnd(16);
        const label = (f.label || '').substring(0, 24).padEnd(24);
        const name = `${f.name || f.id}`.substring(0, 28).padEnd(28);
        console.log(`  ${name} ${label} ${cat} ×${f.count}`);
    }

    // Step 3: 自動パッチ判定・適用
    const recognizerPatches = [];
    const cf7Patches = [];
    const discovered = [];

    for (const f of targets) {
        const entry = { ...f, autoPatched: false };

        if (f.category && f.name) {
            // field_recognizer用パターン
            recognizerPatches.push({
                category: f.category,
                namePattern: buildRegexPattern(f.name)
            });
            // CF7_FIELD_MAP用エントリ
            cf7Patches.push({
                fieldName: f.name,
                category: f.category
            });
            entry.autoPatched = true;
        }
        discovered.push(entry);
    }

    // Step 4: ファイルパッチ適用
    console.log('\n🔧 パッチ適用:');

    if (DRY_RUN) {
        console.log('  [DRY-RUN] 実際のファイル変更はスキップ');
        console.log(`  → field_recognizer.js: ${recognizerPatches.length}件追加予定`);
        console.log(`  → CF7_FIELD_MAP: ${cf7Patches.length}件追加予定`);
    } else {
        const rCount = patchFieldRecognizer(RECOGNIZER_PATH, recognizerPatches);
        const cCount = patchCF7Map(CF7_PATH, cf7Patches);
        console.log(`  ✅ field_recognizer.js: ${rCount}件追加`);
        console.log(`  ✅ CF7_FIELD_MAP: ${cCount}件追加`);
    }

    // Step 5: SKILL.md更新
    updateSkillMd(SKILL_MD_PATH, TARGET_DATE, discovered);
    if (!DRY_RUN) {
        console.log(`  ✅ SKILL.md: ${TARGET_DATE} エントリを更新`);
    }

    // Step 6: サマリー
    const autoCount = discovered.filter(d => d.autoPatched).length;
    const unknownCount = discovered.filter(d => !d.category).length;

    console.log('\n' + '═'.repeat(60));
    console.log('📋 学習サマリー');
    console.log('═'.repeat(60));
    console.log(`  対象フィールド数: ${targets.length}`);
    console.log(`  自動パッチ適用:   ${autoCount}件`);
    console.log(`  要手動確認:       ${unknownCount}件`);

    if (unknownCount > 0) {
        console.log('\n  ⚠️  カテゴリ未推定（手動でSKILL.mdに追記を推奨）:');
        discovered.filter(d => !d.category).forEach(d => {
            console.log(`    - "${d.name || d.id}" (ラベル: "${d.label || '不明'}", ${d.count}回出現)`);
        });
    }

    // 未推定フィールドをスキップリストとして保存
    if (unknownCount > 0 && !DRY_RUN) {
        const skipLogPath = path.join(LOGS_DIR, `unknown_fields_${TARGET_DATE}.json`);
        fs.writeFileSync(skipLogPath, JSON.stringify(
            discovered.filter(d => !d.category).map(d => ({
                name: d.name, id: d.id, label: d.label, type: d.type, count: d.count, urls: d.urls
            })),
            null, 2
        ), 'utf-8');
        console.log(`\n  📋 未推定フィールドを保存: ${skipLogPath}`);
        
        // AIへの手動チューニング依頼プロンプトを出力
        console.log('\n\n' + '🔥'.repeat(30));
        console.log('🤖 AI(Antigravity) への依頼用テキスト');
        console.log('以下のテキストをコピーしてチャットに貼り付けてください：\n');
        console.log(`contact-autoの送信で未知のフィールドが ${unknownCount} 件見つかりました。`);
        console.log(`以下のJSONログを確認して、新しいカテゴリルールの追加や既存ルールの拡張を提案・反映してください。`);
        console.log(`ログパス: ${skipLogPath}`);
        console.log('🔥'.repeat(30) + '\n');
    }

    console.log('');
}

main().catch(e => {
    console.error('\n❌ skill_learner エラー:', e.message);
    process.exit(1);
});
