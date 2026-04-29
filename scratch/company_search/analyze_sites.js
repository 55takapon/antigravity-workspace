// 問題サイトの実HTMLデータを解析するスクリプト
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const urls = [
  'https://three-dots.co.jp/',
  'https://webgram.jp/',
  'https://cog-web.com/',
  'https://suneight.co.jp/',
  'https://bankluck-japan.com/',
  'https://baroque-ad.co.jp/',
  'https://mindfree.jp/',
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const url of urls) {
    console.log('\n=== ' + url + ' ===');
    const page = await browser.newPage();
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
      const title = await page.evaluate(() => document.title);
      const ogSiteName = await page.evaluate(() => {
        const el = document.querySelector('meta[property="og:site_name"]');
        return el ? el.getAttribute('content') : '';
      });
      const ogTitle = await page.evaluate(() => {
        const el = document.querySelector('meta[property="og:title"]');
        return el ? el.getAttribute('content') : '';
      });
      console.log('title: ' + JSON.stringify(title));
      console.log('og:site_name: ' + JSON.stringify(ogSiteName));
      console.log('og:title: ' + JSON.stringify(ogTitle));

      // 会社概要ページを探す
      const companyLink = await page.evaluate(() => {
        const links = Array.from(document.querySelectorAll('a[href]'));
        for (const a of links) {
          const href = a.href;
          const text = (a.textContent || '').trim();
          if (/company|about|corporate/i.test(href) ||
              /会社概要|会社案内|会社情報/i.test(text)) {
            return href;
          }
        }
        return null;
      });
      console.log('companyPage: ' + companyLink);

      if (companyLink) {
        await page.goto(companyLink, { waitUntil: 'domcontentloaded', timeout: 15000 });
        const aboutTitle = await page.evaluate(() => document.title);
        const aboutOg = await page.evaluate(() => {
          const el = document.querySelector('meta[property="og:site_name"]');
          return el ? el.getAttribute('content') : '';
        });
        console.log('about_title: ' + JSON.stringify(aboutTitle));
        console.log('about_og: ' + JSON.stringify(aboutOg));

        const bodyText = await page.evaluate(() => (document.body && document.body.textContent) || '');
        const labelIdx = bodyText.search(/会社名|商号|法人名/);
        if (labelIdx >= 0) {
          const around = bodyText.substring(labelIdx, labelIdx + 80).replace(/\s+/g, ' ');
          console.log('label_context: ' + JSON.stringify(around));
        } else {
          console.log('label_context: NOT FOUND');
        }
      }
    } catch (e) {
      console.log('ERROR: ' + e.message.substring(0, 80));
    }
    await page.close();
  }
  await browser.close();
})();
