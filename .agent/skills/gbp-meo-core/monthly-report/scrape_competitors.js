const { chromium } = require('playwright');

async function scrapeCompetitors(competitors) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: 'ja-JP' });
  const page = await context.newPage();
  
  const results = [];
  for (const comp of competitors) {
    try {
      await page.goto(`https://www.google.com/search?q=${encodeURIComponent(comp.name)}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2000); // Wait for the Knowledge Panel
      
      // Look for elements containing the rating
      const ratingEl = await page.locator('span.Aq14fc').first();
      // Look for the review count
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
      
      results.push({
        name: comp.name,
        isSelf: comp.isSelf,
        reviewCount: reviewCount !== null ? reviewCount : comp.fallbackReviewCount,
        rating: rating !== null ? rating : comp.fallbackRating
      });
      console.log(`Scraped ${comp.name}: ${rating} ★, ${reviewCount} reviews`);
    } catch (e) {
      console.error(`Error scraping ${comp.name}:`, e.message);
      results.push({
        name: comp.name,
        isSelf: comp.isSelf,
        reviewCount: comp.fallbackReviewCount,
        rating: comp.fallbackRating
      });
    }
  }
  
  await browser.close();
  return results;
}

if (require.main === module) {
  scrapeCompetitors([
    { name: 'MARKESMILE 加古川', fallbackReviewCount: 8, fallbackRating: 4.9 },
    { name: 'うみがわ 加古川', fallbackReviewCount: 3, fallbackRating: 5.0 },
    { name: 'ハシモトデザイン 加古川', fallbackReviewCount: 6, fallbackRating: 4.8 }
  ]).then(console.log);
}

module.exports = { scrapeCompetitors };
