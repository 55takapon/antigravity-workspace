/**
 * 繧ｸ繧ｧ繝・ヨ繝励Ο繝・Η繝ｼ繧ｹ 繝・せ繝医ョ繝ｼ繧ｿ
 * 蜉蜿､蟾晏ｸ・繧､繝ｳ繧ｿ繝ｼ繝阪ャ繝医・繝ｼ繧ｱ繝・ぅ繝ｳ繧ｰ讌ｭ
 * 繝・・繧ｿ蜿朱寔譌･: 2026-03-28 逶ｮ隕也｢ｺ隱肴ｸ医∩
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '繧ｸ繧ｧ繝・ヨ繝励Ο繝・Η繝ｼ繧ｹ',
    category: '繧､繝ｳ繧ｿ繝ｼ繝阪ャ繝・繝槭・繧ｱ繝・ぅ繝ｳ繧ｰ讌ｭ',
    address: '縲・75-0042 蜈ｵ蠎ｫ逵悟刈蜿､蟾晏ｸり･ｿ逾槫翠逕ｺ隘ｿ譚・28-2',
    phone: '',  // 髮ｻ隧ｱ逡ｪ蜿ｷ譛ｪ逋ｻ骭ｲ
    website: 'jet-produce.com',
    hours: {
      monday: '9:00縲・7:30',
      tuesday: '9:00縲・7:30',
      wednesday: '9:00縲・7:30',
      thursday: '9:00縲・7:30',
      friday: '9:00縲・7:30',
      saturday: '螳壻ｼ第律',
      sunday: '螳壻ｼ第律'
    },
    description: '縲隈oogle繝槭ャ繝励↓霈峨○縺ｦ縺・ｋ縺ｮ縺ｫ縲∵眠隕上・縺雁ｮ｢縺輔∪縺梧擂縺ｪ縺・阪◎縺ｮ謔ｩ縺ｿ縲∝､壹￥縺ｮ莠区･ｭ閠・＆縺ｾ縺九ｉ閨槭＞縺ｦ縺阪∪縺励◆縲ゅず繧ｧ繝・ヨ繝励Ο繝・Η繝ｼ繧ｹ縺ｯ縲；oogle繝薙ず繝阪せ繝励Ο繝輔ぅ繝ｼ繝ｫ・・EO・峨・驕狗畑繝ｻ謾ｹ蝟・ｒ襍ｷ轤ｹ縺ｫ縲∝ｺ苓・繝ｻ繧ｯ繝ｪ繝九ャ繧ｯ縺ｮWeb髮・ｮ｢繧剃ｸｸ縺斐→繧ｵ繝昴・繝医☆繧句ｰる摩莠句漁謇縺ｧ縺吶よｭｯ遘代け繝ｪ繝九ャ繧ｯ縺ｧ譛磯俣100莉ｶ縺ｮ髮ｻ隧ｱ蝠上＞蜷医ｏ縺帙ｒ螳溽樟縺吶ｋ縺ｪ縺ｩ縲∵･ｭ遞ｮ繧貞撫繧上★謌先棡繧偵▽縺上▲縺ｦ縺阪∪縺励◆縲ゅ・繝ｼ繝繝壹・繧ｸ繝ｻInstagram繝ｻSEO繝ｻ繝槭ャ繝励ゅヰ繝ｩ繝舌Λ縺ｫ驕狗畑縺励※縺・※繧ゅ・寔螳｢縺ｯ縺ｪ縺九↑縺九°縺ｿ蜷医＞縺ｾ縺帙ｓ縲・EO莉｣陦碁°逕ｨ縺九ｉ縲∝哨繧ｳ繝溽ｮ｡逅・・謚慕ｨｿ繝ｻ蜀咏悄譖ｴ譁ｰ縺ｾ縺ｧ縲ゅΟ繝ｼ繧ｫ繝ｫSEO繧定ｻｸ縺ｫ縲√・繝・・荳贋ｽ崎｡ｨ遉ｺ繧堤岼謖・＠縺滄寔螳｢縺ｮ莉慕ｵ・∩蛹悶ｒ險ｭ險医＠縺ｾ縺吶ょ・菴薙ｒ謨ｴ逅・＠縺ｦ縲∫┌鬧・・縺ｪ縺・ｻ慕ｵ・∩繧剃ｸ邱偵↓縺､縺上ｊ縺ｾ縺吶・,  // Google讀懃ｴ｢邨先棡縺ｧ遒ｺ隱肴ｸ医∩
    attributes: [
      '繧ｵ繝ｼ繝薙せ繧ｪ繝励す繝ｧ繝ｳ: 螳溷ｺ苓・縺ｮ蝟ｶ讌ｭ縺ｪ縺・
    ],
    serviceItems: [],
    menuUrl: null,
    reservationUrl: null
  },
  reviews: {
    totalCount: 5,
    averageRating: 5.0,
    // 譛譁ｰ鬆・莉ｶ繧ｵ繝ｳ繝励Μ繝ｳ繧ｰ 窶・蜈ｨ莉ｶ遒ｺ隱・    items: [
      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },   // 隘ｿ譽ｮ闖懈怦
      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },   // 繝懊Β繝翫Ν繝√く繝ｳ
      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },   // Mayumi Sato
      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },   // 縺ゅｊ縺後→縺・し繝ｼ繝薙せ
      { rating: 5, hasReply: false, hasText: true, date: '1縺区怦蜑・ }   // makiko・郁ｿ比ｿ｡縺ｪ縺暦ｼ・    ],
    replyRateNote: '蜈ｨ5莉ｶ遒ｺ隱・ 4/5莉ｶ縺ｫ霑比ｿ｡縺ゅｊ',
    sentiment: {
      positive: ['謚慕ｨｿ', '蜉ｩ縺九ｋ', 'SNS', '繝槭・繧ｱ繝・ぅ繝ｳ繧ｰ', '荳∝ｯｧ', '蜿｣繧ｳ繝・, '繧｢繝峨ヰ繧､繧ｹ'],
      negative: []
    }
  },
  photos: {
    totalCount: 1,   // 繧ｪ繝ｼ繝翫・謠蝉ｾ・譫壹・縺ｿ
    categories: {
      exterior: false,   // 螟冶ｦｳ蜀咏悄縺ｪ縺・      interior: false,    // 蠎怜・蜀咏悄縺ｪ縺暦ｼ医ョ繧ｹ繧ｯ蜻ｨ繧翫・蜀咏悄1譫壹′蜀・ｦｳ縺ｫ霑代＞縺梧ｭ｣蠑上↓縺ｯ荳榊香蛻・ｼ・      menu: false,        // 繧ｵ繝ｼ繝薙せ邏ｹ莉句・逵溘↑縺・      staff: false        // 繧ｹ繧ｿ繝・ヵ蜀咏悄縺ｪ縺・    },
    hasVideo: false
  },
  posts: {
    totalRecent: 0,       // 謚慕ｨｿ縺ｪ縺・    latestDate: null,
    recentDates: [],
    gapMonths: 0,
    hasKeywordContent: false,
    hasCasualOnly: false,
    hasEvent: false,
    postTypes: []
  },
  competitors: [
    { name: '繧｢繝医Μ繧ｨ繧ｯ繝ｬ繝・, category: '繧ｦ繧ｧ繝悶ョ繧ｶ繧､繝翫・', rating: 5.0, reviewCount: 18 },
    { name: '譬ｪ蠑丈ｼ夂､ｾLin繝・じ繧､繝ｳ莠句漁謇', category: '繧ｦ繧ｧ繝悶ョ繧ｶ繧､繝翫・', rating: 5.0, reviewCount: 2 },
    { name: '譬ｪ蠑丈ｼ夂､ｾAWESOME', category: '繧ｦ繧ｧ繝悶ョ繧ｶ繧､繝翫・', rating: 5.0, reviewCount: 1 },
    { name: 'KOBE locoshop', category: '繧､繝ｳ繧ｿ繝ｼ繝阪ャ繝医・繝ｼ繧ｱ繝・ぅ繝ｳ繧ｰ讌ｭ', rating: 1.0, reviewCount: 1 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '繧､繝ｳ繧ｿ繝ｼ繝阪ャ繝医・繝ｼ繧ｱ繝・ぅ繝ｳ繧ｰ 蜉蜿､蟾・/ Web蛻ｶ菴・蜉蜿､蟾・
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
const baseName = `diagnostic_report_jetproduce_web_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_jetproduce_web_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
