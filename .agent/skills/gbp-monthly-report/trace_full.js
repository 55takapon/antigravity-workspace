// Add logging to generate_report_from_sheet.js temporarily
// Patch renderHTML to log competitors
const origRender = require('./render_html').renderHTML;
const { renderHTML: patched } = require('./render_html');

// Override
const path = require('path');
const fs   = require('fs');
const { CLIENTS, SHEET_URL } = require('./client_registry');
const { calculateMainKPIs, generateRecommendations } = require('./calculate_kpis');
const { scrapeCompetitors } = require('./scrape_competitors');

// Inline the extractDataForMonth from generate_report_from_sheet
async function run() {
  const res = await fetch('https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv');
  const text = await res.text();
  const rows = text.split('\n').map(l => l.split(',').map(c => c.replace(/\r$/,'').replace(/^"|"$/g,'').trim()));

  // Same logic as generate_report_from_sheet.js extractDataForMonth
  const clientName = '英和塾', campus = '南校';
  let blockStart = -1;
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    if (campus) {
      if (r[0].includes(clientName) && r[1] && r[1].includes(campus)) { blockStart = i; break; }
    }
  }
  let blockEnd = rows.length;
  for (let i = blockStart + 1; i < rows.length; i++) {
    const f = rows[i][0];
    if (!f) { blockEnd = i; break; }
    if (f !== '月' && !/^\d{4}-\d{2}$/.test(f)) { blockEnd = i; break; }
  }
  const block = rows.slice(blockStart, blockEnd);
  const data = {
    header: { clientName: '英和塾（南校）', industry: '学習塾' },
    month: 4,
    performance: { '閲覧数（合計）': 243 },
    prevPerformance: {},
    reviews: { '口コミ総数（累計）': 1, '平均評価（★）': 5 },
    prevReviews: {},
    posts: { '当月投稿数': 2 },
    targetReviewCount: 30,
    skipRules: ['calls'],
    trendViews: [{ month: '1月', value: 190 }, { month: '2月', value: 280 }, { month: '3月', value: 310 }, { month: '4月', value: 243 }],
    trendReviews: [],
    queries: [],
    actionLog: { actions: '', results: '' },
  };

  const client = CLIENTS.find(c => c.slug === 'eiwa-juku-south');
  const scraped = await scrapeCompetitors(client.competitors);
  scraped.push({ name: data.header.clientName, isSelf: true, reviewCount: data.reviews['口コミ総数（累計）'], rating: data.reviews['平均評価（★）'] });
  data.competitors = scraped;

  console.log('data.competitors:', JSON.stringify(data.competitors));

  const mainKPIs = calculateMainKPIs(data);
  const recs = generateRecommendations(data, data.skipRules, data.targetReviewCount);

  const reportData = { ...data, mainKPIs, recommendations: recs, customMessage: '' };
  console.log('reportData.competitors:', JSON.stringify(reportData.competitors));
  console.log('keys:', Object.keys(reportData));
}

run().catch(console.error);
