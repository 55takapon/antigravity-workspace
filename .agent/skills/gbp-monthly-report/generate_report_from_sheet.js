/**
 * GBP月次レポート生成（Googleスプレッドシート連携版）
 *
 * Usage:
 *   node generate_report_from_sheet.js --url "https://docs.google.com/..." --month 4
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { calculateMainKPIs, generateRecommendations } = require('./calculate_kpis');
const { renderHTML } = require('./render_html');
const { scrapeCompetitors } = require('./scrape_competitors');

// slug -> sheet client info: loaded from client_registry to avoid encoding issues
const { CLIENTS: _CLIENTS } = require('./client_registry');
const SLUG_TO_CLIENT = Object.fromEntries(_CLIENTS.map(c => [c.slug, {
  name:        c.name,
  campus:      c.campus || null,
  displayName: c.campus ? c.name + '(' + c.campus + ')' : c.name,
  competitors: c.competitors || [],
  skipRules:   c.skipRules || [],
}]));


function parseArgs() {
  const args = process.argv.slice(2);
  const options = { url: '', month: 0, output: '', slug: '' };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--url' && args[i + 1])    options.url    = args[++i];
    else if (args[i] === '--month'  && args[i + 1]) options.month  = parseInt(args[++i]);
    else if (args[i] === '--output' && args[i + 1]) options.output = args[++i];
    else if (args[i] === '--slug'   && args[i + 1]) options.slug   = args[++i];
  }
  return options;
}

// Competitors are defined per-client in client_registry.js


async function fetchSheetData(url) {
  // Convert sharing URL to CSV export URL
  let csvUrl = url;
  if (url.includes('/edit')) {
    csvUrl = url.replace(/\/edit.*$/, '/export?format=csv');
  }

  const response = await fetch(csvUrl);
  if (!response.ok) throw new Error(`Failed to fetch CSV: ${response.statusText}`);
  
  const text = await response.text();
  
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

function extractDataForMonth(rows, targetMonth, clientName, campus, clientInfo) {
  const targetPrefix = `2026-${targetMonth.toString().padStart(2, '0')}`;
  const prevPrefix   = targetMonth > 1
    ? `2026-${(targetMonth - 1).toString().padStart(2, '0')}`
    : null;

  // ── Step 1: クライアントブロックを切り出す ──────────────────────────────
  // campus あり = 「英和塾 南校」のように col[0]+col[1] で識別
  // campus なし = col[0] の部分一致
  let blockStart = -1;
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    if (campus) {
      if (r[0].includes(clientName) && r[1] && r[1].includes(campus)) {
        blockStart = i; break;
      }
    } else {
      if (r[0].includes(clientName)) {
        blockStart = i; break;
      }
    }
  }
  if (blockStart === -1) throw new Error(`Client block not found: ${clientName}${campus ? ` ${campus}` : ''}`);

  // ブロック終端
  let blockEnd = rows.length;
  for (let i = blockStart + 1; i < rows.length; i++) {
    const firstCell = rows[i][0];
    if (!firstCell) { blockEnd = i; break; }
    if (firstCell !== '月' && !/^\d{4}-\d{2}$/.test(firstCell)) {
      blockEnd = i; break;
    }
  }

  const block = rows.slice(blockStart, blockEnd);
  // block[0] = クライアント名行, block[1] = 列ヘッダー行, block[2..] = データ行

  // ── Step 2: データ行のパース ────────────────────────────────────────────
  let currentRow = null;
  let prevRow    = null;
  const trendViews   = [];
  const trendReviews = [];

  for (let i = 2; i < block.length; i++) {
    const row = block[i];
    if (!row[0]) continue;

    if (row[0] === targetPrefix) currentRow = row;
    if (prevPrefix && row[0] === prevPrefix) prevRow = row;

    // トレンドデータ収集（データがある月のみ）
    const mMatch = row[0].match(/^2026-(\d{2})$/);
    if (mMatch) {
      const mNum    = parseInt(mMatch[1]);
      const viewVal = parseInt(row[1].replace(/,/g, ''));
      const revVal  = parseInt(row[5].replace(/,/g, ''));
      if (!isNaN(viewVal) && row[1] !== '') trendViews.push({ month: `${mNum}月`, value: viewVal });
      if (!isNaN(revVal)  && row[5] !== '') trendReviews.push({ month: `${mNum}月`, value: revVal });
    }
  }

  if (!currentRow) throw new Error(`No data for month ${targetMonth} in client block`);

  // ── Step 3: 値の取り出し ────────────────────────────────────────────────
  const getVal = (row, index) => {
    let val = row[index];
    if (!val || val === '' || val === '設定なし') return null;
    val = val.replace(/,/g, '');
    const parsed = parseFloat(val);
    return isNaN(parsed) ? val : parsed;
  };

  const mapRow = (row) => {
    if (!row || row.length === 0) return {};
    return {
      performance: {
        '閲覧数（合計）':      getVal(row, 1),
        'ウェブサイトクリック数': getVal(row, 4),
        'ルート検索数':         getVal(row, 3),
        '電話発信数':           getVal(row, 2),
      },
      reviews: {
        '口コミ総数（累計）': getVal(row, 5),
        '平均評価（★）':     getVal(row, 7),
      },
      posts: {
        '当月投稿数': getVal(row, 8),
      },
      targetReviewCount: getVal(row, 6) || 30,
    };
  };

  const current = mapRow(currentRow);
  const prev    = mapRow(prevRow);

  return {
    header: {
      clientName:  clientInfo.displayName || block[0][0],
      industry:    clientInfo.industry || block[0][0],
      category:    clientInfo.industry || '',
      startMonth:  '2026年1月',
    },
    month:            targetMonth,
    performance:      current.performance,
    prevPerformance:  prev.performance   || {},
    reviews:          current.reviews,
    prevReviews:      prev.reviews       || {},
    posts:            current.posts,
    targetReviewCount: current.targetReviewCount,
    skipRules:        [...(clientInfo.skipRules || []), 'calls'],
    trendViews,
    trendReviews,
    queries:          [],
    actionLog:        { actions: '', results: '' },
  };
}

async function htmlToPDF(htmlContent, outputPath) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const tempHtml = outputPath.replace(/\.pdf$/, '.html');
  fs.writeFileSync(tempHtml, htmlContent, 'utf-8');

  await page.goto(`file://${path.resolve(tempHtml)}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000); 

  await page.pdf({
    path: outputPath,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: false,
    margin: { top: '12mm', right: '0mm', bottom: '12mm', left: '0mm' },
    preferCSSPageSize: true,
  });

  await browser.close();
  return { pdfPath: outputPath, htmlPath: tempHtml };
}

/**
 * 前月のHTMLレポートから「担当者より」メッセージを抽出する
 */
function extractPrevMessage(outputDir, clientSlug, month) {
  // First try to preserve the current month's message if it exists (for regeneration)
  const currentMonthStr = month.toString().padStart(2, '0');
  const currentHtml = path.join(outputDir, `${clientSlug}_monthly_2026${currentMonthStr}.html`);
  if (fs.existsSync(currentHtml)) {
    const content = fs.readFileSync(currentHtml, 'utf-8');
    const match = content.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
    if (match) {
      const msg = match[1].replace(/<[^>]+>/g, '').trim();
      if (!msg.startsWith('※') && msg !== '') return msg;
    }
  }

  // Fallback to previous month
  const prevMonth = month - 1;
  if (prevMonth < 1) return null;
  const prevMonthStr = prevMonth.toString().padStart(2, '0');
  const prevHtml = path.join(outputDir, `${clientSlug}_monthly_2026${prevMonthStr}.html`);
  if (!fs.existsSync(prevHtml)) return null;

  const content = fs.readFileSync(prevHtml, 'utf-8');
  const match = content.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
  if (!match) return null;
  const msg = match[1].replace(/<[^>]+>/g, '').trim();
  if (msg.startsWith('※') || msg === '') return null;
  return msg;
}

/**
 * インタラクティブに「担当者より」メッセージを確認・入力する
 */
async function askCustomMessage(month, prevMsg) {
  const readline = require('readline');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  return new Promise(resolve => {
    console.log('');
    console.log('┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('┃ ✉️  「担当者より」セクションのメッセージ');
    console.log('┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    if (prevMsg) {
      console.log(`↳ 先月のメッセージ: 「${prevMsg}」`);
      console.log('  • そのまま使用する場合は Enter');
      console.log('  • 空欄にする場合はsを入力して Enter');
      console.log('  • 新しいメッセージはそのまま入力');
    } else {
      console.log('  （前月分レポートのメッセージなし）');
      console.log('  • メッセージを入力するか、空欄の場合はsを入力して Enter');
    }

    rl.question(`\n${month}月分のメッセージ > `, answer => {
      rl.close();
      const trimmed = answer.trim();
      if (trimmed === '' && prevMsg) {
        // Enter のみ → 先月メッセージをそのまま引き継ぎ
        resolve(prevMsg);
      } else if (trimmed === 's') {
        // s のみ → 空欄
        resolve('');
      } else if (trimmed === '' && !prevMsg) {
        resolve('');
      } else {
        resolve(trimmed);
      }
    });
  });
}

async function main() {
  const options = parseArgs();
  if (!options.url || !options.month) {
    console.error('Usage: node generate_report_from_sheet.js --url "..." --month 4 --slug jetproduce');
    process.exit(1);
  }

  console.log('📊 GBP月次レポート生成開始...');
  console.log(`   対象月: ${options.month}月`);
  
  console.log('   [1/6] スプレッドシートを読み込み中...');
  const rows = await fetchSheetData(options.url);

  const clientInfo = SLUG_TO_CLIENT[options.slug];
  if (!clientInfo) {
    console.error(`❌ クライアントが特定できません。利用可能: ${Object.keys(SLUG_TO_CLIENT).join(', ')}`);
    process.exit(1);
  }
  const displayLabel = clientInfo.displayName || clientInfo.name;
  console.log(`   対象クライアント: ${displayLabel}`);
  const data = extractDataForMonth(rows, options.month, clientInfo.name, clientInfo.campus || null, clientInfo);
  // レポートの表示名をdisplayNameに上書き（campus付きの場合）
  if (clientInfo.displayName) data.header.clientName = clientInfo.displayName;


  console.log('   [2/6] KPIを計算中...');
  const mainKPIs = calculateMainKPIs(data);
  const recommendations = generateRecommendations(data, data.skipRules, data.targetReviewCount);

  console.log('   [3/6] 競合ベンチマークをウェブから取得中...');
  const clientCompetitors = clientInfo.competitors || [];
  const scrapedCompetitors = await scrapeCompetitors(clientCompetitors, outputDir, clientSlug, options.month);
  scrapedCompetitors.push({
    name: data.header.clientName,
    isSelf: true,
    reviewCount: data.reviews['口コミ総数（累計）'],
    rating: data.reviews['平均評価（★）']
  });
  data.competitors = scrapedCompetitors;


  // 出力先を先に確定（前月HTMLを参照するため）
  const outputDir = options.output ? path.resolve(options.output) : path.join(require('os').homedir(), 'gbp-clients', '_monthly-reports');
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
  const clientSlug = options.slug || 'client';
  const monthStr = options.month.toString().padStart(2, '0');
  const fileName = `${clientSlug}_monthly_2026${monthStr}`;
  const pdfPath = path.join(outputDir, `${fileName}.pdf`);

  console.log('   [4/6] 「担当者より」メッセージを確認中...');
  const prevMsg = extractPrevMessage(outputDir, clientSlug, options.month);
  const customMessage = await askCustomMessage(options.month, prevMsg);

  console.log('   [5/6] HTMLを生成中...');
  const reportData = {
    ...data,
    mainKPIs,
    recommendations,
    customMessage,
  };
  const html = renderHTML(reportData);

  console.log('   [6/6] PDFを生成中...');
  const result = await htmlToPDF(html, pdfPath);
  console.log('\n✅ レポート生成完了!');
  console.log(`   PDF: ${result.pdfPath}`);
  console.log(`   HTML: ${result.htmlPath}`);
}

if (require.main === module) {
  main().catch(err => {
    console.error('❌ エラー:', err);
    process.exit(1);
  });
}

module.exports = { main };


