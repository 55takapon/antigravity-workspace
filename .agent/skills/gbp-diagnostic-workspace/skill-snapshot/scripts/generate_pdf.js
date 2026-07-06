/**
 * Playwright PDF生成スクリプト
 * HTMLレポートからプロフェッショナルなPDFを生成する
 * 
 * Usage: node scripts/generate_pdf.js <HTMLファイルパス>
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

async function generatePDF(htmlPath) {
  if (!htmlPath) {
    console.error('Usage: node scripts/generate_pdf.js <HTMLファイルパス>');
    process.exit(1);
  }

  const absolutePath = path.resolve(htmlPath);
  if (!fs.existsSync(absolutePath)) {
    console.error(`ファイルが見つかりません: ${absolutePath}`);
    process.exit(1);
  }

  const pdfPath = absolutePath.replace(/\.html$/, '.pdf');

  console.log('📄 PDF生成開始...');
  console.log(`   入力: ${absolutePath}`);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // HTMLファイルを開く
  await page.goto(`file://${absolutePath}`, { waitUntil: 'networkidle' });

  // Webフォント読み込み完了を待機
  await page.waitForTimeout(2000);

  // PDF生成
  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,          // 背景色・グラデーションを印刷
    displayHeaderFooter: false,     // ブラウザのURL・日付を非表示
    margin: {
      top: '12mm',
      right: '0mm',
      bottom: '12mm',
      left: '0mm',
    },
    preferCSSPageSize: true,        // CSSの@pageルールを優先
  });

  await browser.close();

  const stats = fs.statSync(pdfPath);
  const sizeMB = (stats.size / 1024 / 1024).toFixed(1);

  console.log(`✅ PDF生成完了: ${pdfPath}`);
  console.log(`   サイズ: ${sizeMB}MB`);

  return pdfPath;
}

// CLI実行
if (require.main === module) {
  const htmlPath = process.argv[2];
  generatePDF(htmlPath).catch(err => {
    console.error('PDF生成エラー:', err);
    process.exit(1);
  });
}

module.exports = { generatePDF };
