/**
 * 繝溘・繝域ｭｯ遘・繝・せ繝医ョ繝ｼ繧ｿ
 * 蜈ｵ蠎ｫ逵碁ｫ倡ょｸ・荳闊ｬ豁ｯ遘托ｼ育浣豁｣蜷ｫ繧・・ * 繝・・繧ｿ蜿朱寔譌･: 2026-03-29 繝悶Λ繧ｦ繧ｶ逶ｮ隕也｢ｺ隱肴ｸ医∩
 * 迚ｹ谿贋ｺ矩・ 蜿｣繧ｳ繝溯ｿ比ｿ｡縺ｯ荳蛻・＠縺ｪ縺・婿驥晢ｼ医ロ繧ｬ繝・ぅ繝門哨繧ｳ繝溷ｯｾ遲厄ｼ・ */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '蛹ｻ逋よｳ穂ｺｺ遉ｾ蝗｣ 繝溘・繝域ｭｯ遘・,
    category: '豁ｯ遘大現髯｢',
    subcategories: ['遏ｯ豁｣豁ｯ遘・],
    address: '縲・76-0082 蜈ｵ蠎ｫ逵碁ｫ倡ょｸよ嵜譬ｹ逕ｺ2243-1',
    phone: '079-448-6480',
    website: 'meet-dc.com',
    hours: {
      monday: '9:00縲・3:00, 15:00縲・0:00',
      tuesday: '9:00縲・3:00, 15:00縲・0:00',
      wednesday: '9:00縲・3:00',
      thursday: '9:00縲・3:00, 15:00縲・0:00',
      friday: '9:00縲・3:00, 15:00縲・0:00',
      saturday: '9:00縲・3:00, 14:00縲・7:00',
      sunday: '螳壻ｼ第律'
    },
    description: '蜈ｵ蠎ｫ逵碁ｫ倡ょｸゅ∝ｱｱ髯ｽ譖ｽ譬ｹ鬧・°繧牙ｾ呈ｭｩ10蛻・・縲悟現逋よｳ穂ｺｺ遉ｾ蝗｣ 繝溘・繝域ｭｯ遘代阪〒縺吶ょ慍蝓溘・逧・ｧ倥・縺雁哨縺ｮ蛛･蠎ｷ繧堤函豸ｯ縺ｫ繧上◆縺｣縺ｦ螳医ｋ縺薙→繧堤岼讓吶↓縲∵ぅ閠・ｧ倅ｸ莠ｺ縺ｲ縺ｨ繧翫・縺碑ｦ∵悍縺ｫ蟇・ｊ豺ｻ縺｣縺溯ｨｺ逋ゅｒ陦後▲縺ｦ縺・∪縺吶・繝溘・繝域ｭｯ遘代〒縺ｯ縲∵･ｵ蜉帑ｿ晞匱豐ｻ逋ゅ〒譛螟ｧ髯舌梧ｭｯ縲阪ｒ谿九○繧九ｈ縺・↓蜉ｪ繧√※縺翫ｊ縺ｾ縺吶・險ｺ逋らｧ醍岼縺ｯ縲∬勠豁ｯ繝ｻ豁ｯ蜻ｨ逞・ｲｻ逋ゅ↑縺ｩ縺ｮ荳闊ｬ豁ｯ遘代°繧峨∽ｺ磯亟豁ｯ遘代∫浣豁｣豁ｯ遘代・蟆丞・遏ｯ豁｣豁ｯ遘代√う繝ｳ繝励Λ繝ｳ繝医√そ繝ｩ繝溘ャ繧ｯ豐ｻ逋ゅ√・繝ｯ繧､繝医ル繝ｳ繧ｰ縲∵ｹ邂｡豐ｻ逋ゅ∝・繧梧ｭｯ縺ｾ縺ｧ蟷・ｺ・￥蟇ｾ蠢懊・謔｣閠・ｧ倥・縺泌ｸ梧悍繧・Λ繧､繝輔せ繧ｿ繧､繝ｫ縺ｫ蜷医ｏ縺帙◆險ｺ逋ゅせ繧ｿ繧､繝ｫ繧貞､ｧ蛻・↓縺励※縺翫ｊ縲√＠縺｣縺九ｊ豐ｻ縺励◆縺・婿縺ｫ縺ｯ菫晞匱蜀・〒繧る聞謖√■縺吶ｋ豐ｻ逋りｨ育判繧偵√・繧､繝ｳ繝域ｲｻ逋ゅ□縺代ｒ縺泌ｸ梧悍縺ｮ譁ｹ縺ｫ縺ｯ遏ｭ譛滄俣縺ｧ螳御ｺ・〒縺阪ｋ繧医≧譟碑ｻ溘↓蟇ｾ蠢懊＠縺ｦ縺・∪縺吶・髯｢蜀・・繝舌Μ繧｢繝輔Μ繝ｼ險ｭ險医〒縲∬ｻ頑､・ｭ舌ｄ繝吶ン繝ｼ繧ｫ繝ｼ繧偵＃蛻ｩ逕ｨ縺ｮ譁ｹ縺ｫ繧る・諷ｮ縺励◆髯｢蜀・腸蠅・〒縺吶ゅく繝・ぜ繧ｹ繝壹・繧ｹ繧ょｮ悟ｙ縺励※縺翫ｊ縲∝ｰ上＆縺ｪ縺雁ｭ先ｧ倬｣繧後・譁ｹ繧ょｮ牙ｿ・＠縺ｦ騾夐劼縺・◆縺縺代∪縺吶・縺ｾ縺溘√・繝ｩ繧､繝舌す繝ｼ縺ｫ驟肴・縺励◆螳悟・蛟句ｮ､縺ｮ險ｺ逋ょｮ､繧・・ｫ伜悸闥ｸ豌玲ｻ・曙蝎ｨ縺ｪ縺ｩ縺ｮ貊・曙讖溷勣繧貞ｰ主・縺励◆蠕ｹ蠎慕噪縺ｪ陦帷函邂｡逅・↑縺ｩ縲∝ｮ牙ｿ・＠縺ｦ豐ｻ逋ゅｒ蜿励￠縺ｦ縺・◆縺縺代ｋ迺ｰ蠅・ｒ謨ｴ縺医※縺・∪縺吶るｧ占ｻ雁ｴ繧・蜿ｰ蛻・ｮ悟ｙ縲・縺雁哨縺ｮ縺頑か縺ｿ縺ｯ縲√●縺ｲ繝溘・繝域ｭｯ遘代∈縺皮嶌隲・￥縺縺輔＞縲・,  // GBP遒ｺ隱肴ｸ医∩
    attributes: [
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懷・繧雁哨',
      '險ｭ蛯・ 繝医う繝ｬ',
      '鬧占ｻ雁ｴ: 謨ｷ蝨ｰ蜀・ｧ占ｻ雁ｴ・育┌譁呻ｼ・,
      '繝励Λ繝ｳ: 莠句燕莠育ｴ・耳螂ｨ'
    ],
    serviceItems: ['陌ｫ豁ｯ豐ｻ逋・, '豁ｯ蜻ｨ逞・ｲｻ逋・, '莠磯亟豁ｯ遘・, '遏ｯ豁｣豁ｯ遘・, '蟆丞・遏ｯ豁｣', '繧､繝ｳ繝励Λ繝ｳ繝・, '繧ｻ繝ｩ繝溘ャ繧ｯ', '繝帙Ρ繧､繝医ル繝ｳ繧ｰ', '譬ｹ邂｡豐ｻ逋・, '蜈･繧梧ｭｯ'],
    menuUrl: null,
    reservationUrl: null
  },
  reviews: {
    totalCount: 21,
    averageRating: 3.5,
    items: [
      { rating: 5, hasReply: false, hasText: true, date: '3騾ｱ髢灘燕' },
      { rating: 1, hasReply: false, hasText: true, date: '1縺区怦蜑・ },
      { rating: 1, hasReply: false, hasText: true, date: '1縺区怦蜑・ },
      { rating: 1, hasReply: false, hasText: true, date: '4縺区怦蜑・ },
      { rating: 1, hasReply: false, hasText: true, date: '7縺区怦蜑・ },
      { rating: 1, hasReply: false, hasText: true, date: '9縺区怦蜑・ },
      { rating: 1, hasReply: false, hasText: true, date: '11縺区怦蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 4, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 3, hasReply: false, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 4, hasReply: false, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '3蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '3蟷ｴ蜑・ },
      { rating: 4, hasReply: false, hasText: true, date: '3蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '3蟷ｴ蜑・ },
      { rating: 3, hasReply: false, hasText: true, date: '4蟷ｴ蜑・ },
      { rating: 2, hasReply: false, hasText: true, date: '4蟷ｴ蜑・ }
    ],
    replyRateNote: '蜈ｨ21莉ｶ荳ｭ縲∬ｿ比ｿ｡0莉ｶ・郁ｿ比ｿ｡邇・%・俄・諢丞峙逧・↓霑比ｿ｡縺励↑縺・婿驥・,
    sentiment: {
      positive: ['遏ｯ豁｣', '菫晞匱', '荳∝ｯｧ', '邯ｺ鮗・, '繧ｭ繝・ぜ繧ｹ繝壹・繧ｹ'],
      negative: ['雋ｻ逕ｨ', '隱ｬ譏惹ｸ崎ｶｳ', '逞帙∩', '諷句ｺｦ', '隧ｰ繧∫黄']
    }
  },
  photos: {
    totalCount: 106,
    categories: {
      exterior: true,
      interior: true,
      menu: true,       // 險ｭ蛯吝・逵溘≠繧・      staff: false      // 繧ｹ繧ｿ繝・ヵ蜀咏悄蟆代↑繧・    },
    hasVideo: false
  },
  posts: {
    totalRecent: 6,       // 譛・謚慕ｨｿ ﾃ・3繝ｶ譛・    latestDate: '2026-03-24',
    recentDates: ['2026-03-24', '2026-03-04', '2026-02-15', '2026-02-01', '2026-01-20', '2026-01-05'],
    gapMonths: 0,
    hasKeywordContent: true,
    hasCasualOnly: false,
    hasEvent: false,
    postTypes: ['譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ']
  },
  competitors: [
    { name: '蟯ｩ逕ｰ豁ｯ遘大現髯｢', category: '豁ｯ遘大現髯｢', rating: 4.0, reviewCount: 50 },
    { name: '螻ｱ譛ｬ豁ｯ遘大現髯｢', category: '豁ｯ遘大現髯｢', rating: 4.3, reviewCount: 41 },
    { name: '縺翫♀縺阪ョ繝ｳ繧ｿ繝ｫ繧ｯ繝ｪ繝九ャ繧ｯ', category: '豁ｯ遘大現髯｢', rating: 4.0, reviewCount: 27 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '豁ｯ遘・鬮倡ょｸ・
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
const baseName = `diagnostic_report_meet_dental_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_meet_dental_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
