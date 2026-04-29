/**
 * 繝壹ャ繝医す繝・ち繝ｼ 縺ｫ繧・ｓ縺ｽ繧・繝・せ繝医ョ繝ｼ繧ｿ
 * 譚ｱ莠ｬ驛ｽ豎滓虻蟾晏玄 迪ｫ蟆る摩繝壹ャ繝医す繝・ち繝ｼ
 * 繝・・繧ｿ蜿朱寔譌･: 2026-03-29 繝悶Λ繧ｦ繧ｶ逶ｮ隕也｢ｺ隱肴ｸ医∩
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '繝壹ャ繝医す繝・ち繝ｼ 縺ｫ繧・ｓ縺ｽ繧・,
    category: '繝壹ャ繝医す繝・ち繝ｼ',
    address: '縲・32-0013 譚ｱ莠ｬ驛ｽ豎滓虻蟾晏玄豎滓虻蟾・荳∫岼3逡ｪ63',
    phone: '090-4742-1246',
    website: 'nyanpon-2222.com',
    hours: {
      monday: '8:00縲・8:00',
      tuesday: '8:00縲・8:00',
      wednesday: '8:00縲・8:00',
      thursday: '8:00縲・8:00',
      friday: '8:00縲・8:00',
      saturday: '8:00縲・8:00',
      sunday: '8:00縲・8:00'
    },
    description: '豎滓虻蟾晏玄縺ｧ迪ｫ縺｡繧・ｓ蟆る摩縺ｮ繝壹ャ繝医す繝・ち繝ｼ繧ｵ繝ｼ繝薙せ繧呈署萓帙＠縺ｦ縺・∪縺吶よ羅陦後・蜃ｺ蠑ｵ繝ｻ蜈･髯｢繝ｻ諤･縺ｪ螟門・縺ｪ縺ｩ縺ｧ縺雁ｮｶ繧堤蕗螳医↓縺輔ｌ繧矩圀縲・｣ｼ縺・ｸｻ縺輔∪縺ｫ莉｣繧上▲縺ｦ螟ｧ蛻・↑螳ｶ譌上ｒ諢帶ュ縺溘▲縺ｷ繧翫↓縺贋ｸ冶ｩｱ縺・◆縺励∪縺吶ら賢縺｡繧・ｓ縺ｮ諤ｧ譬ｼ繧・律縲・・鄙呈・縺ｫ蜷医ｏ縺帙※縲・｣滉ｺ区ｺ門ｙ窶｢縺頑ｰｴ縺ｮ莠､謠帚｢繝医う繝ｬ縺頑祉髯､繝ｻ驕翫・繝ｻ繝悶Λ繝・す繝ｳ繧ｰ縺ｪ縺ｩ縲∵勸谿ｵ騾壹ｊ縺ｮ螳牙ｿ・〒縺阪ｋ迺ｰ蠅・ｒ螳医ｊ縺ｾ縺吶ょ・蝗槭↓莠句燕縺頑遠縺｡蜷医ｏ縺幢ｼ・譎る俣遞九♀譎る俣繧偵＞縺溘□縺阪∪縺呻ｼ峨ｒ陦後＞縲∝▼蠎ｷ迥ｶ諷九ｄ逕滓ｴｻ繧ｹ繧ｿ繧､繝ｫ繧定ｩｳ縺励￥縺贋ｼｺ縺・＠縺ｾ縺吶ゅ♀荳冶ｩｱ蠕後・蜀咏悄繧・虚逕ｻ縺ｧ縺泌ｱ蜻翫＠縲・｣ｼ縺・ｸｻ縺輔∪縺ｮ荳榊ｮ峨ｒ霆ｽ貂帙＠縺ｾ縺吶よｱ滓虻蟾晏玄蜀・♀繧医・霑鷹團蝨ｰ蝓溘∈縺ｮ險ｪ蝠丞ｯｾ蠢懊ょ・蝗槫牡蠑輔く繝｣繝ｳ繝壹・繝ｳ螳滓命荳ｭ縲ょｮ牙ｿ・・螳牙・繝ｻ菫｡鬆ｼ縺ｮ繝壹ャ繝医す繝・ち繝ｼ縺ｨ縺励※縲√≠縺ｪ縺溘→繝壹ャ繝医・蠢ｫ驕ｩ縺ｪ豈取律繧偵♀謇倶ｼ昴＞縺励∪縺吶・,  // GBP險ｭ螳壽ｸ医∩・育ｴ・84譁・ｭ暦ｼ・    attributes: [
      '螂ｳ諤ｧ繧ｪ繝ｼ繝翫・'
    ],
    serviceItems: [],
    menuUrl: null,
    reservationUrl: null
  },
  reviews: {
    totalCount: 2,
    averageRating: 5.0,
    items: [
      { rating: 5, hasReply: true, hasText: true, date: '2縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '3縺区怦蜑・ }
    ],
    replyRateNote: '蜈ｨ2莉ｶ霑比ｿ｡貂医∩・・00%・・,
    sentiment: {
      positive: ['荳∝ｯｧ', '螳牙ｿ・, '蝣ｱ蜻・, '迪ｫ', '縺贋ｸ冶ｩｱ'],
      negative: []
    }
  },
  photos: {
    totalCount: 4,
    categories: {
      exterior: false,    // 險ｪ蝠丞梛縺ｪ縺ｮ縺ｧ螟冶ｦｳ縺ｪ縺・      interior: false,    // 險ｪ蝠丞梛縺ｪ縺ｮ縺ｧ蜀・ｦｳ縺ｪ縺・      menu: false,
      staff: true         // 繧ｪ繝ｼ繝翫・・狗賢縺ｮ蜀咏悄縺ゅｊ
    },
    hasVideo: false
  },
  posts: {
    totalRecent: 4,       // 1譛・莉ｶ+2譛・莉ｶ・医Θ繝ｼ繧ｶ繝ｼ逕ｳ蜻・ 譛・謚慕ｨｿ・・    latestDate: '2026-03-23',
    recentDates: ['2026-03-23', '2026-03-04', '2026-02-15', '2026-02-01'],
    gapMonths: 0,
    hasKeywordContent: true,
    hasCasualOnly: false,
    hasEvent: false,
    postTypes: ['譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ']
  },
  competitors: [
    { name: 'Mermaid', category: '繝壹ャ繝医す繝・ち繝ｼ', rating: 5.0, reviewCount: 44 },
    { name: '縲千堪迪ｫ蟆る摩縲代・繝・ヨ繧ｷ繝・ち繝ｼ繧ｺ譚ｱ莠ｬ繝吶う', category: '繝壹ャ繝医す繝・ち繝ｼ', rating: 4.9, reviewCount: 35 },
    { name: '繝壹ャ繝医す繝・ち繝ｼ縺翫≧縺｡縺ｧ縺・▲縺励ｇ', category: '繝壹ャ繝医す繝・ち繝ｼ', rating: 5.0, reviewCount: 10 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '繝壹ャ繝医す繝・ち繝ｼ 豎滓虻蟾・
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
const baseName = `diagnostic_report_nyanpon_petsitter_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_nyanpon_petsitter_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
