const fs = require('fs');
const path = require('path');

/**
 * 競合ベンチマークデータを前月HTMLから取得する（スクレイピング廃止）
 * 
 * 構造:
 * 1. 前月HTMLが存在すれば、そこからベンチマークをコピーする
 * 2. 存在しなければ、client_registry.js の設定値（fallback）を使用する
 */
async function scrapeCompetitors(competitors, outputDir, slug, month) {
  if (!competitors || competitors.length === 0) return [];

  let prevData = null;
  const prevMonth = month - 1;
  
  if (prevMonth >= 1 && outputDir && slug) {
    const prevHtml = path.join(outputDir, `${slug}_monthly_2026${prevMonth.toString().padStart(2, '0')}.html`);
    if (fs.existsSync(prevHtml)) {
      const content = fs.readFileSync(prevHtml, 'utf-8');
      const tbodyMatch = content.match(/<div class="section-title">📊 ベンチマーク参考<\/div>\s*<table>[\s\S]*?<tbody>([\s\S]*?)<\/tbody>/);
      if (tbodyMatch) {
        const rows = tbodyMatch[1].match(/<tr[^>]*>[\s\S]*?<\/tr>/g) || [];
        const extracted = [];
        for (const row of rows) {
          if (row.includes('background')) continue; // 自社行はスキップ
          
          const cells = row.match(/<td[^>]*>([\s\S]*?)<\/td>/g);
          if (!cells || cells.length < 3) continue;
          
          const name = cells[0].replace(/<[^>]+>/g, '').trim();
          const reviewCount = parseInt(cells[1].replace(/[^0-9]/g, ''));
          const rating = parseFloat(cells[2].replace(/[^0-9.]/g, ''));

          if (!isNaN(reviewCount) && !isNaN(rating)) {
            extracted.push({ name, reviewCount, rating, isSelf: false });
          }
        }
        if (extracted.length > 0) {
          prevData = extracted;
          console.log(`   📂 前月レポートからベンチマーク ${extracted.length}件 を引き継ぎました`);
        }
      }
    }
  }

  // 抽出できた場合は前月データと registry の定義をマージ
  const results = [];
  for (const comp of competitors) {
    let reviewCount = comp.fallbackReviewCount;
    let rating = comp.fallbackRating;

    if (prevData) {
      // 名前が部分一致するものを前月データから探す
      const baseName = comp.name.split('（')[0].trim();
      const match = prevData.find(p => p.name.includes(baseName) || baseName.includes(p.name));
      if (match) {
        reviewCount = match.reviewCount;
        rating = match.rating;
      }
    }

    results.push({
      name: comp.name,
      isSelf: comp.isSelf,
      reviewCount: reviewCount,
      rating: rating
    });
  }

  return results;
}

module.exports = { scrapeCompetitors };
