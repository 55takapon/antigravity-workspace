/**
 * 縺九∪縺豁ｯ遘大現髯｢ 繝・せ繝医ョ繝ｼ繧ｿ
 * 鬮倡ょｸ・豁ｯ遘大現髯｢
 * 繝・・繧ｿ蜿朱寔譌･: 2026-03-28 逶ｮ隕也｢ｺ隱肴ｸ医∩
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '縺九∪縺豁ｯ遘大現髯｢',
    category: '豁ｯ遘大現髯｢',
    address: '縲・76-0021 蜈ｵ蠎ｫ逵碁ｫ倡ょｸるｫ倡ら伴譛晄律逕ｺ2荳∫岼15-6',
    phone: '079-442-4082',
    website: 'kamada-d.com',
    hours: {
      monday: '9:00縲・2:00, 14:00縲・8:30',
      tuesday: '9:00縲・2:00, 14:00縲・9:00',
      wednesday: '螳壻ｼ第律',
      thursday: '9:00縲・2:00, 14:00縲・8:30',
      friday: '9:00縲・2:00, 14:00縲・8:30',
      saturday: '9:00縲・3:00',
      sunday: '螳壻ｼ第律'
    },
    description: '鬮倡るｧ・°繧峨⊇縺ｩ霑代＞鬮倡ょｸゅ・縲悟現逋よｳ穂ｺｺ遉ｾ蝗｣ 縺九∪縺・磯詞逕ｰ・画ｭｯ遘大現髯｢縲阪・縲∝慍蝓溘↓譬ｹ蟾ｮ縺励◆豁ｯ遘大現髯｢縺ｧ縺吶よｭｯ縺ｮ螟ｧ蛻・＆繧堤衍縺｣縺ｦ縺・◆縺縺阪∝▼蠎ｷ縺ｪ逕滓ｴｻ繧帝√ｌ繧九ｈ縺・悟ｮ牙ｿ・〒縺阪ｋ貂・ｽ斐↑豐ｻ逋らｩｺ髢薙阪〒險ｺ逋ゅｒ陦後▲縺ｦ縺・∪縺吶ゅｏ縺九ｊ繧・☆縺・ｪｬ譏弱ｒ蠢・′縺代∫ｴ榊ｾ励＞縺溘□縺代ｋ豐ｻ逋らｵ先棡繧堤岼謖・☆縺薙→繧貞､ｧ蛻・↓縺励※縺・∪縺吶り勠豁ｯ繧・ｭｯ蜻ｨ逞・∫衍隕夐℃謨上∝剱縺ｿ蜷医ｏ縺帙・荳崎ｪｿ縺ｪ縺ｩ蟷・ｺ・＞縺頑か縺ｿ縺ｫ蟇ｾ蠢懊＠縲∝ｰ丞・豁ｯ遘代〒縺ｯ縺雁ｭ舌＆縺ｾ縺悟ｮ牙ｿ・＠縺ｦ騾壹∴繧句ｷ･螟ｫ繧貞叙繧雁・繧後※縺・∪縺吶よ・莠ｺ縺ｮ譁ｹ縺ｫ縺ｯ螳壽悄讀懆ｨｺ繧・け繝ｪ繝ｼ繝九Φ繧ｰ繧帝壹§縺ｦ莠磯亟豁ｯ遘代↓蜉帙ｒ蜈･繧後∫函豢ｻ鄙呈・縺ｫ蜷医ｏ縺帙◆繧｢繝峨ヰ繧､繧ｹ繧り｡後＞縺ｾ縺吶ゅ＆繧峨↓蜈･繧梧ｭｯ繧・°縺ｶ縺帷黄縺ｪ縺ｩ縺ｮ豐ｻ逋ゅｄ縲∵ｭｯ荳ｦ縺ｳ繧・ｦ九◆逶ｮ繧呈紛縺医ｋ蟇ｩ鄒取ｭｯ遘代↓繧ょｯｾ蠢懊＠縲∫ｷ丞粋逧・↓繧ｵ繝昴・繝医＞縺溘＠縺ｾ縺吶るｫ倡ょｸゅｄ鬮倡るｧ・捉霎ｺ縺ｧ豁ｯ遘代ｒ縺頑爾縺励・譁ｹ縺ｫ縺ｨ縺｣縺ｦ縲・壹＞繧・☆縺上Μ繝ｩ繝・け繧ｹ縺ｧ縺阪ｋ豁ｯ蛹ｻ閠・〒縺ゅｋ縺薙→繧貞ｿ・′縺代※縺・∪縺吶よｲｻ逋ょｾ後ｂ蜀咲匱髦ｲ豁｢縺ｫ蜷代￠縺溘そ繝ｫ繝輔こ繧｢謖・ｰ弱ｒ蠕ｹ蠎輔＠縲√碁ｫ倡ょｸゅ〒驕ｸ縺ｰ繧後ｋ縺九°繧翫▽縺第ｭｯ蛹ｻ閠・阪→縺励※逧・＆縺ｾ縺ｮ縺雁哨縺ｮ蛛･蠎ｷ繧呈髪縺医∪縺吶ゅ←縺・◇縺頑ｰ苓ｻｽ縺ｫ縺皮嶌隲・￥縺縺輔＞縲・,  // Google讀懃ｴ｢邨先棡縺ｧ遒ｺ隱肴ｸ医∩
    attributes: [
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・蜈･繧雁哨',
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・鬧占ｻ雁ｴ',
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・蠎ｧ蟶ｭ',
      '繧ｵ繝ｼ繝薙せ: 蟆丞・豁ｯ遘・,
      '繧ｵ繝ｼ繝薙せ: 鄒主ｮｹ豁ｯ遘・,
      '繧ｵ繝ｼ繝薙せ: 辟｡逞帶ｭｯ遘第ｲｻ逋・,
      '險ｭ蛯・ 繝医う繝ｬ',
      '險ｭ蛯・ 逕ｷ螂ｳ蜈ｱ逕ｨ繝医う繝ｬ',
      '螳｢螻､: LGBTQ繝輔Ξ繝ｳ繝峨Μ繝ｼ',
      '螳｢螻､: 繝医Λ繝ｳ繧ｹ繧ｸ繧ｧ繝ｳ繝繝ｼ蟇ｾ蠢・,
      '繝励Λ繝ｳ: 莠句燕莠育ｴ・′縺翫☆縺吶ａ',
      '豎ｺ貂域婿豕・ au PAY・域悴蟇ｾ蠢懆｡ｨ險假ｼ・,
      '豎ｺ貂域婿豕・ d謇輔＞・域悴蟇ｾ蠢懆｡ｨ險假ｼ・,
      '豎ｺ貂域婿豕・ PayPay・域悴蟇ｾ蠢懆｡ｨ險假ｼ・,
      '豎ｺ貂域婿豕・ V繝槭ロ繝ｼ・域悴蟇ｾ蠢懆｡ｨ險假ｼ・,
      '豎ｺ貂域婿豕・ 讌ｽ螟ｩ繝壹う・域悴蟇ｾ蠢懆｡ｨ險假ｼ・,
      '豎ｺ貂域婿豕・ 莠､騾夂ｳｻIC繧ｫ繝ｼ繝会ｼ域悴蟇ｾ蠢懆｡ｨ險假ｼ・,
      '鬧占ｻ雁ｴ: 謨ｷ蝨ｰ蜀・ｧ占ｻ雁ｴ',
      '鬧占ｻ雁ｴ: 辟｡譁吶・霍ｯ荳企ｧ占ｻ雁ｴ'
    ],
    serviceItems: ['蟆丞・豁ｯ遘・, '鄒主ｮｹ豁ｯ遘・, '辟｡逞帶ｭｯ遘第ｲｻ逋・],
    menuUrl: null,
    reservationUrl: null
  },
  reviews: {
    totalCount: 29,
    averageRating: 3.9,
    // 譛譁ｰ鬆・・蜈ｨ莉ｶ遒ｺ隱・ 6/29莉ｶ縺ｫ霑比ｿ｡縺ゅｊ
    // 3繝ｶ譛井ｻ･蜀・・100%霑比ｿ｡・・/6莉ｶ・峨√◎繧御ｻ･蜑阪・0%
    items: [
      { rating: 5, hasReply: true, hasText: true, date: '2騾ｱ髢灘燕' },   // 縺ゅ♀繧翫ｓ縺・      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },   // koh golden
      { rating: 5, hasReply: true, hasText: true, date: '2縺区怦蜑・ },   // tmhr kskb
      { rating: 5, hasReply: true, hasText: true, date: '2縺区怦蜑・ },   // 縺薙∪
      { rating: 5, hasReply: true, hasText: true, date: '3縺区怦蜑・ },   // 逡題恭逅・      { rating: 5, hasReply: true, hasText: true, date: '3縺区怦蜑・ },   // 23KA7234
      { rating: 5, hasReply: false, hasText: true, date: '6縺区怦蜑・ },  // 縺九★縺励＜
      { rating: 5, hasReply: false, hasText: true, date: '9縺区怦蜑・ },
      { rating: 1, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 1, hasReply: false, hasText: true, date: '1蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: true, date: '2蟷ｴ蜑・ },
      { rating: 5, hasReply: false, hasText: false, date: '3蟷ｴ蜑・ }
    ],
    replyRateNote: '蜈ｨ29莉ｶ遒ｺ隱・ 逶ｴ霑・繝ｶ譛・/6莉ｶ=100%霑比ｿ｡縲√◎繧御ｻ･蜑阪・0%縲ょ・菴・/29莉ｶ(21%)縺ｯ蜿り・､',
    sentiment: {
      positive: ['荳∝ｯｧ', '蜈育函', '隱ｬ譏・, '繧ｹ繧ｿ繝・ヵ', '螳牙ｿ・, '貂・ｽ・, '繧､繝ｳ繝励Λ繝ｳ繝・, '莠磯亟'],
      negative: ['蠕・■譎る俣', '蟇ｾ蠢・]
    }
  },
  photos: {
    totalCount: 8,    // 繧ｪ繝ｼ繝翫・謠蝉ｾ・繝ｦ繝ｼ繧ｶ繝ｼ謚慕ｨｿ蜷ｫ繧
    categories: {
      exterior: true,    // 螟冶ｦｳ蜀咏悄縺ゅｊ・医せ繧ｯ繝ｪ繝ｼ繝ｳ繧ｷ繝ｧ繝・ヨ遒ｺ隱肴ｸ医∩・・      interior: true,    // 蜿嶺ｻ倥・蠕・粋螳､繝ｻ險ｺ蟇溷ｮ､縺ゅｊ
      menu: false,       // 譁咎≡陦ｨ/繝｡繝九Η繝ｼ蜀咏悄縺ｪ縺・      staff: false       // 繧ｹ繧ｿ繝・ヵ蜀咏悄縺ｪ縺・    },
    hasVideo: false
  },
  posts: {
    // 譛・-2蝗槭・螳牙ｮ壽兜遞ｿ縲よｭｯ遘代く繝ｼ繝ｯ繝ｼ繝牙性繧蝠楢貯險倅ｺ九≠繧翫・    totalRecent: 5,       // 逶ｴ霑・繝ｶ譛育ｴ・莉ｶ
    latestDate: '2026-03-24',  // 4譌･蜑・    recentDates: ['2026-03-24', '2026-03-01', '2026-02-15', '2026-02-01', '2026-01-15'],
    gapMonths: 0,         // 邯咏ｶ夂噪縺ｪ謚慕ｨｿ縺ゅｊ
    hasKeywordContent: true,  // 縲梧ｭｯ蜻ｨ逞・阪悟哨閻斐こ繧｢縲阪後ラ繝ｩ繧､繝槭え繧ｹ縲咲ｭ峨く繝ｼ繝ｯ繝ｼ繝牙性繧
    hasCasualOnly: false,
    hasEvent: false,
    postTypes: ['譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ']
  },
  competitors: [
    { name: '螻ｱ譛ｬ豁ｯ遘大現髯｢', category: '豁ｯ遘大現髯｢', rating: 4.3, reviewCount: 41 },
    { name: 'MV螳晄ｮｿ豁ｯ遘・, category: '豁ｯ遘大現髯｢', rating: 3.3, reviewCount: 31 },
    { name: '蟯ｩ逕ｰ豁ｯ遘大現髯｢', category: '豁ｯ遘大現髯｢', rating: 4.0, reviewCount: 50 },
    { name: '阯､莠墓ｭｯ遘大現髯｢', category: '豁ｯ遘大現髯｢', rating: 4.0, reviewCount: 6 },
    { name: '阯､蜴滓ｭｯ遘大現髯｢', category: '豁ｯ遘大現髯｢', rating: 3.6, reviewCount: 24 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '豁ｯ遘大現髯｢ 鬮倡ょｸ・
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
const baseName = `diagnostic_report_kamada_dental_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_kamada_dental_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(result, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
