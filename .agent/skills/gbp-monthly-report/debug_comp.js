// Debug: trace what happens to competitors array
const { CLIENTS } = require('./client_registry');
const { scrapeCompetitors } = require('./scrape_competitors');

async function debug() {
  const client = CLIENTS.find(c => c.slug === 'eiwa-juku-south');
  console.log('Client competitors from registry:', JSON.stringify(client.competitors, null, 2));
  
  console.log('\nCalling scrapeCompetitors...');
  const result = await scrapeCompetitors(client.competitors);
  console.log('\nResult:', JSON.stringify(result, null, 2));
}

debug().catch(console.error);
