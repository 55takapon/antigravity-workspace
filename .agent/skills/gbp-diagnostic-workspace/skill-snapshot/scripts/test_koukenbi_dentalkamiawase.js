/**
 * 蟷ｸ蛛･鄒取ｭｯ遘代け繝ｪ繝九ャ繧ｯ 繝・せ繝医ョ繝ｼ繧ｿ
 * 譛ｭ蟷悟ｸゆｸｭ螟ｮ蛹ｺ 蝎帙∩蜷医ｏ縺帷音蛹悶・閾ｪ雋ｻ險ｺ逋ゅけ繝ｪ繝九ャ繧ｯ
 * 繝・・繧ｿ蜿朱寔譌･: 2026-03-29 繝悶Λ繧ｦ繧ｶ逶ｮ隕也｢ｺ隱肴ｸ医∩
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '蟷ｸ蛛･鄒取ｭｯ遘代け繝ｪ繝九ャ繧ｯ',
    category: '豁ｯ遘大現髯｢',
    address: '縲・64-0821 蛹玲ｵｷ驕捺惆蟷悟ｸゆｸｭ螟ｮ蛹ｺ蛹・譚｡隘ｿ22荳∫岼1-21 繧｢繧ｹ繝代Λ繝繧､繧ｹ繝薙Ν 1F',
    phone: '011-624-6443',
    website: 'koukenbi.com',
    hours: {
      monday: '螳壻ｼ第律',
      tuesday: '10:00縲・3:00, 14:00縲・8:30',
      wednesday: '螳壻ｼ第律',
      thursday: '10:00縲・3:00, 14:00縲・0:00',
      friday: '10:00縲・3:00, 14:00縲・8:30',
      saturday: '10:00縲・5:00',
      sunday: '螳壻ｼ第律'
    },
    description: '譛ｭ蟷悟ｸゅｒ諡轤ｹ縺ｨ縺吶ｋ縲∬ｺｫ菴薙・荳崎ｪｿ繧呈隼蝟・＠縲∵律縲・・繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ繧偵い繝・・縺吶ｋ縲√≠縺斐★繧後・蝎帙∩蜷医ｏ縺幢ｼ磯｡主､我ｽ咲裸豐ｻ逋ゅ・｡守浣豁｣豐ｻ逋ゑｼ牙ｰる摩豁ｯ遘代け繝ｪ繝九ャ繧ｯ縲・譛蟇・ｊ鬧・・縲∝・螻ｱ蜈ｬ蝨帝ｧ・→縲∬･ｿ18荳∫岼鬧・・螟壹￥縺ｮ闡怜錐莠ｺ繧・√せ繝昴・繝・∈謇九ｂ縲∬・蜉帛髄荳翫√ヱ繝輔か繝ｼ繝槭Φ繧ｹ繧｢繝・・繧堤岼逧・↓險ｪ繧後ｋ縲・螟壹￥縺ｮ譁ｹ縺梧ｰ嶺ｻ倥°縺ｪ縺・∵・諤ｧ逧・↑霄ｫ菴薙・荳崎ｪｿ縺ｨ縲・ｼ磯ｭ逞帙・閻ｰ逞帙・ｦ悶％繧翫∬か縺薙ｊ縲・｡朱未遽逞・ｼ峨≠縺斐★繧後∝剱縺ｿ蜷医ｏ縺帙・髢｢菫ゅ・螳溘・・呻ｼ呻ｼ・・譁ｹ縺ｮ縺ゅ＃縺後★繧後※縺・ｋ縲・縺ゅ↑縺溘・縺ゅ＃縺後★繧後※縺・ｋ縺九←縺・°繧定ｨｺ譁ｭ縺励∪縺吶ゅ≠縺斐★繧後∝剱縺ｿ蜷医ｏ縺帷嶌隲・ｒ縺顔筏縺苓ｾｼ縺ｿ縺上□縺輔＞縲よｭ｣縺励＞縺ゅ＃縺ｮ菴咲ｽｮ縺ｫ縺励◆譎ゅ・逞・憾縺ｮ螟牙喧繧剃ｽ馴ｨ薙☆繧九％縺ｨ縺後〒縺阪∪縺吶・縺ゅ＃縺ｮ菴咲ｽｮ繧呈ｭ｣縺励￥縺吶ｋ螟ｧ螟峨ｒ蜿励￠繧九％縺ｨ縺ｧ縲∫樟蝨ｨ縺ｮ逞・憾縺ｮ迸ｬ譎ゅ・螟牙喧繧偵＃閾ｪ蛻・〒諢溘§繧九％縺ｨ縺後〒縺阪∪縺吶・鬘朱未遽逞・・譬ｹ譛ｬ蜴溷屏縺ｮ蜿ｯ閭ｽ諤ｧ繧ゅ≠繧翫∪縺吶る｡朱未遽逞・ｒ郢ｰ繧願ｿ斐＠縺ｦ縺・ｋ譁ｹ繧ゅ√●縺ｲ險ｺ譁ｭ繝ｻ菴馴ｨ薙ｒ縺雁女縺代￥縺縺輔＞縲・,  // GBP隱ｬ譏取枚遒ｺ隱肴ｸ医∩・・85譁・ｭ暦ｼ・    attributes: [
      '豎ｺ貂域婿豕・ 繧ｯ繝ｬ繧ｸ繝・ヨ繧ｫ繝ｼ繝・,
      '繝励Λ繝ｳ: 隕∽ｺ育ｴ・,
      '險ｭ蛯・ 繝医う繝ｬ'
    ],
    serviceItems: [],
    menuUrl: null,
    reservationUrl: null
  },
  reviews: {
    totalCount: 15,
    averageRating: 4.5,
    items: [
      { rating: 1, hasReply: false, hasText: true, date: '3縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '4縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '6縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '7縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '8縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '10縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '11縺区怦蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 2, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: true, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '3蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '3蟷ｴ蜑・ }
    ],
    replyRateNote: '蜈ｨ15莉ｶ遒ｺ隱・ 11/15莉ｶ霑比ｿ｡(73%)縲ら峩霑代・菴手ｩ穂ｾ｡(1笘・縺ｫ譛ｪ霑比ｿ｡',
    sentiment: {
      positive: ['蝎帙∩蜷医ｏ縺・, '蜈ｨ霄ｫ', '鬆ｭ逞帶隼蝟・, '閧ｩ縺薙ｊ', '荳∝ｯｧ', '隱ｬ譏・, '菫｡鬆ｼ'],
      negative: ['鬮倬｡・, '雋ｻ逕ｨ', '閾ｪ雋ｻ']
    }
  },
  photos: {
    totalCount: 20,
    categories: {
      exterior: true,
      interior: true,
      menu: false,       // 譁咎≡陦ｨ/繧ｵ繝ｼ繝薙せ繝｡繝九Η繝ｼ縺ｪ縺・      staff: true        // 蜈育函縺ｮ蜀咏悄縺ゅｊ
    },
    hasVideo: false
  },
  posts: {
    totalRecent: 7,       // 逶ｴ霑・繝ｶ譛・ 1譛・莉ｶ+2譛・莉ｶ+3譛・莉ｶ=7莉ｶ
    latestDate: '2026-03-23',  // 6譌･蜑・    recentDates: ['2026-03-23', '2026-03-16', '2026-03-05', '2026-02-15', '2026-02-01', '2026-01-20', '2026-01-05'],
    gapMonths: 0,
    hasKeywordContent: true,   // 縺ゅ＃縺壹ｌ繝ｻ蝎帙∩蜷医ｏ縺帙・闃ｱ邊臥裸髢｢騾｣險倅ｺ・    hasCasualOnly: false,
    hasEvent: false,
    postTypes: ['譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ']
  },
  competitors: [
    { name: '繧ｯ繝ｪ繝九ャ繧ｯ遏･莠句・鬢ｨ蜑・, category: '遏ｯ豁｣豁ｯ遘・, rating: 4.8, reviewCount: 84 },
    { name: '縺輔▲縺ｽ繧埼ｧ・燕豁ｯ遘代け繝ｪ繝九ャ繧ｯ', category: '豁ｯ遘大現髯｢', rating: 4.8, reviewCount: 57 },
    { name: '荳ｸ螻ｱ豁ｯ遘大現髯｢', category: '豁ｯ遘大現髯｢', rating: 3.6, reviewCount: 14 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '豁ｯ遘大現髯｢ 譛ｭ蟷悟ｸゆｸｭ螟ｮ蛹ｺ'
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
const baseName = `diagnostic_report_koukenbi_dentalkamiawase_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_koukenbi_dentalkamiawase_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
