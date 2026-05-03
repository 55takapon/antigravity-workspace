/**
 * scrape_reviews.js
 * Playwrightで Googleマップの口コミを全件抽出するスクリプト
 * 
 * 既存Python5スクリプトのベストプラクティスを統合したNode.js版:
 * - ランダム遅延（2-4秒）でbot検知回避
 * - 「もっと見る」ボタンの自動展開
 * - CAPTCHA検知時の通知
 * - 「新しい順」ソートでの取得
 * 
 * Usage:
 *   node scrape_reviews.js --url "GoogleマップURL" --name "client_name"
 *   node scrape_reviews.js --url "https://maps.google.com/maps?cid=XXXXX" --name "bomnal_chicken"
 * 
 * Requirements:
 *   npm install playwright
 *   npx playwright install chromium
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// === 設定ブロック（CSSセレクタ集約） ===
const SELECTORS = {
  // 口コミタブボタン
  reviewTab: 'button[aria-label*="クチコミ"], button[aria-label*="口コミ"], button[data-tab-id="reviews"]',
  // ソートボタン
  sortButton: 'button[aria-label*="並べ替え"], button[data-value="並べ替え"]',
  // 「新しい順」メニュー項目
  sortNewest: '[data-index="1"], [role="menuitemradio"]:nth-child(2)',
  // 個別口コミ要素
  reviewItem: '[data-review-id], div.jftiEf',
  // 口コミ内の各フィールド
  reviewerName: '.d4r55, .WNxzHc a',
  reviewRating: '.kvMYJc, span[role="img"][aria-label*="星"]',
  reviewDate: '.rsqaWe, .xRkPPb',
  reviewText: '.wiI7pd, .MyEned span',
  reviewMoreButton: 'button.w8nwRe, button[aria-label="もっと見る"]',
  // オーナー返信
  ownerReply: '.CDe7pd .wiI7pd, .CDe7pd .MyEned',
  // スクロールコンテナ
  scrollContainer: 'div.m6QErb.DxyBCb, div.m6QErb[aria-label]',
};

// === JST日付生成 ===
function getJSTDateStr() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10).replace(/-/g, '');
}

// === ランダム遅延（2-4秒） ===
function randomDelay(min = 2000, max = 4000) {
  const ms = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise(resolve => setTimeout(resolve, ms));
}

// === メイン処理 ===
async function scrapeReviews(url, clientName) {
  console.log(`\n🔍 口コミ抽出を開始します...`);
  console.log(`   URL: ${url}`);
  console.log(`   クライアント名: ${clientName}`);
  console.log(`   開始時刻: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}\n`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'ja-JP',
    timezoneId: 'Asia/Tokyo',
    viewport: { width: 1280, height: 1024 }
  });

  const page = await context.newPage();

  try {
    // STEP 1: ページを開く
    console.log('📖 Googleマップを開いています...');
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await randomDelay(3000, 6000);

    // CAPTCHA検知
    const captcha = await page.$('iframe[title*="reCAPTCHA"]');
    if (captcha) {
      console.error('⚠️ CAPTCHA検出！手動操作が必要です。');
      await page.screenshot({ path: path.join(__dirname, '..', `debug_captcha_${clientName}.png`) });
      await browser.close();
      return null;
    }

    // STEP 2: 口コミタブに移動
    console.log('📋 口コミタブに移動中...');
    const reviewTabBtn = await page.$(SELECTORS.reviewTab);
    if (reviewTabBtn) {
      await reviewTabBtn.click();
      await randomDelay(2000, 3000);
    }

    // STEP 3: 新しい順にソート
    console.log('🔄 新しい順にソート中...');
    const sortBtn = await page.$(SELECTORS.sortButton);
    if (sortBtn) {
      await sortBtn.click();
      await randomDelay(1000, 2000);
      const newestBtn = await page.$(SELECTORS.sortNewest);
      if (newestBtn) {
        await newestBtn.click();
        await randomDelay(2000, 3000);
      }
    }

    // STEP 4: スクロールで全件ロード
    console.log('📜 口コミをスクロールロード中...');
    const scrollContainer = await page.$(SELECTORS.scrollContainer);

    let lastCount = 0;
    let stableCount = 0;
    const MAX_SCROLL = 200;

    for (let i = 0; i < MAX_SCROLL; i++) {
      if (scrollContainer) {
        await page.evaluate(el => el.scrollBy(0, 2000), scrollContainer);
      } else {
        await page.mouse.wheel(0, 2000);
      }

      await randomDelay(2000, 4000);

      const currentItems = await page.$$(SELECTORS.reviewItem);
      const count = currentItems.length;

      if (i % 5 === 0) {
        console.log(`   スクロール ${i}: ${count} 件ロード済み`);
      }

      if (count === lastCount) {
        stableCount++;
        if (stableCount >= 5) {
          console.log(`   全${count}件ロード完了（安定検知）`);
          break;
        }
      } else {
        stableCount = 0;
      }
      lastCount = count;
    }

    // STEP 5: 「もっと見る」ボタンを全展開
    console.log('📖 口コミ全文を展開中...');
    const moreButtons = await page.$$(SELECTORS.reviewMoreButton);
    for (const btn of moreButtons) {
      try {
        await btn.scrollIntoViewIfNeeded();
        await btn.click();
        await randomDelay(100, 300);
      } catch {
        // 一部のボタンはクリックできない場合がある
      }
    }

    // STEP 6: データ抽出
    console.log('📊 口コミデータを抽出中...');
    const reviewElements = await page.$$(SELECTORS.reviewItem);
    const reviews = [];

    for (const el of reviewElements) {
      try {
        // 投稿者名
        const nameEl = await el.$(SELECTORS.reviewerName);
        const name = nameEl ? (await nameEl.innerText()).trim() : 'Unknown';

        // 星評価
        const ratingEl = await el.$(SELECTORS.reviewRating);
        let rating = 0;
        if (ratingEl) {
          const ariaLabel = await ratingEl.getAttribute('aria-label');
          if (ariaLabel) {
            const m = ariaLabel.match(/(\d)/);
            if (m) rating = parseInt(m[1], 10);
          }
        }

        // 投稿日
        const dateEl = await el.$(SELECTORS.reviewDate);
        const date = dateEl ? (await dateEl.innerText()).trim() : 'Unknown';

        // 口コミ本文
        const textEl = await el.$(SELECTORS.reviewText);
        const text = textEl ? (await textEl.innerText()).trim() : '';

        // テキストなしはスキップ
        if (!text) continue;

        // オーナー返信
        const replyEl = await el.$(SELECTORS.ownerReply);
        const hasOwnerReply = !!replyEl;
        const ownerReplyText = replyEl ? (await replyEl.innerText()).trim() : '';

        reviews.push({
          name,
          rating,
          date,
          text,
          hasOwnerReply,
          ownerReplyText
        });
      } catch (err) {
        // 個別要素のエラーはスキップ
        continue;
      }
    }

    // STEP 7: JSON出力
    const dateStr = getJSTDateStr();
    const output = {
      businessName: clientName,
      sourceUrl: url,
      collectedAt: new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }),
      totalCount: reviews.length,
      reviews
    };

    const outputName = `review_data_${clientName}_${dateStr}.json`;
    const outputPath = path.join(__dirname, '..', outputName);

    fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf-8');

    console.log(`\n✅ 完了！${reviews.length}件の口コミを抽出しました。`);
    console.log(`   出力: ${outputPath}`);
    console.log(`   終了時刻: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}\n`);

    return output;

  } catch (err) {
    console.error(`\n❌ エラー: ${err.message}`);
    await page.screenshot({ path: path.join(__dirname, '..', `debug_error_${clientName}.png`) });
    return null;
  } finally {
    await browser.close();
  }
}

// === CLI実行 ===
if (require.main === module) {
  const args = process.argv.slice(2);
  const urlIdx = args.indexOf('--url');
  const nameIdx = args.indexOf('--name');

  if (urlIdx === -1) {
    console.error('Usage: node scrape_reviews.js --url "GoogleマップURL" --name "client_name"');
    process.exit(1);
  }

  const url = args[urlIdx + 1];
  const name = nameIdx !== -1 ? args[nameIdx + 1] : 'unknown';

  scrapeReviews(url, name);
}

module.exports = { scrapeReviews };
