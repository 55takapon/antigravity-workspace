const { chromium } = require('C:/Users/hangy/.gemini/antigravity/node_modules/playwright');
const path = require('path');

(async () => {
  const inputFile = process.argv[2];
  if (!inputFile) {
    console.error('Usage: node html_to_pdf.js <input.html>');
    process.exit(1);
  }

  const htmlPath = path.resolve(__dirname, inputFile);
  const pdfPath = htmlPath.replace(/\.html$/, '.pdf');

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
