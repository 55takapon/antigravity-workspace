// Node 18+ native fetch

async function debug() {
  const response = await fetch('https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv');
  const text = await response.text();
  const rows = text.split('\n').map(line => 
    line.split(',').map(c => c.replace(/\r$/, '').replace(/^"|"$/g, '').trim())
  );
  
  console.log('=== RAW ROWS (first 15) ===');
  rows.slice(0, 15).forEach((r, i) => console.log(i + ':', JSON.stringify(r)));

  // シミュレート: extractDataForMonth と同じロジックで4月を探す
  const targetPrefix = '2026-04';
  const prevPrefix   = '2026-03';
  let currentRow = null, prevRow = null;
  const trendViews = [], trendReviews = [];

  for (let i = 2; i < rows.length; i++) {
    const row = rows[i];
    if (!row[0]) continue;
    if (row[0] === targetPrefix) currentRow = row;
    if (row[0] === prevPrefix)   prevRow = row;

    const mMatch = row[0].match(/-(\d{2})$/);
    if (mMatch) {
      const mNum = parseInt(mMatch[1]);
      const viewVal = parseInt(row[1]);
      const reviewVal = parseInt(row[5]);
      if (!isNaN(viewVal))   trendViews.push({ month: mNum + '月', value: viewVal });
      if (!isNaN(reviewVal)) trendReviews.push({ month: mNum + '月', value: reviewVal });
    }
  }
  console.log('\n=== 4月行 ===', JSON.stringify(currentRow));
  console.log('=== 3月行 ===', JSON.stringify(prevRow));
  console.log('=== trendViews ===', JSON.stringify(trendViews));
  console.log('=== trendReviews ===', JSON.stringify(trendReviews));
}

debug().catch(console.error);
