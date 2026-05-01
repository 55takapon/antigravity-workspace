const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * 前月のHTMLレポートからベンチマークデータを抽出する
 * → スクレイピング失敗時のフォールバックとして使う
 */
function extractBenchmarkFromPrevReport(outputDir, slug, month) {
  // まず当月HTMLを試す（再生成時）
  const candidates = [
    path.join(outputDir, `${slug}_monthly_2026${month.toString().padStart(2, '0')}.html`),
  ];
  // 前月HTML
  if (month > 1) {
    candidates.push(
      path.join(outputDir, `${slug}_monthly_2026${(month - 1).toString().padStart(2, '0')}.html`)
    );
  }

  for (const htmlPath of candidates) {
    if (!fs.existsSync(htmlPath)) continue;
    const content = fs.readFileSync(htmlPath, 'utf-8');

    // ベンチマークテーブルからデータを抽出
    const tbodyMatch = content.match(/<div class="section-title">📊 ベンチマーク参考<\/div>\s*<table>[\s\S]*?<tbody>([\s\S]*?)<\/tbody>/);
    if (!tbodyMatch) continue;

    const rows = tbodyMatch[1].match(/<tr[^>]*>[\s\S]*?<\/tr>/g) || [];
    const competitors = [];
    for (const row of rows) {
      const cells = row.match(/<td[^>]*>([\s\S]*?)<\/td>/g);
      if (!cells || cells.length < 3) continue;
      const name = cells[0].replace(/<[^>]+>/g, '').trim();
      const reviewText = cells[1].replace(/<[^>]+>/g, '').trim();
      const ratingText = cells[2].replace(/<[^>]+>/g, '').trim();
      const reviewCount = parseInt(reviewText.replace(/[^0-9]/g, ''));
      const rating = parseFloat(ratingText.replace(/[^0-9.]/g, ''));

      // 自社行はスキップ（背景色付きの行）
      if (row.includes('background')) continue;

      if (!isNaN(reviewCount) && !isNaN(rating)) {
        competitors.push({ name, reviewCount, rating, isSelf: false });
      }
    }
    if (competitors.length > 0) {
      console.log(`   📂 前月レポートからベンチマーク${competitors.length}件を取得: ${path.basename(htmlPath)}`);
      return competitors;
    }
  }
  return null;
}

async function scrapeCompetitors(competitors, outputDir, slug, month) {
  // competitors が空なら前月レポートからの取得も試みない
  if (!competitors || competitors.length === 0) return [];

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'ja-JP' });
  const page = await context.newPage();
  
  const results = [];
  let scrapeFailCount = 0;

  for (const comp of competitors) {
    try {
      await page.goto(`https://www.google.com/search?q=${encodeURIComponent(comp.name)}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2000);
      
      const ratingEl = await page.locator('span.Aq14fc').first();
      const reviewEl = await page.locator('a.hqzQac span').first();
      
      let rating = null;
      let reviewCount = null;
      
      if (await ratingEl.count() > 0) {
        rating = parseFloat(await ratingEl.innerText());
      }
      if (await reviewEl.count() > 0) {
        const reviewText = await reviewEl.innerText();
        const match = reviewText.replace(/,/g, '').match(/\d+/);
        if (match) reviewCount = parseInt(match[0]);
      }
      
      if (rating === null && reviewCount === null) scrapeFailCount++;

      results.push({
        name: comp.name,
        isSelf: comp.isSelf,
        reviewCount: reviewCount !== null ? reviewCount : comp.fallbackReviewCount,
        rating: rating !== null ? rating : comp.fallbackRating
      });
      console.log(`   Scraped ${comp.name}: ${rating ?? 'N/A'} ★, ${reviewCount ?? 'N/A'} reviews${(rating === null || reviewCount === null) ? ' (fallback使用)' : ''}`);
    } catch (e) {
      console.error(`   Error scraping ${comp.name}:`, e.message);
      scrapeFailCount++;
      results.push({
        name: comp.name,
        isSelf: comp.isSelf,
        reviewCount: comp.fallbackReviewCount,
        rating: comp.fallbackRating
      });
    }
  }
  
  await browser.close();

  // ── 全件スクレイピング失敗 or データ欠損が多い場合 → 前月レポートにフォールバック ──
  const hasUndefined = results.some(r => r.reviewCount === undefined || r.rating === undefined);
  if (hasUndefined && outputDir && slug && month) {
    console.log(`   ⚠️ ベンチマークにundefined値あり — 前月レポートからフォールバックを試みます`);
    const prevData = extractBenchmarkFromPrevReport(outputDir, slug, month);
    if (prevData) {
      // 前月データで undefined を埋める
      for (const r of results) {
        if (r.isSelf) continue;
        if (r.reviewCount === undefined || r.rating === undefined) {
          const prev = prevData.find(p => p.name.includes(r.name.split('（')[0]) || r.name.includes(p.name.split('（')[0]));
          if (prev) {
            if (r.reviewCount === undefined) r.reviewCount = prev.reviewCount;
            if (r.rating === undefined) r.rating = prev.rating;
            console.log(`   📂 ${r.name}: 前月値を使用 (${prev.reviewCount}件, ★${prev.rating})`);
          }
        }
      }
    }
  }

  // 最終チェック: まだ undefined が残っていたら警告
  const stillUndefined = results.filter(r => !r.isSelf && (r.reviewCount === undefined || r.rating === undefined));
  if (stillUndefined.length > 0) {
    console.log(`   🔴 警告: 以下の競合にデータがありません（レポートで空欄になります）:`);
    stillUndefined.forEach(r => console.log(`      - ${r.name}: reviews=${r.reviewCount}, rating=${r.rating}`));
  }

  return results;
}

if (require.main === module) {
  scrapeCompetitors([
    { name: 'MARKESMILE 加古川', fallbackReviewCount: 8, fallbackRating: 4.9 },
    { name: 'うみがわ 加古川', fallbackReviewCount: 3, fallbackRating: 5.0 },
    { name: 'ハシモトデザイン 加古川', fallbackReviewCount: 6, fallbackRating: 4.8 }
  ]).then(console.log);
}

module.exports = { scrapeCompetitors, extractBenchmarkFromPrevReport };
