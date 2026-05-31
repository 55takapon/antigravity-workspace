const fs = require('fs');

const csvPath = 'C:\\Users\\hangy\\Downloads\\GBP_2026_月次_データ全クライアント - シート1 (1).csv';
const jsonPath = 'C:\\Users\\hangy\\.gemini\\antigravity\\scratch\\gbp-ops-dashboard\\gbp-ops-data.json';

const clientMap = {
  'ジェットプロデュース': 'jetproduce',
  '医療法人社団　かまだ歯科医院': 'kamada-dental',
  '幸健美歯科クリニック': 'sapporo-occlusion',
  '榊原税理士事務所': 'sakakibara-tax',
  'ペットシッターにゃんぽん': 'pet-sitter',
  'ミート歯科': 'meet-dental',
  'アイアムアイ': 'iami-kakogawa',
  '英和塾,南校': 'eiwa-juku-minami',
  '英和塾,北校': 'eiwa-juku-kita',
  '芝本司法書士事務所': 'shibamoto-legal',
  'みち': 'michi'
};

const csvContent = fs.readFileSync(csvPath, 'utf8');
const lines = csvContent.split('\n').map(l => l.trim()).filter(l => l);

let appData = {};
try {
  appData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
} catch (e) {
  console.log('No existing JSON found or parse error. Creating new one.');
}

let currentClientName = null;
let currentClientId = null;

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  if (line.includes(',,')) {
    // Possibly a client header line
    // e.g. ジェットプロデュース,,"""C:\..."""
    // Or 英和塾,南校,"""C:\..."""
    let potentialName = line.split(',"')[0];
    if (potentialName.endsWith(',')) potentialName = potentialName.slice(0, -1);
    
    // Check if it's in clientMap
    let matched = null;
    for (const key of Object.keys(clientMap)) {
      if (line.startsWith(key + ',') || line === key) {
        matched = key;
        break;
      }
    }
    
    if (matched) {
      currentClientName = matched;
      currentClientId = clientMap[matched];
    }
  } else if (line.startsWith('2026-')) {
    if (!currentClientId) continue;
    
    const parts = line.split(',');
    const month = parts[0];
    const viewsRaw = parts[1];
    if (!viewsRaw) continue; // No data for this month
    
    const parseVal = (v) => {
      if (v === undefined || v === null || v === '' || v === '設定なし') return '';
      return Number(v);
    };
    
    const views = parseVal(parts[1]);
    const phone = parseVal(parts[2]);
    const route = parseVal(parts[3]);
    const webclick = parseVal(parts[4]);
    const reviews = parseVal(parts[5]);
    const target = parseVal(parts[6]);
    const rating = parseVal(parts[7]);
    const posts = parseVal(parts[8]);
    
    if (views === '') continue; // Skip if no views data
    
    if (!appData[month]) appData[month] = {};
    if (!appData[month][currentClientId]) appData[month][currentClientId] = {};
    
    appData[month][currentClientId].insight_data = {
      views, phone, route, webclick, reviews, target, rating, posts
    };
    // mark as done
    appData[month][currentClientId].insight = 2;
  }
}

fs.writeFileSync(jsonPath, JSON.stringify(appData, null, 2));
console.log('Done mapping CSV to JSON.');
