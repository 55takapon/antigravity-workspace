/**
 * GBP月次レポート生成 — メインスクリプト
 * 
 * Usage:
 *   node generate_monthly_report.js --csv "data/英和塾_2026.csv" --month 3
 *   node generate_monthly_report.js --csv "data/英和塾_2026.csv" --month 3 --output "reports/"
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { parseReportCSV } = require('./parse_csv');
const { calculateMainKPIs, generateRecommendations } = require('./calculate_kpis');
const { renderHTML } = require('./render_html');

/**
 * コマンドライン引数をパースする
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--csv' && args[i + 1]) {
      options.csv = args[++i];
    } else if (args[i] === '--month' && args[i + 1]) {
      options.month = parseInt(args[++i]);
    } else if (args[i] === '--output' && args[i + 1]) {
      options.output = args[++i];
    } else if (args[i] === '--message' && args[i + 1]) {
      options.message = args[++i];
    }
  }

  return options;
}

/**
 * データが入力されている月のトレンドデータを構築する（1〜12月）
 */
function buildTrendData(csvPath, metricKey, section) {
  const months = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];
  const trend = [];

  for (let m = 1; m <= 12; m++) {
    try {
      const data = parseReportCSV(csvPath, m);
      const sectionData = section === 'performance' ? data.performance : data.reviews;
      const val = sectionData[metricKey] ?? null;
      if (val !== null) {
        trend.push({ month: months[m - 1], value: val });
      }
    } catch (e) {
      // skip
    }
  }

  return trend;
}

/**
 * HTMLをPDFに変換する
 */
async function htmlToPDF(htmlContent, outputPath) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // HTMLを一時ファイルに保存
  const tempHtml = outputPath.replace(/\.pdf$/, '.html');
  fs.writeFileSync(tempHtml, htmlContent, 'utf-8');

  await page.goto(`file://${path.resolve(tempHtml)}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000); // Webフォント読み込み待機

  await page.pdf({
    path: outputPath,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: false,
    margin: { top: '12mm', right: '0mm', bottom: '12mm', left: '0mm' },
    preferCSSPageSize: true,
  });

  await browser.close();

  // HTML一時ファイルも残す（確認用）
  return { pdfPath: outputPath, htmlPath: tempHtml };
}

/**
 * メイン処理
 */
async function main() {
  const options = parseArgs();

  if (!options.csv) {
    console.error('❌ CSVファイルを指定してください');
    console.error('Usage: node generate_monthly_report.js --csv "data/英和塾_2026.csv" --month 3');
    process.exit(1);
  }

  if (!options.month || options.month < 1 || options.month > 12) {
    console.error('❌ 月を1〜12で指定してください（--month 3）');
    process.exit(1);
  }

  const csvPath = path.resolve(options.csv);
  if (!fs.existsSync(csvPath)) {
    console.error(`❌ CSVファイルが見つかりません: ${csvPath}`);
    process.exit(1);
  }

  console.log('📊 GBP月次レポート生成開始...');
  console.log(`   CSV: ${csvPath}`);
  console.log(`   対象月: ${options.month}月`);

  // 1. CSVパース
  console.log('   [1/5] CSVをパース中...');
  const data = parseReportCSV(csvPath, options.month);
  console.log(`   → 顧客名: ${data.header.clientName}`);

  // 2. KPI計算
  console.log('   [2/5] KPIを計算中...');
  const mainKPIs = calculateMainKPIs(data);
  const recommendations = generateRecommendations(data, data.skipRules || [], data.targetReviewCount || null);
  console.log(`   → 推奨アクション: ${recommendations.length}件`);
  if (data.skipRules && data.skipRules.length > 0) {
    console.log(`   → 除外ルール: ${data.skipRules.join(', ')}`);
  }

  // 目標口コミ数: CSVヘッダーから読み取り（未設定なら20件）
  const targetReviewCount = data.targetReviewCount || 20;
  console.log(`   → 目標口コミ数: ${targetReviewCount}件`);

  // 3. トレンドデータ構築
  console.log('   [3/5] トレンドデータを構築中...');
  const trendViews = buildTrendData(csvPath, '閲覧数（合計）', 'performance');
  const trendReviews = buildTrendData(csvPath, '口コミ総数（累計）', 'reviews');

  // 4. HTML生成
  console.log('   [4/5] HTMLを生成中...');
  const reportData = {
    header: data.header,
    month: options.month,
    mainKPIs,
    reviews: data.reviews,
    posts: data.posts,
    queries: data.queries,
    competitors: data.competitors,
    actionLog: data.actionLog,
    recommendations,
    trendViews,
    trendReviews,
    targetReviewCount,
    customMessage: options.message || '',
  };
  const html = renderHTML(reportData);

  // 5. PDF生成
  console.log('   [5/5] PDFを生成中...');
  const monthNames = ['01','02','03','04','05','06','07','08','09','10','11','12'];
  const outputDir = options.output ? path.resolve(options.output) : path.join(require('os').homedir(), 'gbp-clients', '_monthly-reports');
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  const fileName = `${data.header.clientName}_月次レポート_${new Date().getFullYear()}年${monthNames[options.month - 1]}月`;
  const pdfPath = path.join(outputDir, `${fileName}.pdf`);

  const result = await htmlToPDF(html, pdfPath);

  const stats = fs.statSync(result.pdfPath);
  const sizeMB = (stats.size / 1024 / 1024).toFixed(1);

  console.log('');
  console.log(`✅ レポート生成完了!`);
  console.log(`   PDF: ${result.pdfPath} (${sizeMB}MB)`);
  console.log(`   HTML: ${result.htmlPath}`);
}

if (require.main === module) {
  main().catch(err => {
    console.error('❌ エラー:', err);
    process.exit(1);
  });
}

module.exports = { main };
