/**
 * GBP月次レポート バッチ生成スクリプト
 *
 * 使い方:
 *   node batch_report.js              # 前月を自動判定、全クライアント対象
 *   node batch_report.js --month 4    # 月を指定
 *
 * フロー:
 *   フェーズ1: データ確認 → 対象クライアントを自動検出
 *   フェーズ2: 全クライアントのHTML/PDFを一括自動生成
 *   フェーズ3: 担当者よりメッセージを1社ずつ確認・入力
 *   フェーズ4: メッセージ込みでPDFを確定
 *   フェーズ5: 完了サマリー表示
 */
const path = require('path');
const fs   = require('fs');
const readline = require('readline');
const { chromium } = require('playwright');
const { calculateMainKPIs, generateRecommendations } = require('./calculate_kpis');
const { renderHTML } = require('./render_html');
const { scrapeCompetitors } = require('./scrape_competitors');
const { CLIENTS, SHEET_URL } = require('./client_registry');

// ────────────────────────────────────────────────────────────
// 設定
// ────────────────────────────────────────────────────────────
const OUTPUT_DIR = path.join(__dirname, '..', 'reports');

// Competitors are defined per-client in client_registry.js (see CLIENTS[].competitors)


// ────────────────────────────────────────────────────────────
// ユーティリティ
// ────────────────────────────────────────────────────────────
function getTargetMonth() {
  const args = process.argv.slice(2);
  const idx  = args.indexOf('--month');
  if (idx !== -1 && args[idx + 1]) return parseInt(args[idx + 1]);
  // デフォルト: 前月
  const d = new Date();
  return d.getMonth() === 0 ? 12 : d.getMonth(); // getMonth()は0始まり → 1月=0
}

async function fetchSheet(url) {
  const csvUrl = url.replace(/\/edit.*$/, '/export?format=csv');
  const res    = await fetch(csvUrl);
  if (!res.ok) throw new Error(`Sheet fetch failed: ${res.statusText}`);
  const text = await res.text();
  function parseCSV(str) {
    const rows = [];
    const lines = str.split('\n');
    for (let line of lines) {
      line = line.replace(/\r$/, '');
      if (!line) continue;
      const row = [];
      let cur = '';
      let inQuote = false;
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          if (inQuote && line[i+1] === '"') {
            cur += '"'; i++;
          } else {
            inQuote = !inQuote;
          }
        } else if (char === ',' && !inQuote) {
          row.push(cur.trim());
          cur = '';
        } else {
          cur += char;
        }
      }
      row.push(cur.trim());
      rows.push(row);
    }
    return rows;
  }
  return parseCSV(text);
}

function extractClientBlock(rows, clientName, campus) {
  let start = -1;
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    if (campus) {
      if (r[0].includes(clientName) && r[1] && r[1].includes(campus)) { start = i; break; }
    } else {
      if (r[0].includes(clientName)) { start = i; break; }
    }
  }
  if (start === -1) return null;
  let end = rows.length;
  for (let i = start + 1; i < rows.length; i++) {
    const f = rows[i][0];
    if (!f) { end = i; break; }
    if (f !== '月' && !/^\d{4}-\d{2}$/.test(f)) { end = i; break; }
  }
  return rows.slice(start, end);
}

function hasDataForMonth(block, month) {
  if (!block) return false;
  const prefix = `2026-${month.toString().padStart(2, '0')}`;
  const row = block.find(r => r[0] === prefix);
  if (!row) return false;
  // 閲覧数(col1)が入力済みかどうか
  return row[1] !== '' && !isNaN(parseInt(row[1]));
}

function extractDataForMonth(block, targetMonth) {
  const targetPrefix = `2026-${targetMonth.toString().padStart(2, '0')}`;
  const prevPrefix   = targetMonth > 1 ? `2026-${(targetMonth - 1).toString().padStart(2, '0')}` : null;

  let currentRow = null, prevRow = null;
  const trendViews = [], trendReviews = [];

  for (let i = 2; i < block.length; i++) {
    const row = block[i];
    if (!row[0]) continue;
    if (row[0] === targetPrefix) currentRow = row;
    if (prevPrefix && row[0] === prevPrefix) prevRow = row;
    const m = row[0].match(/^2026-(\d{2})$/);
    if (m && row[1] !== '') {
      const mNum = parseInt(m[1]);
      const v = parseInt(row[1].replace(/,/g, '')), rv = parseInt(row[5].replace(/,/g, ''));
      if (!isNaN(v))  trendViews.push({ month: mNum + '月', value: v });
      if (!isNaN(rv)) trendReviews.push({ month: mNum + '月', value: rv });
    }
  }
  if (!currentRow) return null;

  const getVal = (row, idx) => {
    let v = row[idx];
    if (!v || v === '' || v === '設定なし') return null;
    v = v.replace(/,/g, '');
    const n = parseFloat(v);
    return isNaN(n) ? v : n;
  };

  const mapRow = (row) => !row ? {} : {
    performance: {
      '閲覧数（合計）':       getVal(row, 1),
      'ウェブサイトクリック数': getVal(row, 4),
      'ルート検索数':          getVal(row, 3),
      '電話発信数':            getVal(row, 2),
    },
    reviews: {
      '口コミ総数（累計）': getVal(row, 5),
      '平均評価（★）':     getVal(row, 7),
    },
    posts:            { '当月投稿数': getVal(row, 8) },
    targetReviewCount: getVal(row, 6) || 30,
  };

  const cur  = mapRow(currentRow);
  const prev = mapRow(prevRow);
  return {
    header: {
      clientName: block[0][0],
      industry:   block[0][0],
      category:   '',
      startMonth: ''
    },
    month: targetMonth,
    performance:      cur.performance,
    prevPerformance:  prev.performance || {},
    reviews:          cur.reviews,
    prevReviews:      prev.reviews || {},
    posts:            cur.posts,
    targetReviewCount: cur.targetReviewCount,
    skipRules:        ['calls'],
    trendViews, trendReviews,
    queries: [],
    actionLog: { actions: '', results: '' },
  };
}

function extractPrevMessage(slug, month) {
  if (!fs.existsSync(OUTPUT_DIR)) return null;

  // First try to preserve the current month's message if it exists
  const currentMonthStr = month.toString().padStart(2, '0');
  const currentHtml = path.join(OUTPUT_DIR, `${slug}_monthly_2026${currentMonthStr}.html`);
  if (fs.existsSync(currentHtml)) {
    const content = fs.readFileSync(currentHtml, 'utf-8');
    const match = content.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
    if (match) {
      const msg = match[1].replace(/<[^>]+>/g, '').trim();
      if (!msg.startsWith('※') && msg !== '') return msg;
    }
  }

  // Fallback to previous month
  const prevM   = month - 1;
  if (prevM < 1) return null;
  const prevHtml = path.join(OUTPUT_DIR, `${slug}_monthly_2026${prevM.toString().padStart(2, '0')}.html`);
  if (!fs.existsSync(prevHtml)) return null;
  const content = fs.readFileSync(prevHtml, 'utf-8');
  const match   = content.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
  if (!match) return null;
  const msg = match[1].replace(/<[^>]+>/g, '').trim();
  return (msg.startsWith('※') || msg === '') ? null : msg;
}

async function htmlToPDF(htmlContent, outputPath) {
  const browser = await chromium.launch({ headless: true });
  const page    = await browser.newPage();
  const tmpHtml = outputPath.replace(/\.pdf$/, '.html');
  fs.writeFileSync(tmpHtml, htmlContent, 'utf-8');
  await page.goto(`file://${path.resolve(tmpHtml)}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.pdf({
    path: outputPath, format: 'A4', printBackground: true,
    displayHeaderFooter: false,
    margin: { top: '12mm', right: '0mm', bottom: '12mm', left: '0mm' },
    preferCSSPageSize: true,
  });
  await browser.close();
  return { pdfPath: outputPath, htmlPath: tmpHtml };
}

function generateReportHTML(data, mainKPIs, recommendations, competitors, customMessage) {
  data.competitors = competitors;
  return renderHTML({ ...data, mainKPIs, recommendations, customMessage });
}

function ask(rl, question) {
  return new Promise(resolve => rl.question(question, resolve));
}

// ────────────────────────────────────────────────────────────
// メイン処理
// ────────────────────────────────────────────────────────────
async function main() {
  const month = getTargetMonth();
  const year  = new Date().getFullYear();
  const monthStr = month.toString().padStart(2, '0');

  console.log('');
  console.log('╔════════════════════════════════════════════╗');
  console.log(`║  GBP月次レポート バッチ生成 — ${year}年${month}月     ║`);
  console.log('╚════════════════════════════════════════════╝');

  if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  // ── フェーズ1: データ確認 ──────────────────────────────────
  console.log('\n📋 フェーズ1: スプレッドシートからデータを確認中...');
  const rows = await fetchSheet(SHEET_URL);

  const targets = [];    // データありクライアント
  const skipped = [];    // データなし

  for (const client of CLIENTS) {
    const block = extractClientBlock(rows, client.name, client.campus || null);
    if (hasDataForMonth(block, month)) {
      const data = extractDataForMonth(block, month);
      if (data) {
        // campusがある場合は表示名を南校/北校付きに上書き
        if (client.campus) data.header.clientName = client.name + '(' + client.campus + ')';
        targets.push({ ...client, block, data });
        console.log(`  ✅ ${data.header.clientName} — データあり`);
      }
    } else {
      skipped.push(client);
      const label = client.campus ? client.name + '(' + client.campus + ')' : client.name;
      console.log(`  ⏭  ${label} — データなし（スキップ）`);
    }
  }

  if (targets.length === 0) {
    console.log('\n❌ 対象クライアントが見つかりません。スプレッドシートにデータを入力してください。');
    process.exit(0);
  }

  console.log(`\n対象: ${targets.length}社 / スキップ: ${skipped.length}社`);
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const confirm = await ask(rl, '\nこの内容でレポート生成を開始しますか？ [y/n] > ');
  if (confirm.trim().toLowerCase() !== 'y') {
    rl.close(); console.log('中止しました。'); process.exit(0);
  }

  // ── フェーズ2: メッセージ抽出と一括生成 ────────────────────────
  console.log('\n⚙️  フェーズ2: HTML/PDF 一括生成（メッセージ自動引き継ぎ）中...');
  const generated = [];

  for (const client of targets) {
    try {
      const { data, slug } = client;
      
      // メッセージを抽出（生成前に取得！）
      let msg = extractPrevMessage(slug, month);
      if (!msg) msg = '';

      const mainKPIs        = calculateMainKPIs(data);
      const recommendations  = generateRecommendations(data, data.skipRules, data.targetReviewCount);
      // クライアント固有の競合リストを使用
      const clientComps = client.competitors || [];
      const scrapedComps = await scrapeCompetitors(clientComps);
      const competitors = [
        ...scrapedComps,
        { name: data.header.clientName, isSelf: true,
          reviewCount: data.reviews['口コミ総数（累計）'],
          rating:      data.reviews['平均評価（★）'] }
      ];
      const html = generateReportHTML(data, mainKPIs, recommendations, competitors, msg);
      const pdfPath = path.join(OUTPUT_DIR, `${slug}_monthly_2026${monthStr}.pdf`);
      await htmlToPDF(html, pdfPath);
      console.log(`  ✅ ${client.name} — 生成完了`);
      generated.push({ client, data, mainKPIs, recommendations, competitors, pdfPath });
    } catch (e) {
      console.error(`  ❌ ${client.name} — エラー: ${e.message}`);
    }
  }

  // ── フェーズ3: 完了サマリー ───────────────────────────────
  console.log('\n╔════════════════════════════════════════════╗');
  console.log(`║  ✅ ${year}年${month}月分 レポート生成完了             ║`);
  console.log('╚════════════════════════════════════════════╝');
  console.log(`\n生成済み: ${generated.length}社`);
  generated.forEach(item => {
    const msg = item.msg;
    const msgNote = msg ? `「${msg.slice(0, 20)}${msg.length > 20 ? '…' : ''}」` : '（空欄）';
    console.log(`  📄 ${item.client.name}  担当者メッセージ: ${msgNote}`);
    console.log(`     ${item.pdfPath}`);
  });
  if (skipped.length > 0) {
    console.log(`\nスキップ（データなし）: ${skipped.length}社`);
    skipped.forEach(c => console.log(`  ⏭  ${c.name}`));
  }
}

main().catch(err => {
  console.error('❌ エラー:', err);
  process.exit(1);
});
