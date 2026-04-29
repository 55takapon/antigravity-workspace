/**
 * Refine(繝ｪ繝輔ぃ繧､繝ｳ) 繝・せ繝医ョ繝ｼ繧ｿ 窶・菫ｮ豁｣迚・ * 蟋ｫ霍ｯ蟶ゅ・謨ｴ菴馴劼 窶・蜀咲｢ｺ隱肴ｸ医∩繝・・繧ｿ
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: 'Refine(繝ｪ繝輔ぃ繧､繝ｳ)',
    category: '謨ｴ菴・,
    address: '縲・70-0057 蜈ｵ蠎ｫ逵悟ｧｫ霍ｯ蟶ょ圏莉雁ｮｿ2荳∫岼2-8 繧ｳ繝ｼ繧ｸ繝ｼ繧ｳ繝ｼ繝・ 101',
    phone: '079-260-7714',
    website: 'https://shisei-himeji.com/',
    hours: {
      monday: '螳壻ｼ第律',
      tuesday: '10:00縲・0:00',
      wednesday: '10:00縲・0:00',
      thursday: '10:00縲・0:00',
      friday: '10:00縲・0:00',
      saturday: '10:00縲・0:00',
      sunday: '螳壻ｼ第律'
    },
    // 隱ｬ譏取枚: GBP蟆ら畑譫・医が繝ｼ繝翫・謠蝉ｾ幢ｼ峨↓縺ｯ譛ｪ險ｭ螳・    // Google讀懃ｴ｢縺ｧ縺ｯ繧ｵ繧､繝医・meta description縺瑚｡ｨ遉ｺ縺輔ｌ繧九′縲・    // GBP縺ｮ縲瑚ｪｬ譏弱阪ヵ繧｣繝ｼ繝ｫ繝峨→縺ｯ逡ｰ縺ｪ繧・    description: '',
    descriptionLength: 0,
    attributes: [
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・鬧占ｻ雁ｴ',
      '豎ｺ貂域婿豕・ 繧ｯ繝ｬ繧ｸ繝・ヨ繧ｫ繝ｼ繝・
    ],
    serviceItems: [],
    menuUrl: null,
    reservationUrl: 'https://beauty.hotpepper.jp/'
  },
  reviews: {
    totalCount: 58,
    averageRating: 4.9,
    // 譛譁ｰ鬆・〒15莉ｶ繧ｵ繝ｳ繝励Μ繝ｳ繧ｰ 窶・蜈ｨ莉ｶ繧ｪ繝ｼ繝翫・霑比ｿ｡縺ゅｊ
    items: [
      { rating: 5, hasReply: true, hasText: true, date: '2騾ｱ髢灘燕' },   // 鬮俶ｩ句茜蜈ｸ縺輔ｓ
      { rating: 5, hasReply: true, hasText: true, date: '2騾ｱ髢灘燕' },   // 蝮ょ哨蜍昜ｸ縺輔ｓ
      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '2縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '3縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '3縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '4縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '6縺区怦蜑・ },
      { rating: 4, hasReply: true, hasText: true, date: '8縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '2蟷ｴ蜑・ }
    ],
    replyRateNote: '譛譁ｰ15莉ｶ縺ｮ繧ｵ繝ｳ繝励Μ繝ｳ繧ｰ: 蜈ｨ莉ｶ霑比ｿ｡遒ｺ隱肴ｸ医∩',
    sentiment: {
      positive: ['蟋ｿ蜍｢', '閻ｰ', '蜈育函', '繝｡繝ｳ繝・リ繝ｳ繧ｹ', '繧ｹ繝・く繝ｪ', '遲九ヨ繝ｬ', '鬆ｭ逞・, '驕句虚'],
      negative: []
    }
  },
  photos: {
    totalCount: 45,
    categories: {
      exterior: true,   // 繧ｪ繝ｼ繝翫・謠蝉ｾ帙・螟冶ｦｳ蜀咏悄縺ゅｊ・育岼隕也｢ｺ隱肴ｸ医∩・・      interior: true,    // 繧ｪ繝ｼ繝翫・謠蝉ｾ帙・蜀・ｦｳ蜀咏悄縺ゅｊ・育岼隕也｢ｺ隱肴ｸ医∩・・      menu: false,       // 譁ｽ陦薙Γ繝九Η繝ｼ蜀咏悄縺ｯ蟆ら畑譫縺ｪ縺・      staff: true        // 譁ｽ陦楢・・逵溘≠繧・    },
    hasVideo: true       // 蜍慕判繧ｫ繝・ざ繝ｪ縺ゅｊ
  },
  posts: {
    // 螳滓・: 蜈ｨ11莉ｶ縲・025/7譛医↓髮・ｸｭ縲・0譛医↓1莉ｶ蠕娯・5繝ｶ譛育ｩｺ逋ｽ竊・026/3譛医↓2莉ｶ蜀埼幕
    // 逶ｴ霑・繝ｶ譛茨ｼ・026/1-3譛茨ｼ峨・2莉ｶ縺ｮ縺ｿ
    totalRecent: 2,
    latestDate: '2026-03-28',
    recentDates: ['2026-03-28', '2026-03-16'],
    gapMonths: 5,            // 2025/10竊・026/3 縺ｮ5繝ｶ譛育ｩｺ逋ｽ
    hasKeywordContent: false, // 逶ｴ霑第兜遞ｿ縺ｯ譌･蟶ｸ蝣ｱ蜻贋ｸｭ蠢・ｼ医♀蝨溽肇縲∝ｧｿ蜍｢隰帛ｺｧ蝣ｱ蜻奇ｼ・    hasCasualOnly: true,      // 縲梧紛菴薙阪瑚・逞帙咲ｭ峨く繝ｼ繝ｯ繝ｼ繝牙性縺ｾ縺・    hasEvent: false,
    postTypes: ['譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ']
  },
  competitors: [
    { name: '蟋ｫ霍ｯ鬧・燕髯｢', category: '謨ｴ菴・, rating: 5.0, reviewCount: 29 },
    { name: '繝ｩ繧ｯ繝ｪ繧ｨ蟋ｫ霍ｯ鬧・燕髯｢', category: '謨ｴ菴・, rating: 4.9, reviewCount: 82 },
    { name: '蟋ｫ霍ｯ繧ｫ繧､繝ｭ繝励Λ繧ｯ繝・ぅ繝・け繧ｻ繝ｳ繧ｿ繝ｼ', category: '謨ｴ菴・, rating: 4.9, reviewCount: 103 },
    { name: '縺ｲ繧阪′繧区磁鬪ｨ髯｢繝ｻ骰ｼ轣ｸ髯｢ 闃ｱ逕ｰ髯｢', category: '謨ｴ菴・, rating: 4.8, reviewCount: 146 },
    { name: '蟯｡譛ｬ謨ｴ菴馴劼', category: '謨ｴ菴・, rating: 4.9, reviewCount: 153 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・蜀肴､懆ｨｼ貂医∩',
    searchQuery: '謨ｴ菴・蟋ｫ霍ｯ蟶・
  }
};

const result = analyzeGBP(data);

console.log('=== 繧ｹ繧ｳ繧｢繝ｪ繝ｳ繧ｰ邨先棡 ===');
console.log(`繝薙ず繝阪せ蜷・ ${result.businessName}`);
console.log(`讌ｭ遞ｮ蛻､螳・ ${result.industry.label}`);
console.log(`邱丞粋繧ｹ繧ｳ繧｢: ${result.totalRank.rank} (${result.totalScore}/100)`);
console.log('');
console.log('5霆ｸ繧ｹ繧ｳ繧｢:');
for (const axis of result.axes) {
  console.log(`  ${axis.rank.rank} ${axis.label}: ${axis.score}轤ｹ`);
}

// JST固定で日付生成（UTC+9）
const now = new Date();
const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const dateStr = jst.toISOString().slice(0, 10).replace(/-/g, '');
const baseName = `diagnostic_report_refine_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_refine_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
