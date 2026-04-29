const { chromium } = require('playwright');
const path = require('path');

async function convert() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  const htmlPath = path.resolve('../reports/みち_月次レポート_2026年03月.html');
  const pdfPath = path.resolve('../reports/みち_月次レポート_2026年03月.pdf');

  await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    displayHeaderFooter: false,
    margin: { top: '12mm', right: '0mm', bottom: '12mm', left: '0mm' },
    preferCSSPageSize: true,
  });

  await browser.close();
  console.log('✅ PDFの書き出しが完了しました: ' + pdfPath);
}

convert().catch(console.error);
