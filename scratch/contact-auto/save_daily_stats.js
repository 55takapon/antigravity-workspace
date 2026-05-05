#!/usr/bin/env node
/**
 * save_daily_stats.js — 日次送信統計を stats/ に自動保存
 *
 * 使い方:
 *   node save_daily_stats.js --sheets <ID> --sheet-name <NAME>
 *   node save_daily_stats.js --sheets <ID> --sheet-name <NAME> --date 2026-05-05
 *
 * contact_auto.js の終了後に自動実行される。
 * jet-produce.com など EXCLUDE_DOMAINS はカウントしない。
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

// ── 設定 ──
const CRED_PATH = path.join(__dirname, 'google_credentials.json');
const STATS_DIR = path.join(__dirname, 'stats');
const EXCLUDE_DOMAINS = ['jet-produce.com', 'localhost', '127.0.0.1'];

// 日付を JST で YYYY/MM/DD 形式に
function getTodayJST(dateStr) {
  const d = dateStr ? new Date(dateStr) : new Date();
  // JST = UTC+9
  const jst = new Date(d.getTime() + 9 * 60 * 60 * 1000);
  const y = jst.getUTCFullYear();
  const m = String(jst.getUTCMonth() + 1).padStart(2, '0');
  const day = String(jst.getUTCDate()).padStart(2, '0');
  return `${y}/${m}/${day}`;
}

function getFileDateStr(dateStr) {
  const d = dateStr ? new Date(dateStr) : new Date();
  const jst = new Date(d.getTime() + 9 * 60 * 60 * 1000);
  const y = jst.getUTCFullYear();
  const m = String(jst.getUTCMonth() + 1).padStart(2, '0');
  const day = String(jst.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// ── 引数解析 ──
const args = process.argv.slice(2);
let spreadsheetId = null;
let sheetNames = [];
let dateOverride = null;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--sheets' && args[i + 1]) spreadsheetId = args[i + 1];
  if (args[i] === '--sheet-name' && args[i + 1]) sheetNames.push(args[i + 1]);
  if (args[i] === '--date' && args[i + 1]) dateOverride = args[i + 1];
}

// --sheet-name は複数指定可 or カンマ区切り対応
sheetNames = sheetNames.flatMap(s => s.split(',').map(x => x.trim()));

if (!spreadsheetId || sheetNames.length === 0) {
  console.error('使い方: node save_daily_stats.js --sheets <ID> --sheet-name <NAME> [--date YYYY-MM-DD]');
  process.exit(1);
}

async function collectSheetStats(sheets, spreadsheetId, sheetName, targetDate) {
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: `'${sheetName}'`,
  });
  const values = res.data.values || [];
  if (values.length < 2) return null;

  const headers = values[0];
  const rows = values.slice(1);

  const col = (name) => headers.indexOf(name);
  const urlCol    = col('問い合わせフォームURL');
  const dateCol   = col('送信日');
  const statusCol = col('送信○×');
  const reasonCol = col('送信不可理由');

  let tried = 0, maru = 0, delta = 0, batsu = 0, mi = 0;
  let excludeCount = 0, skipPreexist = 0, skipNoUrl = 0, skipNg = 0;
  const failureReasons = {};

  for (const row of rows) {
    const url    = (row[urlCol]    || '').trim();
    const date   = (row[dateCol]   || '').trim();
    const status = (row[statusCol] || '').trim();
    const reason = (row[reasonCol] || '').trim();

    if (!url || !url.startsWith('http')) { skipNoUrl++; continue; }

    let hostname = '';
    try { hostname = new URL(url).hostname; } catch(e) {}
    if (EXCLUDE_DOMAINS.some(d => hostname.includes(d))) { excludeCount++; continue; }

    if (date && date !== targetDate) { skipPreexist++; continue; }

    // 5/5に試みた行:
    //  - 送信日が今日 (〇/△)
    //  - 送信日が空でもstatusが入っている (× や 未 は日付を書かない仕様)
    //    ただし「前日以前に送信済み」は上でスキップ済み
    const hasStatus = status && status !== '';
    if (date === targetDate || hasStatus) {
      tried++;
      if (status === '〇') maru++;
      else if (status === '△') delta++;
      else if (status === '×') {
        batsu++;
        // 失敗理由を分類
        const r = reason.toLowerCase();
        let category = 'その他';
        if (r.includes('recaptcha') || r.includes('送信ボタン')) category = 'reCAPTCHA/ボタン未検出';
        else if (r.includes('バリデーション')) category = 'バリデーションエラー';
        else if (r.includes('用途限定') || r.includes('採用')) category = '用途限定（採用等）';
        else if (r.includes('営業') || r.includes('遠慮')) category = '営業お断り検出';
        else if (r.includes('タイムアウト') || r.includes('timeout')) category = 'タイムアウト';
        failureReasons[category] = (failureReasons[category] || 0) + 1;
      }
      else if (status === '未') mi++;
    } else if (reason && !date && !status) {
      skipNg++;
    }
  }

  const successRate = tried > 0 ? Math.round(((maru + delta) / tried) * 1000) / 10 : 0;

  return {
    sheet: sheetName,
    total_tried: tried,
    success_maru: maru,
    success_delta: delta,
    fail_batsu: batsu,
    unknown_mi: mi,
    success_rate: successRate,
    skip_preexist: skipPreexist,
    skip_no_url: skipNoUrl,
    skip_exclude: excludeCount,
    skip_ng_reason: skipNg,
    failure_reasons: failureReasons,
  };
}

async function main() {
  const targetDate = getTodayJST(dateOverride);
  const fileDate   = getFileDateStr(dateOverride);

  console.log(`\n📊 save_daily_stats — ${targetDate}`);
  console.log(`   シート: ${sheetNames.join(', ')}`);

  if (!fs.existsSync(CRED_PATH)) {
    console.error('❌ google_credentials.json なし');
    process.exit(1);
  }

  const credentials = JSON.parse(fs.readFileSync(CRED_PATH, 'utf-8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  // 既存のstatsファイルがあれば読み込んでマージ（別シート追加対応）
  const statsFile = path.join(STATS_DIR, `stats_${fileDate}.json`);
  let existing = null;
  if (fs.existsSync(statsFile)) {
    try { existing = JSON.parse(fs.readFileSync(statsFile, 'utf-8')); } catch(e) {}
  }

  const sheetResults = existing?.sheets_detail || [];

  for (const sheetName of sheetNames) {
    const result = await collectSheetStats(sheets, spreadsheetId, sheetName, targetDate);
    if (!result) { console.log(`  ⚠️ ${sheetName}: データなし`); continue; }

    // 既存の同シート結果を置き換え
    const idx = sheetResults.findIndex(r => r.sheet === sheetName);
    if (idx >= 0) sheetResults[idx] = result;
    else sheetResults.push(result);

    console.log(`  ✅ ${sheetName}: 試行 ${result.total_tried}件 | 成功 ${result.success_maru + result.success_delta}件 | 送信率 ${result.success_rate}%`);
  }

  // 集計（全シート合算）
  const totals = sheetResults.reduce((acc, r) => {
    acc.total_tried    += r.total_tried;
    acc.success_maru   += r.success_maru;
    acc.success_delta  += r.success_delta;
    acc.fail_batsu     += r.fail_batsu;
    acc.unknown_mi     += r.unknown_mi;
    acc.skip_preexist  += r.skip_preexist;
    acc.skip_no_url    += r.skip_no_url;
    acc.skip_exclude   += r.skip_exclude;
    acc.skip_ng_reason += r.skip_ng_reason;
    for (const [k, v] of Object.entries(r.failure_reasons || {})) {
      acc.failure_reasons[k] = (acc.failure_reasons[k] || 0) + v;
    }
    return acc;
  }, {
    total_tried: 0, success_maru: 0, success_delta: 0,
    fail_batsu: 0, unknown_mi: 0,
    skip_preexist: 0, skip_no_url: 0, skip_exclude: 0, skip_ng_reason: 0,
    failure_reasons: {},
  });

  const overallRate = totals.total_tried > 0
    ? Math.round(((totals.success_maru + totals.success_delta) / totals.total_tried) * 1000) / 10
    : 0;

  const statsData = {
    date: fileDate,
    generated_at: new Date().toISOString(),
    spreadsheet_id: spreadsheetId,
    sheets_processed: sheetNames,
    // 全シート合算
    total_tried:    totals.total_tried,
    success_maru:   totals.success_maru,
    success_delta:  totals.success_delta,
    fail_batsu:     totals.fail_batsu,
    unknown_mi:     totals.unknown_mi,
    success_rate:   overallRate,
    skip_preexist:  totals.skip_preexist,
    skip_no_url:    totals.skip_no_url,
    skip_exclude:   totals.skip_exclude,
    skip_ng_reason: totals.skip_ng_reason,
    failure_reasons: totals.failure_reasons,
    // シート別詳細
    sheets_detail: sheetResults,
  };

  if (!fs.existsSync(STATS_DIR)) fs.mkdirSync(STATS_DIR, { recursive: true });
  fs.writeFileSync(statsFile, JSON.stringify(statsData, null, 2), 'utf-8');

  console.log(`\n  💾 保存完了: stats/stats_${fileDate}.json`);
  console.log(`  📈 全体送信率: ${overallRate}%（試行${totals.total_tried}件 / 成功${totals.success_maru + totals.success_delta}件）`);
}

main().catch(e => { console.error('❌ save_daily_stats エラー:', e.message); process.exit(1); });
