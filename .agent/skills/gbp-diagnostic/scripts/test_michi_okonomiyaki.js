/**
 * 縺ｿ縺｡ 繝・せ繝医ョ繝ｼ繧ｿ
 * 蜉蜿､蟾晏ｸゑｼ域擲蜉蜿､蟾晢ｼ峨♀螂ｽ縺ｿ辟ｼ縺榊ｺ・ * 繝・・繧ｿ蜿朱寔譌･: 2026-03-28 逶ｮ隕也｢ｺ隱肴ｸ医∩
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '縺ｿ縺｡',
    category: '縺雁･ｽ縺ｿ辟ｼ縺榊ｺ・,
    address: '縲・75-0105 蜈ｵ蠎ｫ逵悟刈蜿､蟾晏ｸょｹｳ蟯｡逕ｺ2-15',
    phone: '070-1828-0103',
    website: 'youtu.be/C2CoM7zBDFM',   // YouTube繝ｪ繝ｳ繧ｯ縺後え繧ｧ繝悶し繧､繝医→縺励※逋ｻ骭ｲ
    hours: {
      monday: '螳壻ｼ第律',
      tuesday: '螳壻ｼ第律',
      wednesday: '螳壻ｼ第律',
      thursday: '11:30縲・4:00, 17:30縲・1:00',
      friday: '11:30縲・4:00, 17:30縲・1:00',
      saturday: '11:30縲・4:00, 17:30縲・1:00',
      sunday: '11:30縲・4:00, 17:30縲・1:00'
    },
    description: '',  // GBP隱ｬ譏取枚譛ｪ險ｭ螳・    attributes: [
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・鬧占ｻ雁ｴ・域悴蟇ｾ蠢懶ｼ・,
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・蜈･繧雁哨・域悴蟇ｾ蠢懶ｼ・,
      '繧ｵ繝ｼ繝薙せ繧ｪ繝励す繝ｧ繝ｳ: 螳・・',
      '繧ｵ繝ｼ繝薙せ繧ｪ繝励す繝ｧ繝ｳ: 繝・う繧ｯ繧｢繧ｦ繝・,
      '繧ｵ繝ｼ繝薙せ繧ｪ繝励す繝ｧ繝ｳ: 繧､繝ｼ繝医う繝ｳ',
      '莠ｺ豌・ 繝ｩ繝ｳ繝√↓莠ｺ豌・,
      '莠ｺ豌・ 繝・ぅ繝翫・縺ｫ莠ｺ豌・,
      '莠ｺ豌・ 荳莠ｺ縺ｧ縺ｮ鬟滉ｺ・,
      '繧ｵ繝ｼ繝薙せ: 繧｢繝ｫ繧ｳ繝ｼ繝ｫ鬟ｲ譁・,
      '繧ｵ繝ｼ繝薙せ: 繝薙・繝ｫ',
      '繧ｵ繝ｼ繝薙せ: 霆ｽ鬟・,
      '螳｢螻､: 繧ｰ繝ｫ繝ｼ繝怜ｮ｢',
      '繝励Λ繝ｳ: 莠育ｴ・庄',
      '豎ｺ貂域婿豕・ 讌ｽ螟ｩ繝壹う',
      '蟄蝉ｾ・ 蟄舌←繧ょ髄縺・,
      '鬧占ｻ雁ｴ: 辟｡譁咎ｧ占ｻ雁ｴ'
    ],
    serviceItems: ['繧､繝ｼ繝医う繝ｳ', '繝・う繧ｯ繧｢繧ｦ繝・, '螳・・'],
    menuUrl: null,
    reservationUrl: null,
    priceRange: 'ﾂ･1,000縲・,000'
  },
  reviews: {
    totalCount: 47,
    averageRating: 4.5,
    // 譛譁ｰ鬆・2莉ｶ遒ｺ隱・ 1/12莉ｶ縺ｫ霑比ｿ｡ 竊・霑比ｿ｡邇・%
    items: [
      { rating: 5, hasReply: true, hasText: true, date: '2騾ｱ髢灘燕' },   // 繧ｬ繧ｨ繝ｫ繧医＠ 竊・蜚ｯ荳霑比ｿ｡縺ゅｊ
      { rating: 4, hasReply: false, hasText: true, date: '1縺区怦蜑・ },  // 縺溘∴縺・      { rating: 5, hasReply: false, hasText: true, date: '1縺区怦蜑・ },  // 譏ｭ莠・      { rating: 4, hasReply: false, hasText: true, date: '2縺区怦蜑・ },  // CoCo Nuts
      { rating: 5, hasReply: false, hasText: true, date: '2縺区怦蜑・ },  // 阯､蜴溽ｾ惹ｽ仙ｭ・      { rating: 5, hasReply: false, hasText: true, date: '5縺区怦蜑・ },  // 縺ゅ≠
      { rating: 4, hasReply: false, hasText: true, date: '6縺区怦蜑・ },  // 縺翫♀縺ｲ縺輔◆繧ゅ▽
      { rating: 5, hasReply: false, hasText: true, date: '7縺区怦蜑・ },  // T.Y
      { rating: 5, hasReply: false, hasText: true, date: '8縺区怦蜑・ },  // h o
      { rating: 5, hasReply: false, hasText: true, date: '10縺区怦蜑・ }, // 縺吶↑S
      { rating: 5, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },    // 貂｡驍顔ｾ主ｹｸ
      { rating: 5, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ }     // 蟒｣轢ｬ縺ゅｆ縺ｿ
    ],
    replyRateNote: '譛譁ｰ12莉ｶ遒ｺ隱・ 1/12莉ｶ(8%)縺ｮ縺ｿ霑比ｿ｡縲ら峩霑・騾ｱ髢薙・1莉ｶ縺ｮ縺ｿ蟇ｾ蠢懊・,
    sentiment: {
      positive: ['螟ｫ蟀ｦ', '繝帙Ν繝｢繝ｳ縺・←繧・, '縺昴・', '辣ｮ霎ｼ縺ｿ', '縺翫〒繧・, '驩・攸辟ｼ縺・, '縺ｵ繧上・繧・, '鄒主袖縺励＞'],
      negative: []
    }
  },
  photos: {
    totalCount: 14,    // 繧ｪ繝ｼ繝翫・+繝ｦ繝ｼ繧ｶ繝ｼ蜷郁ｨ・    categories: {
      exterior: true,    // 螟冶ｦｳ蜀咏悄縺ゅｊ
      interior: true,    // 繧ｫ繧ｦ繝ｳ繧ｿ繝ｼ繝ｻ蠎怜・蜀咏悄縺ゅｊ
      menu: true,        // 繝｡繝九Η繝ｼ蜀咏悄縺ゅｊ・医♀縺励↑縺後″・・      staff: false       // 繧ｹ繧ｿ繝・ヵ蜀咏悄縺ｪ縺・    },
    hasVideo: false
  },
  posts: {
    // 譛譁ｰ謚慕ｨｿ: 2025/10/09縲梧悽譌･雋ｸ蛻・坂・ 邏・.5繝ｶ譛亥燕縺ｮ驕句霧騾｣邨｡縺ｮ縺ｿ
    totalRecent: 0,       // 逶ｴ霑・繝ｶ譛医・謚慕ｨｿ0莉ｶ
    latestDate: '2025-10-09',
    recentDates: [],
    gapMonths: 5,         // 5繝ｶ譛井ｻ･荳翫・遨ｺ逋ｽ
    hasKeywordContent: false,  // 縲梧悽譌･雋ｸ蛻・阪・驕句霧騾｣邨｡縺ｧ繧ｭ繝ｼ繝ｯ繝ｼ繝牙ｯｾ遲悶↑縺・    hasCasualOnly: true,
    hasEvent: false,
    postTypes: []
  },
  competitors: [
    { name: '豐ｳ遶･', category: '縺雁･ｽ縺ｿ辟ｼ縺榊ｺ・, rating: 4.3, reviewCount: 88 },
    { name: '縺ｾ縺斐∩', category: '縺雁･ｽ縺ｿ辟ｼ縺榊ｺ・, rating: 4.1, reviewCount: 87 },
    { name: '縺雁･ｽ縺ｿ辟ｼ 縺ｯ繧医＠譛ｬ蠎・, category: '縺雁･ｽ縺ｿ辟ｼ縺榊ｺ・, rating: 4.0, reviewCount: 84 },
    { name: '縺雁･ｽ縺ｿ辟ｼ縺阪・驩・攸繝舌Ν ORIGAMI', category: '縺雁･ｽ縺ｿ辟ｼ縺榊ｺ・, rating: 4.5, reviewCount: 48 },
    { name: '縺溘％蜈ｫ', category: '縺雁･ｽ縺ｿ辟ｼ縺榊ｺ・, rating: 4.4, reviewCount: 37 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '縺雁･ｽ縺ｿ辟ｼ縺・譚ｱ蜉蜿､蟾・
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
  if (axis.details && axis.details.length > 0) {
    for (const d of axis.details) {
      console.log(`     竊・${d}`);
    }
  }
}

// JST固定で日付生成（UTC+9）
const now = new Date();
const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const dateStr = jst.toISOString().slice(0, 10).replace(/-/g, '');
const baseName = `diagnostic_report_michi_okonomiyaki_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_michi_okonomiyaki_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
