/**
 * verify_report.js — GBP月次レポート品質チェック
 *
 * ■ 目的:
 *   スプレッドシートの元データとレポートHTML内の数値が一致しているかを突合検証する。
 *   それだけ。それ以上のことはしない。
 *
 * ■ 前提（レポート作成プロセス）:
 *   1. 前月のHTMLを複製してベースにする
 *   2. スプレッドシートからKPI数値（閲覧数・電話・ルート・Webクリック等）を取得し更新
 *   3. ベンチマーク（競合）の評価点数・口コミ数をWebスクレイピングで取得し更新
 *   4. 担当者コメントは前月のまま出力（必要に応じて手動で書き換える）
 *   5. 本スクリプトで「2で取得した数値が正しくHTMLに反映されたか」を突合チェック
 *
 *   前月複製が前提のため、「データ混在」「ベンチマーク空欄」「コメント空欄」は
 *   プロセスを正しく踏めば起きない。起きたらプロセスの問題であり、
 *   このスクリプトで検知する責務ではない。
 *
 * ■ 使い方:
 *   node verify_report.js              # 最新月の全レポートをチェック
 *   node verify_report.js --month 4    # 4月分を指定
 */
const fs = require('fs');
const path = require('path');

const REPORT_DIR = path.join(require('os').homedir(), '.gemini', 'antigravity', '.agent', 'clients', '00monthly-reports');
const { CLIENTS, SHEET_URL } = require('../../gbp-monthly-report/client_registry');

const REGISTRY = Object.fromEntries(CLIENTS.map(c => [c.slug, {
  name:        c.name,
  campus:      c.campus || null,
  displayName: c.campus ? c.name + '(' + c.campus + ')' : c.name,
}]));

// ────────────────────────────────────────────────
let customCsvPath = null;
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--csv' && args[i + 1]) customCsvPath = args[++i];
}

async function fetchSheetData() {
  let text;
  if (customCsvPath) {
    text = fs.readFileSync(customCsvPath, 'utf8');
  } else {
    const csvUrl = SHEET_URL.replace(/\/edit.*$/, '/export?format=csv');
    const res = await fetch(csvUrl);
    if (!res.ok) throw new Error(`Sheet fetch failed: ${res.statusText}`);
    text = await res.text();
  }

  const rows = [];
  const lines = text.split('\n');
  for (let line of lines) {
    line = line.replace(/\r$/, '');
    if (!line) continue;
    const row = [];
    let cur = '';
    let inQuote = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        if (inQuote && line[i+1] === '"') { cur += '"'; i++; }
        else inQuote = !inQuote;
      } else if (char === ',' && !inQuote) {
        row.push(cur.trim()); cur = '';
      } else {
        cur += char;
      }
    }
    row.push(cur.trim());
    rows.push(row);
  }
  return rows;
}

// ────────────────────────────────────────────────
// シートからクライアントブロックのデータ行を取得
// ────────────────────────────────────────────────
function getSheetValues(rows, clientName, campus, targetMonth) {
  const prefix = `2026-${targetMonth.toString().padStart(2, '0')}`;

  // ブロック検出
  let blockStart = -1;
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    if (campus) {
      if (r[0].includes(clientName) && r[1] && r[1].includes(campus)) { blockStart = i; break; }
    } else {
      if (r[0].includes(clientName)) { blockStart = i; break; }
    }
  }
  if (blockStart === -1) return null;

  // 対象月の行を探す
  for (let i = blockStart + 2; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) break;
    if (r[0] === prefix) {
      const getNum = (val) => {
        if (!val || val === '' || val === '設定なし') return null;
        const n = parseFloat(val.replace(/,/g, ''));
        return isNaN(n) ? null : n;
      };
      return {
        views:    getNum(r[1]),
        calls:    getNum(r[2]),
        routes:   getNum(r[3]),
        clicks:   getNum(r[4]),
      };
    }
  }
  return null;
}

// ────────────────────────────────────────────────
// HTMLレポートからKPI数値を抽出
// ────────────────────────────────────────────────
function extractHTMLValues(content) {
  const getKPI = (label) => {
    const re = new RegExp(`<div class="kpi-value">([\\d,]+)</div>\\s*<div class="kpi-label">${label}</div>`);
    const m = content.match(re);
    if (!m) return null;
    return parseInt(m[1].replace(/,/g, ''), 10);
  };

  return {
    views:  getKPI('閲覧数'),
    clicks: getKPI('Webクリック'),
    routes: getKPI('ルート検索'),
    calls:  getKPI('電話発信'),
  };
}

// ────────────────────────────────────────────────
// 単一レポートの数値突合検査
// ────────────────────────────────────────────────
function verifyReport(filePath, sheetValues) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const slug = path.basename(filePath).replace(/_monthly_.*$/, '');
  const errors = [];
  const registryClient = REGISTRY[slug];

  // slugの存在確認（registry未登録ならチェック不能）
  if (!registryClient) {
    errors.push(`slug "${slug}" が client_registry.js に存在しません — チェック不能`);
    return { errors };
  }

  // シートデータがなければチェック不能
  if (!sheetValues) {
    errors.push(`シートから "${registryClient.displayName}" のデータが取得できませんでした — チェック不能`);
    return { errors };
  }

  // 数値突合チェック（これだけが本スクリプトの責務）
  const htmlValues = extractHTMLValues(content);

  const compare = (label, sheetVal, htmlVal) => {
    if (sheetVal === null) return; // シートにデータなし → スキップ
    if (htmlVal === null) {
      errors.push(`[突合NG] ${label}: シート=${sheetVal}, レポート=取得不可`);
      return;
    }
    if (sheetVal !== htmlVal) {
      errors.push(`[突合NG] ${label}: シート=${sheetVal}, レポート=${htmlVal}（不一致）`);
    }
  };

  compare('閲覧数', sheetValues.views, htmlValues.views);
  compare('Webクリック', sheetValues.clicks, htmlValues.clicks);
  compare('ルート検索', sheetValues.routes, htmlValues.routes);
  compare('電話発信', sheetValues.calls, htmlValues.calls);

  return { errors };
}

// ────────────────────────────────────────────────
// メイン
// ────────────────────────────────────────────────
async function main() {
  if (!fs.existsSync(REPORT_DIR)) {
    console.error('Report directory not found:', REPORT_DIR);
    process.exit(1);
  }

  // 月指定
  const args = process.argv.slice(2);
  const monthIdx = args.indexOf('--month');
  let targetMonth = null;

  const files = fs.readdirSync(REPORT_DIR).filter(f => f.endsWith('.html'));
  const months = [...new Set(files.map(f => {
    const m = f.match(/_monthly_\d{4}(\d{2})/);
    return m ? parseInt(m[1]) : null;
  }).filter(Boolean))].sort((a, b) => a - b);

  if (monthIdx !== -1 && args[monthIdx + 1]) {
    targetMonth = parseInt(args[monthIdx + 1]);
  } else {
    targetMonth = months[months.length - 1];
  }

  const monthStr = targetMonth.toString().padStart(2, '0');
  const targetFiles = files.filter(f => f.includes(`_monthly_2026${monthStr}`));

  console.log(`🔍 GBPレポート数値突合チェック — ${targetMonth}月分（${targetFiles.length}ファイル）`);
  console.log('');

  // スプレッドシートからソースデータを取得
  console.log('📊 スプレッドシートから元データを取得中...');
  let sheetRows = null;
  try {
    sheetRows = await fetchSheetData();
    console.log(`   ✅ ${sheetRows.length}行取得\n`);
  } catch (e) {
    console.error(`   ❌ シート取得失敗（${e.message}）`);
    console.error('   シートデータなしでは数値突合ができません。中断します。');
    process.exit(1);
  }

  let hasError = false;
  let totalErrors = 0;

  for (const file of targetFiles) {
    const filePath = path.join(REPORT_DIR, file);
    const slug = file.replace(/_monthly_.*$/, '');
    const client = REGISTRY[slug];
    const label = client ? client.displayName : slug;

    // シートからこのクライアントの元データを取得
    let sheetValues = null;
    if (client) {
      sheetValues = getSheetValues(sheetRows, client.name, client.campus, targetMonth);
    }

    const { errors } = verifyReport(filePath, sheetValues);

    if (errors.length > 0) {
      console.log(`❌ [NG] ${label}`);
      errors.forEach(e => console.log(`   🔴 ${e}`));
      hasError = true;
      totalErrors += errors.length;
    } else {
      console.log(`✅ [OK] ${label} — 全数値一致`);
    }
  }

  // 未生成クライアント検出
  console.log('');
  const reportSlugs = new Set(targetFiles.map(f => f.replace(/_monthly_.*$/, '')));
  const missingSlugs = Object.keys(REGISTRY).filter(s => !reportSlugs.has(s));
  if (missingSlugs.length > 0) {
    console.log(`⚠️ レポート未生成のクライアント:`);
    missingSlugs.forEach(s => console.log(`   ⏭ ${REGISTRY[s].displayName} (${s})`));
  }

  console.log('');
  console.log(`━━━ サマリー ━━━`);
  console.log(`  チェック対象: ${targetFiles.length}ファイル`);
  console.log(`  数値不一致エラー: ${totalErrors}件`);

  if (hasError) {
    console.log('\n⚠️ 数値突合チェックに失敗しました。レポートの数値を修正してください。');
    process.exit(1);
  } else {
    console.log('\n🎉 全レポートの数値突合チェックを通過しました。');
  }
}

main();
