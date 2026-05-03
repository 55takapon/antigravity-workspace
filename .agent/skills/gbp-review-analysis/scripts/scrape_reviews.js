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
  // タブのセレクタ（仕様変更に備えてbuttonタグ制約を外す）
  reviewTab: '[aria-label*="クチコミ"], [aria-label*="口コミ"], [data-tab-id="reviews"]',
  sortButton: 'button[aria-label="クチコミの並べ替え"], button[data-value="Sort"], button.g88R1[aria-label*="並べ替え"], button[aria-label="並べ替え"]',
  // 「新しい順」メニュー項目
  sortNewest: '[data-index="1"], [role="menuitemradio"]:nth-child(2)',
  // 個別口コミ要素
  reviewItem: '[data-review-id], div.jftiEf',
  // 口コミ内の各フィールド
  reviewerName: '.d4r55, .WNxzHc a',
  reviewRating: '.kvMYJc, .kvMYob, span[role="img"][aria-label*="星"]',
  reviewDate: '.rsqaWe, .rsqawe, .xRkPPb',
  reviewText: '.wiI7pd, .wiI7cb, .MyEned span',
  reviewMoreButton: 'button.w8nwRe, button[aria-label="もっと見る"]',
  // オーナー返信
  ownerReply: '.CDe7pd .wiI7pd, .CDe7pd .wiI7cb, .CDe7pd .MyEned',
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

  // プロファイル保存用ディレクトリ
  const userDataDir = path.join(__dirname, '..', 'chrome_profile');
  
  // ログイン状態を保持するPersistent Contextで起動（headless: falseで画面表示）
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    locale: 'ja-JP',
    timezoneId: 'Asia/Tokyo',
    viewport: { width: 1280, height: 1024 }
  });
  
  const pages = context.pages();
  const page = pages.length > 0 ? pages[0] : await context.newPage();

  // Bot検知を回避するための偽装処理
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });

  try {
    // STEP 1: ページを開く
    console.log('📖 Googleマップを開いています...');
    // 短縮URL対応のため、domcontentloaded後に十分な固定待機
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await randomDelay(8000, 12000);
    
    console.log(`   リダイレクト後URL: ${page.url()}`);
    await page.screenshot({ path: path.join(__dirname, '..', `debug_1_loaded_${clientName}.png`) });

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
      console.log('   タブクリック成功、読み込み待機...');
      // 口コミ要素が現れるまで最大10秒待機
      await page.waitForSelector(SELECTORS.reviewItem, { timeout: 10000 }).catch(() => console.log('   (Timeout waiting for reviews)'));
      await randomDelay(2000, 3000);
    } else {
      console.log('   ⚠️ クチコミタブが見つかりませんでした');
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
    const extractedReviews = [];
    // 重複防止用セット: DOMに同じ口コミが複数存在する場合への根本的対応
    const seenIds = new Set();
    const seenFingerprints = new Set();
    for (const el of reviewElements) {
      try {
        const textEl = await el.$(SELECTORS.reviewText);
        const text = textEl ? (await textEl.innerText()).trim() : '';

        // 全件抽出のためテキストが空でもスキップしない（星だけの評価も対象）

        const id = await el.getAttribute('data-review-id');

        // 重複チェック 1: GoogleのレビューIDがあればそれで一意判定
        if (id && seenIds.has(id)) continue;
        if (id) seenIds.add(id);

        // 重複チェック 2: IDがない場合は「投稿者名+日時文字」で指紋印を生成し一意性を保証
        const dateEl = await el.$(SELECTORS.reviewDate);
        const dateText = dateEl ? (await dateEl.innerText()).trim() : '';

        const authorEl = await el.$(SELECTORS.reviewerName);
        const author = authorEl ? (await authorEl.innerText()).trim() : '';

        if (!id) {
          const fingerprint = `${author}||${dateText}`;
          if (seenFingerprints.has(fingerprint)) continue;
          seenFingerprints.add(fingerprint);
        }

        // オーナー返信（汎用的なテキスト探索も併用）
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

        let ownerReply = '';
        const replyEl = await el.$(SELECTORS.ownerReply);
        if (replyEl) {
          ownerReply = (await replyEl.innerText()).trim();
        } else {
          // フォールバック: "オーナーからの返信"というテキストを持つ要素を探す
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

    // 公式メタデータの抽出（総合評価、総件数、業種カテゴリ、店舗名）
    console.log('📊 店舗のメタデータを抽出中...');
    const metadata = await page.evaluate(() => {
      let rating = 0;
      let reviewCount = 0;
      let category = '不明';
      let bName = '不明';

      try {
        // 店舗名の抽出 (h1要素)
        const h1El = document.querySelector('h1');
        if (h1El) bName = h1El.innerText.trim();

        // よくあるGoogle Mapsの評価テキスト（例: "4.5"）
        const ratingEls = Array.from(document.querySelectorAll('div, span')).filter(el => el.innerText && el.innerText.match(/^[\d.]+$/));
        if (ratingEls.length > 0) {
          const mainRating = document.querySelector('div.F7nice, div.jANrlb, div.fontDisplayLarge');
          if (mainRating) {
            const match = mainRating.innerText.match(/([\d.]+)/);
            if (match) rating = parseFloat(match[1]);
          }
        }

        // 件数（例: "47 件のクチコミ"）
        const countEls = Array.from(document.querySelectorAll('span, div')).filter(el => el.innerText && el.innerText.includes('件のクチコミ'));
        if (countEls.length > 0) {
          const match = countEls[0].innerText.match(/([\d,]+)\s*件のクチコミ/);
          if (match) reviewCount = parseInt(match[1].replace(/,/g, ''), 10);
        }

        // カテゴリ（例: お好み焼き店）
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

    console.log(`\n✅ 完了！${extractedReviews.length}件の口コミ（テキストなし含む全件）を抽出しました。`);

    // STEP 7: JSON出力
    const dateStr = getJSTDateStr();
    // clientName はファイル名などに使う識別子（英数字）、メタデータのbusinessNameは表示名
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

    console.log(`\n✅ 完了！${extractedReviews.length}件の口コミを抽出しました。`);
    console.log(`   出力: ${outputPath}`);
    console.log(`   終了時刻: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}\n`);

    return outputData;

  } catch (err) {
    console.error(`\n❌ エラー: ${err.message}`);
    await page.screenshot({ path: path.join(__dirname, '..', `debug_error_${clientName}.png`) });
    return null;
  } finally {
    // STEP 7: ブラウザ終了
    await context.close();
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
