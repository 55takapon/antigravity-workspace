// Trace exact reportData.competitors value before renderHTML
const path = require('path');
const fs   = require('fs');
const { CLIENTS } = require('./client_registry');
const { calculateMainKPIs, generateRecommendations } = require('./calculate_kpis');
const { renderHTML } = require('./render_html');
const { scrapeCompetitors } = require('./scrape_competitors');

async function trace() {
  const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv';
  const res = await fetch(SHEET_URL);
  const text = await res.text();
  const rows = text.split('\n').map(l => l.split(',').map(c => c.replace(/\r$/,'').replace(/^"|"$/g,'').trim()));

  // Simulate extractDataForMonth for eiwa-south
  const clientInfo = { name: '英和塾', campus: '南校', displayName: '英和塾（南校）' };
  
  // Block detection
  let blockStart = -1;
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    if (!r[0]) continue;
    if (r[0].includes(clientInfo.name) && r[1] && r[1].includes(clientInfo.campus)) {
      blockStart = i; break;
    }
  }
  let blockEnd = rows.length;
  for (let i = blockStart + 1; i < rows.length; i++) {
    const f = rows[i][0];
    if (!f) { blockEnd = i; break; }
    if (f !== '月' && !/^\d{4}-\d{2}$/.test(f)) { blockEnd = i; break; }
  }
  console.log('Block:', blockStart, '-', blockEnd, '  clientNameRow:', JSON.stringify(rows[blockStart]));
  
  // Build data object manually
  const client = CLIENTS.find(c => c.slug === 'eiwa-juku-south');
  const competitors = client.competitors;
  
  const scraped = await scrapeCompetitors(competitors);
  scraped.push({ name: '英和塾（南校）', isSelf: true, reviewCount: 1, rating: 5 });
  
  const data = { header: { clientName: '英和塾（南校）' }, competitors: [] };
  data.competitors = scraped;
  
  console.log('\ndata.competitors:', JSON.stringify(data.competitors, null, 2));
  
  // Check spread behavior
  const reportData = {
    ...data,
    mainKPIs: {},
    recommendations: [],
    customMessage: '',
  };
  console.log('\nreportData.competitors:', JSON.stringify(reportData.competitors));
}

trace().catch(console.error);
