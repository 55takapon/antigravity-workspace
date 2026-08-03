const fs = require('fs');
const path = require('path');

const REPORT_DIR = path.join(require('os').homedir(), '.gemini', 'antigravity', '.agent', 'clients', '00monthly-reports');
const REGISTRY_PATH = path.join(__dirname, 'client_registry.js');

function extractCompetitorsFromHtml(htmlPath) {
  if (!fs.existsSync(htmlPath)) return [];
  const content = fs.readFileSync(htmlPath, 'utf-8');
  const benchmarkMatch = content.match(/<div class="section-title">📊 ベンチマーク参考<\/div>\s*<table>[\s\S]*?<tbody>([\s\S]*?)<\/tbody>/);
  if (!benchmarkMatch) return [];
  
  const tbody = benchmarkMatch[1];
  const rows = tbody.match(/<tr[^>]*>[\s\S]*?<\/tr>/g) || [];
  const competitors = [];
  
  for (const row of rows) {
    if (row.includes('★')) continue; // Skip self
    const cells = row.match(/<td>([\s\S]*?)<\/td>/g);
    if (cells && cells.length >= 3) {
      const name = cells[0].replace(/<\/?td>/g, '').trim();
      const reviewText = cells[1].replace(/<\/?td>/g, '').replace('件', '').trim();
      const ratingText = cells[2].replace(/<\/?td>/g, '').trim();
      
      competitors.push({
        name: name,
        isSelf: false,
        fallbackReviewCount: parseInt(reviewText, 10) || 0,
        fallbackRating: parseFloat(ratingText) || 0
      });
    }
  }
  return competitors;
}

function updateRegistry() {
  const { CLIENTS } = require('./client_registry');
  let updatedCount = 0;

  for (const client of CLIENTS) {
    if (client.competitors && client.competitors.length > 0) continue; // Already has competitors
    
    // Check old files (both new slugs and old slugs just in case)
    let htmlPath = path.join(REPORT_DIR, `${client.slug}_monthly_202603.html`);
    if (!fs.existsSync(htmlPath)) {
       // if we can't find it, skip
       continue;
    }
    
    const comps = extractCompetitorsFromHtml(htmlPath);
    if (comps.length > 0) {
      client.competitors = comps;
      updatedCount++;
      console.log(`✅ Extracted ${comps.length} competitors for ${client.slug}`);
    } else {
      console.log(`⚠️ No competitors found in 3月 report for ${client.slug}`);
    }
  }

  if (updatedCount > 0) {
    const registryContent = fs.readFileSync(REGISTRY_PATH, 'utf-8');
    // We rewrite the CLIENTS array in the registry
    const newClientsStr = JSON.stringify(CLIENTS, null, 2).replace(/"([^"]+)":/g, '"$1":');
    
    const newRegistry = registryContent.replace(/const CLIENTS = \[[\s\S]*?\];/, `const CLIENTS = ${newClientsStr};`);
    fs.writeFileSync(REGISTRY_PATH, newRegistry, 'utf-8');
    console.log(`Updated client_registry.js with competitors for ${updatedCount} clients.`);
  } else {
    console.log('No updates needed for client_registry.js');
  }
}

updateRegistry();
