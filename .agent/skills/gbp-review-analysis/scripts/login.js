const { chromium } = require('playwright');
const path = require('path');

async function loginToGoogle() {
  console.log('ログイン用ブラウザを起動しています...');
  const userDataDir = path.join(__dirname, '..', 'chrome_profile');
  
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    locale: 'ja-JP',
    viewport: { width: 1280, height: 1024 }
  });

  const pages = context.pages();
  const page = pages.length > 0 ? pages[0] : await context.newPage();

  // Bot検知を回避するための偽装処理
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  console.log('Googleマップに移動します。手動でログインを行ってください。');
  console.log('（ログインが完了したら、このウィンドウは開いたままでAIにお知らせください）');
  await page.goto("https://www.google.com/maps");

  // スクリプトが終了しないように待機
  await new Promise(() => {});
}

loginToGoogle();
