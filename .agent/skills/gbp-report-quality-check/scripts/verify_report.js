/**
 * verify_report.js — GBP月次レポート品質チェック
 *
 * 使い方:
 *   node verify_report.js              # 最新月の全レポートをチェック
 *   node verify_report.js --month 4    # 4月分を指定
 *
 * チェック内容:
 *   1. slug が client_registry に存在するか
 *   2. クライアント名がレポート内に正しく含まれているか（データ混在検知）
 *   3. 閲覧数がゼロ・異常値でないか
 *   4. ベンチマーク（競合データ）が空欄でないか
 *   5. 担当者コメントが空欄でないか
 *   6. skipRulesが正しく反映されているか
 *   7. レポート未生成のクライアントがいないか
 *   8. 【重要】スプレッドシート元データとレポート内の数値が一致するか
 */
const fs = require('fs');
const path = require('path');

const REPORT_DIR = path.join(__dirname, '../../gbp-meo-core/reports');
const { CLIENTS, SHEET_URL } = require('../../gbp-meo-core/monthly-report/client_registry');

const REGISTRY = Object.fromEntries(CLIENTS.map(c => [c.slug, {
  name:        c.name,
  campus:      c.campus || null,
  displayName: c.campus ? c.name + '(' + c.campus + ')' : c.name,
  industry:    c.industry,
  competitors: c.competitors || [],
  skipRules:   c.skipRules || [],
}]));

// ────────────────────────────────────────────────
// スプレッドシートからCSVを取得してパース
// ────────────────────────────────────────────────
async function fetchSheetData() {
  const csvUrl = SHEET_URL.replace(/\/edit.*$/, '/export?format=csv');
  const res = await fetch(csvUrl);
  if (!res.ok) throw new Error(`Sheet fetch failed: ${res.statusText}`);
  const text = await res.text();

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
        reviews:  getNum(r[5]),
        rating:   getNum(r[7]),
        posts:    getNum(r[8]),
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
// 単一レポートの検査
// ────────────────────────────────────────────────
function verifyReport(filePath, sheetValues) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const slug = path.basename(filePath).replace(/_monthly_.*$/, '');
  const errors = [];
  const warnings = [];
  const registryClient = REGISTRY[slug];

  // Check 1: slug存在チェック
  if (!registryClient) {
    errors.push(`slug "${slug}" が client_registry.js に存在しません`);
    return { errors, warnings };
  }

  // Check 2: クライアント名チェック（データ混在検知）
  if (!content.includes(registryClient.name)) {
    errors.push(`クライアント名「${registryClient.name}」がレポート内に見つかりません（データ混在の疑い）`);
  }

  // Check 3: 閲覧数
  const viewMatch = content.match(/<div class="kpi-value">([\d,]+)<\/div>\s*<div class="kpi-label">閲覧数<\/div>/);
  if (viewMatch) {
    const views = parseInt(viewMatch[1].replace(/,/g, ''), 10);
    if (views < 10) errors.push(`異常な閲覧数: ${views}`);
    if (views === 0) errors.push(`閲覧数が0です`);
  } else {
    errors.push('閲覧数のKPIが見つかりません');
  }

  // Check 4: ベンチマーク
  const bmMatch = content.match(/<div class="section-title">📊 ベンチマーク参考<\/div>\s*<table>[\s\S]*?<tbody>([\s\S]*?)<\/tbody>/);
  if (bmMatch) {
    const tbody = bmMatch[1];
    const rows = tbody.match(/<tr[^>]*>[\s\S]*?<\/tr>/g) || [];
    const nonSelfRows = rows.filter(r => !r.includes('background'));
    if (nonSelfRows.length === 0 && registryClient.competitors.length > 0) {
      errors.push(`ベンチマーク（競合）が空（registry上は${registryClient.competitors.length}社定義済み）`);
    }
  } else {
    errors.push('ベンチマーク参考セクションが見つかりません');
  }

  // Check 5: 担当者コメント
  const msgMatch = content.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
  if (msgMatch) {
    const msg = msgMatch[1].replace(/<[^>]+>/g, '').trim();
    if (msg.startsWith('※') || msg === '') {
      warnings.push(`担当者コメントが空欄またはプレースホルダー`);
    }
  } else {
    warnings.push('担当者よりセクションが見つかりません');
  }

  // Check 6: skipRules反映チェック
  if (registryClient.skipRules.includes('posts')) {
    if (content.includes('投稿が') && content.includes('件です（月')) {
      errors.push(`skipRules["posts"]設定済みなのに投稿頻度推奨が出力されています`);
    }
  }

  // Check 7: 【重要】スプレッドシート元データとの数値突合
  if (sheetValues) {
    const htmlValues = extractHTMLValues(content);

    const compare = (label, sheetVal, htmlVal) => {
      if (sheetVal === null) return; // シートにデータなし → スキップ
      if (htmlVal === null) {
        errors.push(`[突合NG] ${label}: シート=${sheetVal}, レポート=取得不可`);
        return;
      }
      if (sheetVal !== htmlVal) {
        errors.push(`[突合NG] ${label}: シート=${sheetVal}, レポート=${htmlVal}（不一致！データ捏造の疑い）`);
      }
    };

    compare('閲覧数', sheetValues.views, htmlValues.views);
    compare('Webクリック', sheetValues.clicks, htmlValues.clicks);
    compare('ルート検索', sheetValues.routes, htmlValues.routes);
    compare('電話発信', sheetValues.calls, htmlValues.calls);
  }

  return { errors, warnings };
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

  console.log(`🔍 GBPレポート品質チェック — ${targetMonth}月分（${targetFiles.length}ファイル）`);
  console.log('');

  // スプレッドシートからソースデータを取得
  console.log('📊 スプレッドシートから元データを取得中...');
  let sheetRows = null;
  try {
    sheetRows = await fetchSheetData();
    console.log(`   ✅ ${sheetRows.length}行取得\n`);
  } catch (e) {
    console.log(`   ⚠️ シート取得失敗（${e.message}）— 数値突合チェックはスキップします\n`);
  }

  let hasError = false;
  let totalErrors = 0;
  let totalWarnings = 0;

  for (const file of targetFiles) {
    const filePath = path.join(REPORT_DIR, file);
    const slug = file.replace(/_monthly_.*$/, '');
    const client = REGISTRY[slug];
    const label = client ? client.displayName : slug;

    // シートからこのクライアントの元データを取得
    let sheetValues = null;
    if (sheetRows && client) {
      sheetValues = getSheetValues(sheetRows, client.name, client.campus, targetMonth);
    }

    const { errors, warnings } = verifyReport(filePath, sheetValues);

    if (errors.length > 0) {
      console.log(`❌ [NG] ${label}`);
      errors.forEach(e => console.log(`   🔴 ${e}`));
      warnings.forEach(w => console.log(`   🟡 ${w}`));
      hasError = true;
      totalErrors += errors.length;
    } else if (warnings.length > 0) {
      console.log(`⚠️ [WARN] ${label}`);
      warnings.forEach(w => console.log(`   🟡 ${w}`));
    } else {
      console.log(`✅ [OK] ${label}`);
      if (sheetValues) console.log(`   📊 数値突合: 全項目一致`);
    }
    totalWarnings += warnings.length;
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
  console.log(`  エラー: ${totalErrors}件`);
  console.log(`  警告: ${totalWarnings}件`);
  console.log(`  数値突合: ${sheetRows ? '実施済み' : 'スキップ（シート取得失敗）'}`);

  if (hasError) {
    console.log('\n⚠️ 品質チェックに失敗しました。修正してください。');
    process.exit(1);
  } else {
    console.log('\n🎉 全レポートの品質チェックを通過しました。');
  }
}

main();
