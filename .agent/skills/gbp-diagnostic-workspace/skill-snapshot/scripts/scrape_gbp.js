/**
 * GBP データ収集スクリプト（Playwright）
 * GoogleマップURLからGBPの公開情報を収集する
 * 
 * Usage: node scrape_gbp.js "https://maps.google.com/..."
 * Output: gbp_data_{timestamp}.json
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * GoogleマップURLからGBPデータを収集
 * @param {string} url - GoogleマップURL
 * @param {object} options - オプション
 * @returns {object} 収集データ
 */
async function scrapeGBP(url, options = {}) {
  const {
    headless = true,
    maxReviews = 20,
    screenshotDir = null,
    competitorSearch = true
  } = options;

  const browser = await chromium.launch({ headless });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'ja-JP',
    viewport: { width: 1280, height: 1024 }
  });
  const page = await context.newPage();

  const data = {
    basic: {},
    reviews: { totalCount: 0, averageRating: 0, items: [] },
    photos: { totalCount: 0 },
    posts: { latestPostDate: null, recentCount: 0 },
    competitors: [],
    meta: {
      scrapedAt: new Date().toISOString(),
      sourceUrl: url
    }
  };

  try {
    console.log('[1/6] GBPページを開いています...');
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);

    if (screenshotDir) {
      await page.screenshot({ path: path.join(screenshotDir, '01_initial.png') });
    }

    // ==========================================
    // STEP 1: 基本情報の取得
    // ==========================================
    console.log('[2/6] 基本情報を取得中...');
    
    // ビジネス名
    data.basic.name = await safeText(page, 'h1');
    
    // カテゴリ
    data.basic.category = await safeText(page, 'button[jsaction*="category"]');
    if (!data.basic.category) {
      // 代替セレクタ
      const categoryEl = await page.$('.DkEaL');
      if (categoryEl) data.basic.category = await categoryEl.innerText();
    }

    // 住所
    data.basic.address = await extractInfoItem(page, '住所', 'address');
    
    // 電話番号
    data.basic.phone = await extractInfoItem(page, '電話', 'phone');
    
    // ウェブサイト
    const websiteEl = await page.$('a[data-item-id="authority"]');
    if (websiteEl) {
      data.basic.website = await websiteEl.getAttribute('href');
    }

    // 営業時間
    data.basic.hours = await extractHours(page);

    // 説明文
    data.basic.description = await extractDescription(page);

    // 属性
    data.basic.attributes = await extractAttributes(page);

    // サービス項目
    data.basic.services = await extractServices(page);

    console.log(`  ビジネス名: ${data.basic.name}`);
    console.log(`  カテゴリ: ${data.basic.category}`);

    // ==========================================
    // STEP 2: 口コミ情報の取得
    // ==========================================
    console.log('[3/6] 口コミ情報を取得中...');

    // 口コミ件数と平均評価
    const ratingText = await safeText(page, '.F7nice span[aria-hidden="true"]');
    if (ratingText) {
      data.reviews.averageRating = parseFloat(ratingText);
    }

    const reviewCountText = await safeText(page, '.F7nice span:last-child');
    if (reviewCountText) {
      const match = reviewCountText.match(/[\d,]+/);
      if (match) data.reviews.totalCount = parseInt(match[0].replace(/,/g, ''));
    }

    // 口コミタブを開いてレビュー詳細を取得
    const reviewTab = await page.$('button[aria-label*="クチコミ"], button[aria-label*="レビュー"], [role="tab"]:has-text("クチコミ")');
    if (reviewTab) {
      await reviewTab.click();
      await page.waitForTimeout(3000);

      // スクロールしてレビューを読み込む
      const scrollable = await page.$('.m6QErb.DxyBCb');
      if (scrollable) {
        let lastCount = 0;
        for (let i = 0; i < 10; i++) {
          await page.evaluate(el => el.scrollBy(0, 3000), scrollable);
          await page.waitForTimeout(1500);
          const items = await page.$$('.jftiEf');
          if (items.length >= maxReviews || items.length === lastCount) break;
          lastCount = items.length;
        }
      }

      // レビュー抽出
      const reviewEls = await page.$$('.jftiEf');
      for (const el of reviewEls.slice(0, maxReviews)) {
        try {
          // 全文展開
          const moreBtn = await el.$('button[aria-label*="もっと見る"], button.w8nwRe');
          if (moreBtn) {
            await moreBtn.click();
            await page.waitForTimeout(300);
          }

          const rating = await el.$eval('.kvMYJc', e => {
            const label = e.getAttribute('aria-label');
            const match = label?.match(/(\d)/);
            return match ? parseInt(match[1]) : 0;
          }).catch(() => 0);

          const text = await el.$eval('.wiI7pd', e => e.innerText).catch(() => '');
          const date = await el.$eval('.rsqaWe', e => e.innerText).catch(() => '');
          const hasOwnerReply = (await el.$('.CDe7pd')) !== null;

          data.reviews.items.push({
            rating,
            text: text.trim(),
            date: date.trim(),
            hasOwnerReply
          });
        } catch (e) { continue; }
      }
    }

    console.log(`  口コミ: ${data.reviews.totalCount}件, 平均${data.reviews.averageRating}星`);
    console.log(`  取得レビュー: ${data.reviews.items.length}件`);

    // ==========================================
    // STEP 3: 写真情報の取得
    // ==========================================
    console.log('[4/6] 写真情報を取得中...');
    
    // 写真タブのカウント
    const photoTab = await page.$('button[aria-label*="写真"], [role="tab"]:has-text("写真")');
    if (photoTab) {
      const photoTabText = await photoTab.innerText();
      const photoMatch = photoTabText.match(/[\d,]+/);
      if (photoMatch) {
        data.photos.totalCount = parseInt(photoMatch[0].replace(/,/g, ''));
      }
    }

    // 写真の種類を推定（カテゴリタブの有無）
    if (photoTab) {
      await photoTab.click();
      await page.waitForTimeout(2000);
      
      const photoCategoryEls = await page.$$('.e13q2c .duB5Yc');
      const photoCategories = [];
      for (const catEl of photoCategoryEls) {
        const catText = await catEl.innerText().catch(() => '');
        photoCategories.push(catText);
      }
      
      data.photos.categories = photoCategories;
      data.photos.hasExterior = photoCategories.some(c => c.includes('外観'));
      data.photos.hasInterior = photoCategories.some(c => c.includes('内部') || c.includes('店内') || c.includes('雰囲気'));
      data.photos.hasFood = photoCategories.some(c => c.includes('メニュー') || c.includes('料理') || c.includes('商品'));
      data.photos.hasStaff = photoCategories.some(c => c.includes('スタッフ') || c.includes('チーム'));
    }

    console.log(`  写真: ${data.photos.totalCount}枚`);

    // ==========================================
    // STEP 4: 投稿情報の取得
    // ==========================================
    console.log('[5/6] 投稿情報を取得中...');
    
    // 概要タブに戻る
    const overviewTab = await page.$('button[aria-label*="概要"], [role="tab"]:has-text("概要")');
    if (overviewTab) {
      await overviewTab.click();
      await page.waitForTimeout(2000);
    }

    // 投稿/最新情報セクションの検出
    const updateEls = await page.$$('.cXHGnc');
    if (updateEls.length > 0) {
      data.posts.recentCount = updateEls.length;
      // 最新投稿の日付を取得
      const latestDate = await updateEls[0].$eval('.rsqaWe, .OSrXXb', e => e.innerText).catch(() => null);
      data.posts.latestPostDate = latestDate;
      
      // 投稿タイプの確認
      for (const updateEl of updateEls) {
        const text = await updateEl.innerText().catch(() => '');
        if (text.includes('特典') || text.includes('クーポン')) data.posts.hasOffer = true;
        if (text.includes('イベント')) data.posts.hasEvent = true;
      }
    }

    console.log(`  投稿: ${data.posts.recentCount}件`);

    // ==========================================
    // STEP 5: 競合情報の取得
    // ==========================================
    if (competitorSearch && data.basic.category && data.basic.address) {
      console.log('[6/6] 競合情報を取得中...');
      
      // カテゴリ + エリアで検索
      const area = extractArea(data.basic.address);
      const searchQuery = `${data.basic.category} ${area}`;
      
      const searchUrl = `https://www.google.com/maps/search/${encodeURIComponent(searchQuery)}`;
      await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(5000);

      // 検索結果のリストアイテムを取得
      const resultEls = await page.$$('.Nv2PK');
      for (const resultEl of resultEls.slice(0, 8)) {
        try {
          const name = await resultEl.$eval('.qBF1Pd', e => e.innerText).catch(() => '');
          if (name === data.basic.name) continue; // 自分自身を除外

          const rating = await resultEl.$eval('.MW4etd', e => parseFloat(e.innerText)).catch(() => 0);
          const reviewText = await resultEl.$eval('.UY7F9', e => e.innerText).catch(() => '');
          const reviewMatch = reviewText.match(/\((\d[\d,]*)\)/);
          const reviewCount = reviewMatch ? parseInt(reviewMatch[1].replace(/,/g, '')) : 0;

          if (name) {
            data.competitors.push({
              name: name.trim(),
              rating,
              reviewCount
            });
          }

          if (data.competitors.length >= 5) break;
        } catch (e) { continue; }
      }

      console.log(`  競合: ${data.competitors.length}社検出`);
    } else {
      console.log('[6/6] 競合情報: スキップ（カテゴリ or 住所が取得できませんでした）');
    }

    if (screenshotDir) {
      await page.screenshot({ path: path.join(screenshotDir, '06_final.png') });
    }

  } catch (error) {
    console.error('データ収集中にエラーが発生:', error.message);
    data.meta.error = error.message;
    if (screenshotDir) {
      await page.screenshot({ path: path.join(screenshotDir, 'error.png') });
    }
  } finally {
    await browser.close();
  }

  return data;
}

// ==========================================
// ヘルパー関数
// ==========================================

async function safeText(page, selector) {
  try {
    const el = await page.$(selector);
    return el ? (await el.innerText()).trim() : null;
  } catch { return null; }
}

async function extractInfoItem(page, label, type) {
  try {
    // data-item-idベースの取得
    const selectors = {
      address: '[data-item-id="address"] .Io6YTe, [data-item-id="address"] .rogA2c',
      phone: '[data-item-id*="phone"] .Io6YTe, [data-item-id*="phone"] .rogA2c'
    };
    if (selectors[type]) {
      const el = await page.$(selectors[type]);
      if (el) return (await el.innerText()).trim();
    }
    // aria-labelベースのフォールバック
    const ariaEl = await page.$(`button[aria-label*="${label}"], a[aria-label*="${label}"]`);
    if (ariaEl) {
      const ariaLabel = await ariaEl.getAttribute('aria-label');
      return ariaLabel?.replace(`${label}: `, '').trim();
    }
    return null;
  } catch { return null; }
}

async function extractHours(page) {
  try {
    // 営業時間ドロップダウンを展開
    const hoursBtn = await page.$('[data-item-id="oh"] button, button[aria-label*="営業時間"]');
    if (hoursBtn) {
      await hoursBtn.click();
      await page.waitForTimeout(1000);
    }
    
    const hourRows = await page.$$('.y0skZc table tr, .OqCZI');
    const hours = {};
    for (const row of hourRows) {
      const text = await row.innerText().catch(() => '');
      const parts = text.split('\t').map(s => s.trim()).filter(Boolean);
      if (parts.length >= 2) {
        hours[parts[0]] = parts.slice(1).join(', ');
      }
    }
    return Object.keys(hours).length > 0 ? hours : null;
  } catch { return null; }
}

async function extractDescription(page) {
  try {
    // 概要タブの説明文
    const descEl = await page.$('.PYvSYb, [data-attrid="description"] span');
    if (descEl) return (await descEl.innerText()).trim();
    
    // 代替: ビジネス概要セクション
    const aboutEl = await page.$('.bfdHYd .Io6YTe');
    if (aboutEl) return (await aboutEl.innerText()).trim();
    
    return null;
  } catch { return null; }
}

async function extractAttributes(page) {
  try {
    const attrs = [];
    const attrEls = await page.$$('.RcCsl li, .E0DTEd .iP2t7d, .CK16pd .RcCsl span');
    for (const el of attrEls) {
      const text = await el.innerText().catch(() => '');
      if (text.trim()) attrs.push(text.trim());
    }
    return attrs;
  } catch { return []; }
}

async function extractServices(page) {
  try {
    const services = [];
    const serviceEls = await page.$$('.LssJHb .hXNfWe span, .nmKJod span');
    for (const el of serviceEls) {
      const text = await el.innerText().catch(() => '');
      if (text.trim()) services.push(text.trim());
    }
    return services;
  } catch { return []; }
}

function extractArea(address) {
  if (!address) return '';
  // 「○○区」「○○市」「○○町」を抽出
  const match = address.match(/([\u4e00-\u9fff]+[区市町村])/);
  return match ? match[1] : address.substring(0, 10);
}

// ==========================================
// メイン実行
// ==========================================

async function main() {
  const url = process.argv[2];
  if (!url) {
    console.error('Usage: node scrape_gbp.js "GoogleマップURL"');
    process.exit(1);
  }

  console.log('=== GBP データ収集開始 ===');
  console.log(`URL: ${url}\n`);

  const data = await scrapeGBP(url, {
    headless: true,
    maxReviews: 20,
    competitorSearch: true
  });

  const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const safeName = (data.basic.name || 'unknown').replace(/[/\\?%*:|"<>]/g, '_').substring(0, 30);
  const outputFile = `gbp_data_${safeName}_${timestamp}.json`;

  fs.writeFileSync(outputFile, JSON.stringify(data, null, 2), 'utf-8');
  console.log(`\n=== 完了: ${outputFile} ===`);

  return data;
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { scrapeGBP };
