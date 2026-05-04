/**
 * scrape_reviews.js
 * Playwrightで Googleマップの口コミを全件抽出するスクリプト
 * 
 * Usage:
 *   node scrape_reviews.js --url "GoogleマップURL" --name "client_name"
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// === 設定ブロック（CSSセレクタ集約） ===
const SELECTORS = {
  reviewTab: '[aria-label*="クチコミ"], [aria-label*="口コミ"], [data-tab-id="reviews"]',
  // 個別口コミ要素：[data-review-id]で全要素を取得し、後段でトップレベルのみに絞る
  // div.jftiEfは旧クラス名で現在のGoogleMapsDOMに存在しない可能性があるため属性のみで探す
  reviewItem: '[data-review-id]',
  reviewerName: '.d4r55, .WNxzHc a, .al6Kxe',
  reviewRating: '.kvMYJc, .kvMYob, span[role="img"][aria-label*="星"]',
  reviewDate: '.rsqaWe, .rsqawe, .xRkPPb',
  reviewText: '.wiI7pd, .wiI7cb, .MyEned span',
  reviewMoreButton: 'button.w8nwRe, button[aria-label="もっと見る"]',
  ownerReply: '.CDe7pd .wiI7pd, .CDe7pd .wiI7cb, .CDe7pd .MyEned',
  // 実際のDOMで確認されたクラスを含む拡張セレクタ
  scrollContainer: 'div.m6QErb.DxyBCb, div.m6QErb[aria-label], div[aria-label][data-scroll-y][scrollable="true"]',
};

// === JST日付生成 ===
function getJSTDateStr() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10).replace(/-/g, '');
}

// === ランダム遅延 ===
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

  const userDataDir = path.join(__dirname, '..', 'chrome_profile');
  
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    locale: 'ja-JP',
    timezoneId: 'Asia/Tokyo',
    viewport: { width: 1280, height: 1024 }
  });
  
  const pages = context.pages();
  const page = pages.length > 0 ? pages[0] : await context.newPage();

  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  try {
    // STEP 1: ページを開く
    console.log('📖 Googleマップを開いています...');
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await randomDelay(8000, 12000);
    
    console.log(`   リダイレクト後URL: ${page.url()}`);

    // CAPTCHA検知
    const captcha = await page.$('iframe[title*="reCAPTCHA"]');
    if (captcha) {
      console.error('⚠️ CAPTCHA検出！手動操作が必要です。');
      await context.close();
      return null;
    }

    // STEP 2: 口コミタブに移動
    console.log('📋 口コミタブに移動中...');
    const reviewTabBtn = await page.$(SELECTORS.reviewTab);
    if (reviewTabBtn) {
      await reviewTabBtn.click();
      console.log('   タブクリック成功、読み込み待機...');
      await page.waitForSelector(SELECTORS.reviewItem, { timeout: 10000 }).catch(() => console.log('   (Timeout waiting for reviews)'));
      await randomDelay(2000, 3000);
    } else {
      console.log('   ⚠️ クチコミタブが見つかりませんでした');
    }

    // STEP 3: ソートなし（デフォルト関連度順）で全件取得
    // 「新しい順」ソート後にスクロールコンテナが切り替わりスクロールが効かなくなるため廃止
    console.log('📋 デフォルト順（関連度順）で全件取得します...');
    await randomDelay(1000, 2000);

    // STEP 4: スクロールで全件ロード
    console.log('📜 口コミをスクロールロード中...');

    let lastCount = 0;
    let stableCount = 0;
    const MAX_SCROLL = 200;

    for (let i = 0; i < MAX_SCROLL; i++) {
      // 毎回スクロールコンテナを再取得（DOM変更対応）
      const scrollContainer = await page.$(SELECTORS.scrollContainer);

      if (scrollContainer) {
        await scrollContainer.scrollIntoViewIfNeeded();
        // scrollTopを最下部に設定することで確実にスクロールさせる
        await page.evaluate(el => {
          el.scrollTop = el.scrollHeight;
        }, scrollContainer);
      } else {
        // フォールバック: ページ全体スクロール
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      }

      await randomDelay(2000, 4000);

      const currentItems = await page.$$(SELECTORS.reviewItem);
      const count = currentItems.length;

      if (i % 5 === 0) {
        console.log(`   スクロール ${i}: ${count} 件ロード済み`);
      }

      if (count === lastCount) {
        stableCount++;
        if (stableCount >= 10) {
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
    const extractedReviews = [];
    // IDが必ず存在するから、IDのみで重複管理する
    const seenIds = new Set();

    for (const el of reviewElements) {
      try {
        const textEl = await el.$(SELECTORS.reviewText);
        const text = textEl ? (await textEl.innerText()).trim() : '';

        const id = await el.getAttribute('data-review-id');

        // IDがない要素はスキップ
        if (!id) continue;

        // 【根本対策】祖先要素にも data-review-id があるならネストした子要素 — スキップ
        const isNested = await el.evaluate(node => {
          let parent = node.parentElement;
          while (parent) {
            if (parent.hasAttribute('data-review-id')) return true;
            parent = parent.parentElement;
          }
          return false;
        });
        if (isNested) continue;

        // 重複チェック: 同一IDは追加しない
        if (seenIds.has(id)) continue;
        seenIds.add(id);

        const dateEl = await el.$(SELECTORS.reviewDate);
        const dateText = dateEl ? (await dateEl.innerText()).trim() : '';

        const authorEl = await el.$(SELECTORS.reviewerName);
        const author = authorEl ? (await authorEl.innerText()).trim() : '';

        // 星評価の取得
        let rating = 0;
        const ratingEl = await el.$(SELECTORS.reviewRating);
        if (ratingEl) {
          const ariaLabel = await ratingEl.getAttribute('aria-label');
          if (ariaLabel) {
            const m = ariaLabel.match(/(\d)/);
            if (m) rating = parseInt(m[1], 10);
          }
        }
        if (rating === 0) {
          const fallbackEls = await el.$$('[aria-label*="星"]');
          for (const fe of fallbackEls) {
            const label = await fe.getAttribute('aria-label');
            const m = label ? label.match(/(\d)\s*つ星/) : null;
            if (m) { rating = parseInt(m[1], 10); break; }
          }
        }

        // オーナー返信
        let ownerReply = '';
        const replyEl = await el.$(SELECTORS.ownerReply);
        if (replyEl) {
          ownerReply = (await replyEl.innerText()).trim();
        } else {
          const replyTextEls = await el.$$('xpath=.//*[contains(text(), "オーナーからの返信")]/..');
          if (replyTextEls.length > 0) {
            ownerReply = (await replyTextEls[0].innerText()).replace('オーナーからの返信', '').trim();
          }
        }

        extractedReviews.push({
          id,
          author,
          rating,
          dateText,
          text,
          ownerReply: ownerReply || null,
          scrapedAt: new Date().toISOString()
        });
      } catch (err) {
        // 個別要素のパースエラーはスキップ
      }
    }

    // STEP 7: 公式メタデータの抽出
    console.log('📊 店舗のメタデータを抽出中...');
    const metadata = await page.evaluate(() => {
      let rating = 0;
      let reviewCount = 0;
      let category = '不明';
      let bName = '不明';

      try {
        const h1El = document.querySelector('h1');
        if (h1El) bName = h1El.innerText.trim();

        const mainRating = document.querySelector('div.F7nice, div.jANrlb, div.fontDisplayLarge');
        if (mainRating) {
          const match = mainRating.innerText.match(/([\d.]+)/);
          if (match) rating = parseFloat(match[1]);
        }

        const countEls = Array.from(document.querySelectorAll('span, div')).filter(el => el.innerText && el.innerText.includes('件のクチコミ'));
        if (countEls.length > 0) {
          const match = countEls[0].innerText.match(/([\d,]+)\s*件のクチコミ/);
          if (match) reviewCount = parseInt(match[1].replace(/,/g, ''), 10);
        }

        const catBtn = document.querySelector('button.DkEaL');
        if (catBtn) {
          category = catBtn.innerText;
        } else {
          const buttons = Array.from(document.querySelectorAll('button'));
          const catBtnAlt = buttons.find(b => b.innerText && (b.innerText.includes('店') || b.innerText.includes('レストラン') || b.innerText.includes('料理') || b.innerText.includes('カフェ')));
          if (catBtnAlt) category = catBtnAlt.innerText;
        }
      } catch (e) {}

      return { averageRating: rating, totalReviews: reviewCount, businessCategory: category, businessName: bName };
    });
    
    console.log(`   取得結果: 店舗名=${metadata.businessName}, 総合評価=${metadata.averageRating}, 総件数=${metadata.totalReviews}, カテゴリ=${metadata.businessCategory}`);

    console.log(`\n✅ 完了！${extractedReviews.length}件の口コミを抽出しました。`);

    // STEP 8: JSON出力
    const dateStr = getJSTDateStr();
    const safeClientId = clientName.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
    
    const outputData = {
      clientId: safeClientId,
      businessName: metadata.businessName !== '不明' ? metadata.businessName : clientName,
      scrapedUrl: url,
      scrapedAt: new Date().toISOString(),
      metadata: metadata,
      reviews: extractedReviews
    };

    const outputName = `review_data_${safeClientId}_${dateStr}.json`;
    const outputPath = path.join(__dirname, '..', outputName);

    fs.writeFileSync(outputPath, JSON.stringify(outputData, null, 2), 'utf-8');
    console.log(`✅ 完了！${extractedReviews.length}件の口コミを抽出しました。`);
    console.log(`   出力: ${outputPath}`);
    console.log(`   終了時刻: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}\n`);

  } finally {
    await context.close();
  }
}

// === CLI実行 ===
if (require.main === module) {
  const args = process.argv.slice(2);
  const urlIdx = args.indexOf('--url');
  const nameIdx = args.indexOf('--name');

  if (urlIdx === -1 || nameIdx === -1) {
    console.error('Usage: node scrape_reviews.js --url <GoogleMapsURL> --name <client_name>');
    process.exit(1);
  }

  scrapeReviews(args[urlIdx + 1], args[nameIdx + 1]).catch(err => {
    console.error('❌ エラーが発生しました:', err);
    process.exit(1);
  });
}

module.exports = { scrapeReviews };
