'use strict';

/**
 * daily-report-collector.js v3.0
 * Claude Code のセッショントランスクリプト（~/.claude/projects/<プロジェクト>/<セッションID>.jsonl）を
 * 走査し、指定日（JST）の全セッションから以下を抽出する：
 *   1. ユーザーの実際のリクエスト一覧（DONE照合用）
 *   2. ユーザーの指摘・トラブル（キーワード検出。config/incident-keywords.json で管理）
 *
 * 使い方:
 *   node daily-report-collector.js            … 今日（JST）のセッションを走査
 *   node daily-report-collector.js --date 2026-07-16 … 指定日（JST）を走査
 *
 * 終了コード: 0=正常 / 1=実行エラー / 2=検出0件（異常の可能性。データソースを確認すること）
 *
 * ⚠️ このスクリプトは「補助ツール」。キーワードなしの重要事象は目視確認が必要。
 *    旧v2.0のAntigravity brain/走査は2026-07-17に廃止（brain/は2026-05-19以降更新なし）。
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

const PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const KEYWORDS_PATH = path.join(__dirname, '..', 'config', 'incident-keywords.json');

// ---------- 引数 ----------
function parseArgs(argv) {
  const r = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      r[key] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
    }
  }
  return r;
}
const args = parseArgs(process.argv.slice(2));

// ---------- JSTの日付境界（タイムスタンプはUTC保存のため明示変換する） ----------
const JST_OFFSET_MS = 9 * 60 * 60 * 1000;

function jstDateString(date) {
  return new Date(date.getTime() + JST_OFFSET_MS).toISOString().split('T')[0];
}

const targetDate = args.date || jstDateString(new Date());
if (!/^\d{4}-\d{2}-\d{2}$/.test(targetDate)) {
  console.error(`エラー: --date は YYYY-MM-DD 形式で指定してください（指定値: ${targetDate}）`);
  process.exit(1);
}
// JSTのその日 00:00〜24:00 をUTCに換算
const dayStartUtc = new Date(new Date(targetDate + 'T00:00:00Z').getTime() - JST_OFFSET_MS);
const dayEndUtc = new Date(dayStartUtc.getTime() + 24 * 60 * 60 * 1000);

// ---------- キーワード読み込み ----------
let KEYWORDS = [];
let EXCEPTIONS = [];
try {
  const kw = JSON.parse(fs.readFileSync(KEYWORDS_PATH, 'utf8'));
  KEYWORDS = kw.keywords || [];
  EXCEPTIONS = kw.exceptions || [];
} catch (e) {
  console.error(`エラー: キーワード設定を読めません: ${KEYWORDS_PATH}\n${e.message}`);
  process.exit(1);
}

function detectKeywords(text) {
  // 除外語を先に消してから検出することで「なんでも」→「なんで」等の誤検出を防ぐ
  let scrubbed = text;
  for (const ex of EXCEPTIONS) scrubbed = scrubbed.split(ex).join('');
  return KEYWORDS.filter(w => scrubbed.includes(w));
}

// ---------- ユーザー発話の抽出 ----------
function extractUserText(obj) {
  if (obj.type !== 'user' || obj.isSidechain || obj.isMeta) return null;
  const msg = obj.message;
  if (!msg || msg.role !== 'user') return null;

  let text = '';
  if (typeof msg.content === 'string') {
    text = msg.content;
  } else if (Array.isArray(msg.content)) {
    // tool_result等を除き、人間が打ったテキストブロックだけを拾う
    text = msg.content
      .filter(c => c && c.type === 'text' && typeof c.text === 'string')
      .map(c => c.text)
      .join('\n');
  }
  text = text.trim();
  if (!text) return null;
  // システム由来のノイズ行を除外
  if (text.startsWith('<command-name>')) return null;
  if (text.startsWith('<local-command')) return null;
  if (text.startsWith('<system-reminder>') && !text.includes('</system-reminder>\n')) return null;
  if (text.startsWith('Caveat:')) return null;
  if (text.startsWith('[Request interrupted')) return null;
  if (text.startsWith('<task-notification>')) return null;
  // system-reminderブロックが先頭に付いた実発話は、ブロックを剥がして本文だけ残す
  text = text.replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g, '').trim();
  return text || null;
}

// ---------- セッション走査 ----------
function analyzeSessionFile(filePath) {
  const lines = fs.readFileSync(filePath, 'utf8').split('\n');
  const requests = [];
  const incidents = [];
  let summary = null;
  let firstTime = null;

  for (const line of lines) {
    if (!line.trim()) continue;
    let obj;
    try { obj = JSON.parse(line); } catch { continue; }

    if (obj.type === 'summary' && obj.summary) summary = obj.summary;

    const ts = obj.timestamp ? new Date(obj.timestamp) : null;
    if (!ts || ts < dayStartUtc || ts >= dayEndUtc) continue;

    const text = extractUserText(obj);
    if (!text) continue;

    if (!firstTime) firstTime = ts;
    requests.push({ time: ts, text });

    const found = detectKeywords(text);
    if (found.length > 0) {
      incidents.push({ time: ts, keywords: found, text });
    }
  }
  return { requests, incidents, summary, firstTime };
}

function main() {
  if (!fs.existsSync(PROJECTS_DIR)) {
    console.error(`エラー: セッションデータが見つかりません: ${PROJECTS_DIR}`);
    console.error('Claude Code のセッション保存先が変わった可能性があります。スキルの改修が必要です。');
    process.exit(1);
  }

  const sessions = [];
  for (const projDir of fs.readdirSync(PROJECTS_DIR)) {
    const full = path.join(PROJECTS_DIR, projDir);
    let stat;
    try { stat = fs.statSync(full); } catch { continue; }
    if (!stat.isDirectory()) continue;

    for (const file of fs.readdirSync(full)) {
      if (!file.endsWith('.jsonl')) continue;
      const fp = path.join(full, file);
      // mtimeが対象日の開始（UTC換算）より前のファイルは対象日の発話を含み得ないためスキップ
      if (fs.statSync(fp).mtime < dayStartUtc) continue;
      const result = analyzeSessionFile(fp);
      if (result.requests.length === 0) continue;
      sessions.push({
        project: projDir,
        sessionId: path.basename(file, '.jsonl'),
        filePath: fp,
        ...result,
      });
    }
  }

  sessions.sort((a, b) => a.firstTime - b.firstTime);

  console.log('\n===== Daily Report Collector v3.0（Claude Code対応） =====');
  console.log(`対象日: ${targetDate}（JST 00:00〜24:00）`);
  console.log(`検出セッション数: ${sessions.length}\n`);

  let totalIncidents = 0;
  const jstTime = d => new Date(d.getTime() + JST_OFFSET_MS).toISOString().substring(11, 16);

  for (const s of sessions) {
    console.log(`📁 [${s.project}] ${s.sessionId}`);
    console.log(`   ファイル: ${s.filePath}`);
    if (s.summary) console.log(`   タイトル: ${s.summary}`);
    console.log(`   ユーザーリクエスト数: ${s.requests.length} / 🚨 指摘/トラブル: ${s.incidents.length}件`);
    console.log('   📋 リクエスト一覧（DONEに漏れがないか照合すること）:');
    for (const r of s.requests) {
      console.log(`     [${jstTime(r.time)}] ${r.text.substring(0, 100).replace(/\n/g, ' ')}`);
    }
    for (const inc of s.incidents) {
      totalIncidents++;
      console.log(`   ⚡ INCIDENT候補 [${jstTime(inc.time)}] KW: ${inc.keywords.join(', ')}`);
      console.log(`       → ${inc.text.substring(0, 120).replace(/\n/g, ' ')}`);
    }
    console.log('');
  }

  console.log('===== サマリー =====');
  console.log(`全セッション: ${sessions.length} / 指摘・トラブル候補: ${totalIncidents}件`);

  // レポートヘッダー用（転記ミス防止のためコピペ可能な形で出力する）
  console.log('\n----- レポートヘッダー用（この行をそのまま貼り付ける） -----');
  console.log(`> 検出セッション数: ${sessions.length}件（daily-report-collector v3.0 / 対象日 ${targetDate} JST）`);
  console.log('------------------------------------------------------------');

  console.log('\n⚠️  このスクリプトは補助ツール。キーワードなしの重要事象は各セッションの内容確認が必要。');

  if (sessions.length === 0) {
    console.log('\n🔴 検出0件です。作業した日なら異常です。以下を確認してください:');
    console.log(`   1. 対象日の指定ミス（--date ${targetDate} で正しいか）`);
    console.log(`   2. データソースの変更（${PROJECTS_DIR} が現役か）`);
    console.log('   0件のままレポートを作成してはならない。原因をユーザーに報告すること。');
    process.exit(2);
  }
}

main();
