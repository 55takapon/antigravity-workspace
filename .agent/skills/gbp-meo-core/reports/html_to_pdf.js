const { chromium } = require('C:/Users/hangy/.gemini/antigravity/node_modules/playwright');
const path = require('path');

(async () => {
  const htmlPath = path.resolve(__dirname, 'みち_月次レポート_2026年03月.html');
  const pdfPath = path.resolve(__dirname, 'みち_月次レポート_2026年03月.pdf');

  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await page.goto(`file:///${htmlPath.replace(/\\/g, '/')}`, { waitUntil: 'networkidle' });
  
  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' }
  });

  console.log(`PDF generated: ${pdfPath}`);
  await browser.close();
})();
