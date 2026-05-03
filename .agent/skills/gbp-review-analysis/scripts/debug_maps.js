const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function debugMaps() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ locale: 'ja-JP' });
  const page = await context.newPage();

  // Bot検知を回避するための偽装処理
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  console.log('Navigating...');
  await page.goto("https://maps.app.goo.gl/kGXY9P6pee7nXxw77", { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 10000));

  console.log('Taking screenshot of overview...');
  await page.screenshot({ path: path.join(__dirname, '..', `debug_overview.png`) });

  // タブボタンをすべて取得して出力
  console.log('Finding tabs...');
  const buttons = await page.$$('button, a, div');
  let reviewTabBtn = null;
  for (const btn of buttons) {
    const text = await btn.innerText().catch(() => '');
    const aria = await btn.getAttribute('aria-label').catch(() => '');
    if ((text && text.includes('クチコミ')) || (aria && aria.includes('クチコミ'))) {
      console.log(`Found candidate: text='${text.replace(/\n/g, ' ')}', aria-label='${aria}'`);
      reviewTabBtn = btn;
    }
  }

  if (reviewTabBtn) {
    console.log('Clicking review tab...');
    await reviewTabBtn.click();
    await new Promise(r => setTimeout(r, 5000));
    console.log('Taking screenshot of reviews...');
    await page.screenshot({ path: path.join(__dirname, '..', `debug_reviews.png`) });
    
  } else {
    console.log('Review tab not found!');
  }
  
  const html = await page.content();
  fs.writeFileSync(path.join(__dirname, '..', 'debug_page.html'), html);
  console.log('HTML saved to debug_page.html');

  await browser.close();
}

debugMaps();
