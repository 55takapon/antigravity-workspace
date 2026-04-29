/**
 * GBP診断 統合実行スクリプト
 * 
 * Usage: node run_diagnostic.js "GoogleマップURL"
 * Output:
 *   - diagnostic_report_{name}_{date}.html  (PDF化用)
 *   - diagnostic_report_{name}_{date}_notebook.txt  (NotebookLM用)
 *   - diagnostic_data_{name}_{date}.json  (生データ)
 */

const fs = require('fs');
const path = require('path');
const { scrapeGBP } = require('./scrape_gbp');
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText, generateSalesPitchText } = require('./generate_report');

async function runDiagnostic(url, options = {}) {
  const {
    outputDir = process.cwd(),
    headless = true,
    maxReviews = 20,
    competitorSearch = true
  } = options;

  console.log('╔══════════════════════════════════════════╗');
  console.log('║   GBP MEO 診断レポート 自動生成ツール    ║');
  console.log('╚══════════════════════════════════════════╝');
  console.log(`\n入力URL: ${url}\n`);

  // STEP 1: データ収集
  console.log('━━━ STEP 1/3: データ収集 ━━━');
  const data = await scrapeGBP(url, {
    headless,
    maxReviews,
    competitorSearch
  });

  if (!data.basic.name) {
    console.error('❌ ビジネス情報を取得できませんでした。URLを確認してください。');
    return null;
  }

  // STEP 2: スコアリング
  console.log('\n━━━ STEP 2/3: スコアリング ━━━');
  const result = analyzeGBP(data);

  console.log(`  ビジネス名: ${result.businessName}`);
  console.log(`  業種判定: ${result.industry.label}`);
  console.log(`  総合スコア: ${result.totalRank.rank} (${result.totalScore}/100)`);
  console.log('  5軸スコア:');
  for (const axis of result.axes) {
    console.log(`    ${axis.rank.rank} ${axis.label}: ${axis.score}点`);
  }
  console.log('  伸びしろTOP3:');
  for (const item of result.top3) {
    console.log(`    ${item.rank}. ${item.improvement.summary}`);
  }

  // STEP 3: レポート生成
  console.log('\n━━━ STEP 3/3: レポート生成 ━━━');
  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const safeName = (result.businessName || 'unknown')
    .replace(/[/\\?%*:|"<>\s]/g, '_')
    .substring(0, 20);

  // HTMLレポート
  const html = generateHTML(result, data);
  const htmlFile = path.join(outputDir, `diagnostic_report_${safeName}_${timestamp}.html`);
  fs.writeFileSync(htmlFile, html, 'utf-8');
  console.log(`  ✅ HTML: ${htmlFile}`);

  // NotebookLMテキスト
  const notebook = generateNotebookText(result, data);
  const notebookFile = path.join(outputDir, `diagnostic_report_${safeName}_${timestamp}_notebook.txt`);
  fs.writeFileSync(notebookFile, notebook, 'utf-8');
  console.log(`  ✅ NotebookLM: ${notebookFile}`);

  // 営業用訴求トーク
  const pitchText = generateSalesPitchText(result, data);
  const pitchFile = path.join(outputDir, `diagnostic_sales_pitch_${safeName}_${timestamp}.txt`);
  fs.writeFileSync(pitchFile, pitchText, 'utf-8');
  console.log(`  ✅ 営業訴求トーク: ${pitchFile}`);

  // 生データ（JSON）
  const jsonData = { raw: data, analysis: result };
  const jsonFile = path.join(outputDir, `diagnostic_data_${safeName}_${timestamp}.json`);
  fs.writeFileSync(jsonFile, JSON.stringify(jsonData, null, 2), 'utf-8');
  console.log(`  ✅ データ: ${jsonFile}`);

  console.log('\n╔══════════════════════════════════════════╗');
  console.log('║          診断レポート生成完了！           ║');
  console.log('╚══════════════════════════════════════════╝');

  return { data, result, files: { html: htmlFile, notebook: notebookFile, json: jsonFile } };
}

// CLI実行
if (require.main === module) {
  const url = process.argv[2];
  if (!url) {
    console.error('Usage: node run_diagnostic.js "GoogleマップURL"');
    console.error('Example: node run_diagnostic.js "https://maps.google.com/maps?cid=12345"');
    process.exit(1);
  }

  runDiagnostic(url).then(result => {
    if (!result) process.exit(1);
  }).catch(err => {
    console.error('エラー:', err);
    process.exit(1);
  });
}

module.exports = { runDiagnostic };
