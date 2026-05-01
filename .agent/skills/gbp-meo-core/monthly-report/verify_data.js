// verify data extraction
async function check() {
  const response = await fetch('https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv');
  const text = await response.text();
  const rows = text.split('\n').map(l => l.split(',').map(c => c.replace(/\r$/, '').replace(/^"|"$/g, '').trim()));
  
  const clientName = 'ジェットプロデュース';
  let blockStart = rows.findIndex(r => r[0] && r[0].includes(clientName));
  let blockEnd = rows.length;
  for (let i = blockStart + 1; i < rows.length; i++) {
    const f = rows[i][0];
    if (!f) { blockEnd = i; break; }
    if (f !== '月' && !/^\d{4}-\d{2}$/.test(f)) { blockEnd = i; break; }
  }
  const block = rows.slice(blockStart, blockEnd);

  const target = block.find(r => r[0] === '2026-04');
  const prev   = block.find(r => r[0] === '2026-03');
  console.log('=== 4月行 ===', JSON.stringify(target));
  console.log('=== 3月行 ===', JSON.stringify(prev));
  const trend = block.slice(2).filter(r => r[0] && /^\d{4}-\d{2}$/.test(r[0]) && r[1] !== '');
  console.log('=== trendViews (データあり月のみ) ===');
  trend.forEach(r => console.log('  ', r[0], '閲覧:', r[1], '口コミ:', r[5], '評価:', r[7], '投稿:', r[8]));
}
check().catch(console.error);
