/**
 * scrape_reviews.js
 * Playwrightで Googleマップの口コミを全件抽出するスクリプト
 *
 * ※ scrape_auto.js（動作確認済み手法）を完全移植・統合したバージョン
 *
 * Usage:
 *   node scrape_reviews.js --url "GoogleマップURL" --name "client_name"
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// === JST日付生成 ===
function getJSTDateStr() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10).replace(/-/g, '');
}

// === メイン処理 ===
async function scrapeReviews(url, clientName) {
  const OUT_DIR = path.join(__dirname, '..');

  console.log(`\n🔍 口コミ抽出を開始します...`);
  console.log(`   URL: ${url}`);
  console.log(`   クライアント名: ${clientName}`);
  console.log(`   開始時刻: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}\n`);

  // ── ブラウザ起動（scrape_auto.js と同方式） ──
  const browser = await chromium.launch({
    headless: false,
    args: [
      '--lang=ja-JP',
      '--window-size=1280,900',
      '--disable-blink-features=AutomationControlled',
      '--no-first-run',
      '--no-default-browser-check',
    ],
    slowMo: 50,
  });

  const context = await browser.newContext({
    locale: 'ja-JP',
    viewport: { width: 1280, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
  });

  const page = await context.newPage();

  try {
    // STEP 1: ページを開く
    console.log('📖 Googleマップを開いています...');
    await page.goto(url, { waitUntil: 'load', timeout: 60000 });
    await page.waitForTimeout(5000);

    const resolvedUrl = page.url();
    console.log(`   リダイレクト後URL: ${resolvedUrl}`);

    // STEP 2: URLハックで口コミタブを強制表示（scrape_auto.js の核心手法）
    // タブクリックではなく、GoogleマップのURLパラメータを書き換えて直接口コミタブへ遷移
    let reviewUrl = resolvedUrl;
    if (!resolvedUrl.includes('!9m1!1b1')) {
      const baseUrl = resolvedUrl.split('?')[0];
      const queryStr = resolvedUrl.includes('?') ? '?' + resolvedUrl.split('?')[1] : '';
      let dataStr = baseUrl;

      // !4mN!3mM のカウンタを +2（口コミタブのフラグ分）
      dataStr = dataStr.replace(/(!4m)(\d+)(!3m)(\d+)/, (_, a, n1, b, n2) =>
        `${a}${parseInt(n1) + 2}${b}${parseInt(n2) + 2}`
      );
      // !16s の直前に !9m1!1b1 を挿入（口コミタブ表示フラグ）
      dataStr = dataStr.replace('!16s', '!9m1!1b1!16s');

      reviewUrl = dataStr + queryStr;
      console.log(`   口コミタブURL: ${reviewUrl}`);
      await page.goto(reviewUrl, { waitUntil: 'load', timeout: 60000 });
      await page.waitForTimeout(5000);
    } else {
      console.log('   既に口コミタブURLです');
    }

    // デバッグ用スクリーンショット
    const screenshotPath = path.join(OUT_DIR, `screenshot_${clientName}.png`);
    await page.screenshot({ path: screenshotPath });
    console.log(`   スクリーンショット: ${screenshotPath}`);

    // STEP 3: 初期口コミ数を確認（IDベースでカウント）
    const initCount = await page.evaluate(() => {
      const ids = new Set();
      document.querySelectorAll('[data-review-id]').forEach(el => ids.add(el.getAttribute('data-review-id')));
      return ids.size;
    });
    console.log(`\n   初期口コミ数: ${initCount}件`);

    // STEP 4: 全件スクロール（scrape_auto.js と同方式）
    console.log('📜 全件スクロール中...');
    let prevCount = 0;
    let sameStreak = 0;
    let scrolledCount = 0; // スクロール完了後の実 DOM上の口コミ数（公式件数取得失敗時のフォールバック）

    for (let i = 0; i < 100; i++) {
      // 「もっと見る」を展開しながらスクロール（page.evaluate 内で一括処理）
      await page.evaluate(() => {
        // 口コミ本文の「もっと見る」と返信の「もっと見る」を両方展開
        document.querySelectorAll([
          '.w8nwRe',                                   // 口コミ本文の展開ボタン
          'button[jsaction*="pane.review.expandReview"]', // 口コミ展開（旧）
          '.w8nwRe.kyuRq',                             // 返信の展開ボタン（既知クラス）
          'button[aria-label*="もっと見る"]',           // aria-labelベースのフォールバック
          '.CDe7pd .w8nwRe',                           // 返信コンテナ内のもっと見る
        ].join(',')).forEach(btn => {
          try { btn.click(); } catch (e) {}
        });

        // スクロールコンテナを優先順位付きで試行（scrape_auto.js の手法）
        const panels = [
          '.m6QErb.DxyBCb',
          '.m6QErb[aria-label]',
          '.ecceSd',
          'div[role="feed"]',
          'div[role="main"] .m6QErb',
        ];
        for (const sel of panels) {
          const el = document.querySelector(sel);
          if (el && el.scrollHeight > el.clientHeight) {
            el.scrollTop += 1500;
            return;
          }
        }
        // フォールバック: ページ全体スクロール
        window.scrollBy(0, 1500);
      });

      await page.waitForTimeout(700);

      // IDベースで重複なしにカウント
      const count = await page.evaluate(() => {
        const ids = new Set();
        document.querySelectorAll('[data-review-id]').forEach(el => ids.add(el.getAttribute('data-review-id')));
        return ids.size;
      });

      if (i % 10 === 0) console.log(`   スクロール${i + 1}回: ${count}件`);

      if (count === prevCount) {
        sameStreak++;
        if (sameStreak >= 10) {
          console.log(`   読み込み完了: ${count}件`);
          scrolledCount = count; // スクロール完了時の実カウントを保持
          break;
        }
      } else {
        sameStreak = 0;
      }
      prevCount = count;
      scrolledCount = count; // 最新カウントを常に更新
    }

    // STEP 5: 全ての「もっと見る」を確実に展開（口コミ本文 + オーナー返信の両方）
    // スクロール中のクリックでは画面外の要素に届かないため、スクロール完了後に専用パスで処理
    console.log('📖 全テキストを展開中（口コミ＋返信）...');
    let expandedCount = 0;
    for (let attempt = 0; attempt < 5; attempt++) {
      const clicked = await page.evaluate(() => {
        let count = 0;
        const btns = document.querySelectorAll([
          '.w8nwRe',
          'button[jsaction*="pane.review.expandReview"]',
          'button[aria-label*="もっと見る"]',
          '.CDe7pd .w8nwRe',
          '.CDe7pd button',
        ].join(','));
        btns.forEach(btn => {
          try {
            btn.scrollIntoView({ block: 'center' });
            btn.click();
            count++;
          } catch (e) {}
        });
        return count;
      });
      expandedCount += clicked;
      if (clicked === 0) break;
      await page.waitForTimeout(800);
    }
    console.log(`   展開処理完了（計${expandedCount}回クリック）`);

    // STEP 6: データ抽出（全てpage.evaluate内でブラウザ側処理 ← scrape_auto.js の核心）
    console.log('\n📊 データ抽出中...');
    const data = await page.evaluate(() => {
      // ── 店舗メタデータ ──
      const nameEl = document.querySelector('h1.DUwDvf') || document.querySelector('.fontHeadlineLarge');
      const storeName = nameEl
        ? nameEl.textContent.trim()
        : (document.title.split(' - ')[0].trim() || '不明');

      const ratingEl = document.querySelector('.fontDisplayLarge');
      const storeRating = ratingEl ? ratingEl.textContent.trim() : '';

      // 公式総件数の取得（複数セレクタで試行）
      const countSelectors = [
        'div.F7nice span[aria-label]',
        'button[aria-label*="件のクチコミ"]',
        '[aria-label*="件のクチコミ"]',
        'span[aria-label*="星"]',
      ];
      let totalCount = 0;
      for (const sel of countSelectors) {
        const el = document.querySelector(sel);
        if (!el) continue;
        const label = el.getAttribute('aria-label') || el.textContent;
        const m = label.match(/(\d[\d,]*)\s*件/);
        if (m) { totalCount = parseInt(m[1].replace(/,/g, ''), 10); break; }
      }
      // フォールバック: ページ内のspan全体から「47件のクチコミ」パターンを検索
      if (!totalCount) {
        const text = document.body.innerText;
        const m = text.match(/(\d+)\s*件のクチコミ/);
        if (m) totalCount = parseInt(m[1], 10);
      }

      const catBtn = document.querySelector('button.DkEaL');
      const businessCategory = catBtn ? catBtn.textContent.trim() : '不明';

      // ── 口コミ要素：トップレベルのみ取得（closest による正確な判定）──
      const allEls = document.querySelectorAll('[data-review-id]');
      const seenIds = new Set();
      const topEls = [];
      allEls.forEach(el => {
        const id = el.getAttribute('data-review-id');
        if (!id || seenIds.has(id)) return;
        // 親要素にも data-review-id があればネストした子要素 → スキップ
        if (el.parentElement && el.parentElement.closest('[data-review-id]')) return;
        seenIds.add(id);
        topEls.push(el);
      });

      // ── オーナー返信の既知フレーズ（テキストベースの補完フィルタ）──
      const OWNER_PHRASES = [
        'ご来店ありがとうございました',
        'またのご来店をお待ちしてます',
        'お越しいただきありがとうございました',
      ];

      // ── 構造化フォームの切り捨てマーカー ──
      const CUT_MARKERS = [
        '1 人あたりの料金', '1人あたりの料金',
        '騒音レベル', 'グループの人数', '待ち時間',
      ];

      const reviews = [];
      for (const el of topEls) {
        // .wiI7pd / .MyEned を複数取得し、オーナー返信コンテナ外のものを採用
        const allTextEls = Array.from(el.querySelectorAll('.wiI7pd, .MyEned'));
        let text = '';

        for (const t of allTextEls) {
          // 祖先をたどってオーナー返信セクションか判定
          let ancestor = t.parentElement;
          let isOwnerSection = false;
          while (ancestor && ancestor !== el) {
            const label = ancestor.getAttribute('aria-label') || '';
            if (label.includes('オーナー') || label.includes('owner')) {
              isOwnerSection = true; break;
            }
            if (ancestor.className && ancestor.className.includes('CDe7pd')) {
              isOwnerSection = true; break;
            }
            ancestor = ancestor.parentElement;
          }
          if (isOwnerSection) continue;

          const raw = t.innerText.trim();

          // 構造化フォームセクションを切り捨て
          let cutIdx = raw.length;
          for (const marker of CUT_MARKERS) {
            const idx = raw.indexOf(marker);
            if (idx !== -1 && idx < cutIdx) cutIdx = idx;
          }
          const beforeStructured = raw.slice(0, cutIdx).trim();

          // サブ評価行（「食事: 1」等）を除去
          const cleaned = beforeStructured.split('\n')
            .filter(line => {
              const l = line.trim();
              if (!l) return false;
              if (/^(食事|サービス|雰囲気)[:：]\s*\d*$/.test(l)) return false;
              if (/^(注文の種類|食事の種類|イートイン|ディナー|ランチ|テイクアウト|おすすめの料理|駐車場の種類|無料駐車場|有料駐車場)/.test(l)) return false;
              return true;
            })
            .join('\n')
            .trim();

          text = cleaned;
          if (text) break;
        }

        // テキストなし口コミ（星のみ）は取得対象外
        if (!text) continue;

        // オーナー返信テキストを除外（DOMフィルタの補完）
        if (OWNER_PHRASES.some(p => text.includes(p))) continue;

        // 各フィールドの取得
        const authorEl = el.querySelector('.d4r55') || el.querySelector('.NMjTrf');
        const ratingEl2 = el.querySelector('[aria-label*="星"]') ||
                          el.querySelector('[aria-label*="star"]') ||
                          el.querySelector('.kvMYJc');
        let rating = 0;
        if (ratingEl2) {
          const m = (ratingEl2.getAttribute('aria-label') || '').match(/(\d)/);
          rating = m ? parseInt(m[1]) : 0;
        }

        const dateEl = el.querySelector('.rsqaWe') || el.querySelector('.xRkPPb');
        const localGuideEl = el.querySelector('.RfnDt');

        // オーナー返信テキストの取得
        const replyContainer = el.querySelector('.CDe7pd');
        let ownerReply = null;
        if (replyContainer) {
          const replyTextEl = replyContainer.querySelector('.wiI7pd, .MyEned');
          if (replyTextEl) ownerReply = replyTextEl.innerText.trim() || null;
        }

        reviews.push({
          id: el.getAttribute('data-review-id'),
          author: authorEl ? authorEl.textContent.trim() : '匿名',
          rating,
          dateText: dateEl ? dateEl.textContent.trim() : '',
          text,
          localGuide: localGuideEl ? localGuideEl.textContent.trim() : '',
          ownerReply,
          scrapedAt: new Date().toISOString(),
        });
      }

      return { storeName, storeRating, totalCount, businessCategory, reviews };
    });

    console.log(`   店舗名: ${data.storeName}`);
    console.log(`   評価: ${data.storeRating} / 口コミ総数: ${data.totalCount}`);
    console.log(`   カテゴリ: ${data.businessCategory}`);
    console.log(`   コメントあり: ${data.reviews.length}件`);

    await browser.close();

    if (data.reviews.length === 0) {
      console.log('\n⚠️ 口コミが取得できませんでした。スクリーンショットを確認してください。');
      return null;
    }

    // STEP 6: JSON出力
    const dateStr = getJSTDateStr();
    const safeClientId = clientName.toLowerCase().replace(/[^\w]/g, '_').replace(/_+/g, '_');

    // officialTotalCount: DOM取得値がテキスト件数以下なら不正値なのでscrolledCountを採用
    const rawTotal = data.totalCount;
    const officialTotalCount = (rawTotal && rawTotal > data.reviews.length) ? rawTotal : scrolledCount;

    const jsonData = {
      clientId: safeClientId,
      businessName: data.storeName,
      businessCategory: data.businessCategory,
      storeRating: data.storeRating,
      officialTotalCount,  // Googleマップ公式件数（星のみ含む全評価: 47件など）
      textReviewCount: data.reviews.length, // テキストコメントあり件数（31件など）
      scrapedUrl: url,
      scrapedAt: new Date().toISOString(),
      reviews: data.reviews,
    };

    const outputName = `review_data_${safeClientId}_${dateStr}.json`;
    const outputPath = path.join(OUT_DIR, outputName);
    fs.writeFileSync(outputPath, JSON.stringify(jsonData, null, 2), 'utf-8');

    console.log(`\n✅ 完了！`);
    console.log(`   出力: ${outputPath}`);
    console.log(`   終了時刻: ${new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })}\n`);

    return jsonData;

  } catch (err) {
    await browser.close();
    throw err;
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
