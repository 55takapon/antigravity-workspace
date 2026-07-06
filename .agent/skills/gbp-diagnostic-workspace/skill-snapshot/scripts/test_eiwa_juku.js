/**
 * 闍ｱ蜥悟｡ｾ 繝・せ繝医ョ繝ｼ繧ｿ
 * 蜉蜿､蟾晏ｸゑｼ域擲蜉蜿､蟾晢ｼ牙ｭｦ鄙貞｡ｾ繝ｻ蜿鈴ｨ謎ｺ亥ｙ譬｡
 * 繝・・繧ｿ蜿朱寔譌･: 2026-03-28 逶ｮ隕也｢ｺ隱肴ｸ医∩
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '闍ｱ蜥悟｡ｾ',
    category: '蜿鈴ｨ謎ｺ亥ｙ譬｡',
    address: '縲・75-0102 蜈ｵ蠎ｫ逵悟刈蜿､蟾晏ｸょｹｳ蟯｡逕ｺ隘ｿ隹ｷ206-2',
    phone: '079-427-1011',
    website: 'eiwajuku.com',
    hours: {
      monday: '17:00縲・2:00',
      tuesday: '17:00縲・2:00',
      wednesday: '17:00縲・2:00',
      thursday: '17:00縲・2:00',
      friday: '17:00縲・2:00',
      saturday: '14:00縲・2:00',
      sunday: '螳壻ｼ第律'
    },
    // GBP隱ｬ譏取枚: Google讀懃ｴ｢繝翫Ξ繝・ず繝代ロ繝ｫ縺ｧ遒ｺ隱肴ｸ医∩・育ｴ・60譁・ｭ暦ｼ・    description: '縲後〒縺阪↑縺九▲縺溘％縺ｨ繧偵〒縺阪ｋ縺薙→縺ｸ縲・繧ｫ繝輔ぉ縺ｮ繧医≧縺ｪ髢区叛逧・↑謨吝ｮ､縺ｧ縲√い繝・ヨ繝帙・繝縺ｫ蟄ｦ縺ｹ繧玖恭蜥悟｡ｾ 蟷ｳ蟯｡蜊玲｡縲りｳｪ蝠上＠繧・☆縺・峅蝗ｲ豌励・螳悟・蛟句挨謗域･ｭ縺ｧ縲∝級蠑ｷ繧ゆｺｺ髢灘鴨繧りご縺ｦ縺ｾ縺吶ゅ瑚ｦｪ縺ｨ縺励※騾壹ｏ縺帙◆縺・｡ｾ縲阪ｒ逶ｮ謖・＠縺ｦ縺・∪縺吶・R譚ｱ蜉蜿､蟾晞ｧ・ｾ呈ｭｩ10蛻・辟｡譁吩ｽ馴ｨ灘ｮ滓命荳ｭ',
    attributes: [
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・鬧占ｻ雁ｴ・域悴蟇ｾ蠢懶ｼ・,
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・蜈･繧雁哨・域悴蟇ｾ蠢懶ｼ・,
      '螳｢螻､: LGBTQ繝輔Ξ繝ｳ繝峨Μ繝ｼ',
      '螳｢螻､: 繝医Λ繝ｳ繧ｹ繧ｸ繧ｧ繝ｳ繝繝ｼ蟇ｾ蠢・
    ],
    serviceItems: [],
    menuUrl: null,
    reservationUrl: null
  },
  reviews: {
    totalCount: 1,
    averageRating: 5.0,
    // 1莉ｶ縺ｮ縺ｿ繝ｻ繧ｪ繝ｼ繝翫・譛ｪ霑比ｿ｡
    items: [
      { rating: 5, hasReply: false, hasText: true, date: '2縺区怦蜑・ }  // 縲悟・逕溘′縺・▽繧りｦｪ霄ｫ縺ｫ蜷代″蜷医▲縺ｦ縺上□縺輔ｋ縲・    ],
    replyRateNote: '蜈ｨ1莉ｶ: 0/1莉ｶ譛ｪ霑比ｿ｡',
    sentiment: {
      positive: ['隕ｪ霄ｫ', '螳牙ｿ・, '讌ｽ縺励∩'],
      negative: []
    }
  },
  photos: {
    totalCount: 15,   // 繧ｪ繝ｼ繝翫・謠蝉ｾ・繧ｹ繝医Μ繝ｼ繝医ン繝･繝ｼ蜷ｫ繧
    categories: {
      exterior: true,    // 逵区攸繝ｻ螟冶ｦｳ縺ゅｊ
      interior: true,    // 謨吝ｮ､蜀・ｦｳ・医き繝輔ぉ鬚ｨ・峨≠繧・      menu: false,       // 譁咎≡陦ｨ繝ｻ繧ｳ繝ｼ繧ｹ邏ｹ莉九↑縺・      staff: false       // 隰帛ｸｫ蜀咏悄縺ｪ縺暦ｼ域兜遞ｿ縺ｫ縺ｯ鬘泌・縺励≠繧奇ｼ・    },
    hasVideo: false
  },
  posts: {
    totalRecent: 1,       // 逶ｴ霑・繝ｶ譛・ 2026/02/20縺ｮ1莉ｶ
    latestDate: '2026-02-20',
    recentDates: ['2026-02-20'],
    gapMonths: 1,         // 1繝ｶ譛亥燕
    hasKeywordContent: true,  // 蜿鈴ｨ薙・繝｡繝ｳ繧ｿ繝ｫ繧ｱ繧｢髢｢騾｣縺ｮ繧ｭ繝ｼ繝ｯ繝ｼ繝牙性繧
    hasCasualOnly: false,
    hasEvent: false,
    postTypes: ['譛譁ｰ諠・ｱ']
  },
  competitors: [
    { name: '謨呵ご遨ｺ髢薙お繧ｰ繧ｼ 譚ｱ蜉蜿､蟾晄｡', category: '謨呵ご繧ｻ繝ｳ繧ｿ繝ｼ', rating: 5.0, reviewCount: 15 },
    { name: '蛟句挨謖・ｰ弱∪縺ｪ縺ｳ繝励Λ繧ｹ 譚ｱ蜉蜿､蟾晄蕗螳､', category: '蜿鈴ｨ謎ｺ亥ｙ譬｡', rating: 4.7, reviewCount: 22 },
    { name: '繧ｨ繝・ぅ繝・け 譚ｱ蜉蜿､蟾晄｡', category: '蜿鈴ｨ謎ｺ亥ｙ譬｡', rating: 4.8, reviewCount: 6 },
    { name: '蜑ｵ遐泌ｭｦ髯｢ 譚ｱ蜉蜿､蟾晄｡', category: '蜿鈴ｨ謎ｺ亥ｙ譬｡', rating: 5.0, reviewCount: 2 },
    { name: '縺ｾ繧薙※繧灘句挨 譚ｱ蜉蜿､蟾晄蕗螳､', category: '蜿鈴ｨ謎ｺ亥ｙ譬｡', rating: 4.7, reviewCount: 6 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) + Google Search 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '蟄ｦ鄙貞｡ｾ 譚ｱ蜉蜿､蟾・
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
const baseName = `diagnostic_report_eiwa_juku_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_eiwa_juku_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
