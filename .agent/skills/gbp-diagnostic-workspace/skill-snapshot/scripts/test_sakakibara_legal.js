/**
 * 讎雁次遞守炊螢ｫ莠句漁謇 繝・せ繝医ョ繝ｼ繧ｿ
 * 蝣ｺ遲区悽逕ｺ 遞守炊螢ｫ
 * 繝・・繧ｿ蜿朱寔譌･: 2026-03-29 繝悶Λ繧ｦ繧ｶ逶ｮ隕也｢ｺ隱肴ｸ医∩
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

const data = {
  basic: {
    name: '讎雁次遞守炊螢ｫ莠句漁謇',
    category: '遞守炊螢ｫ',
    address: '縲・41-0057 螟ｧ髦ｪ蠎懷､ｧ髦ｪ蟶ゆｸｭ螟ｮ蛹ｺ蛹嶺ｹ・ｮ晏ｯｺ逕ｺ1荳∫岼4-15 SC蝣ｺ遲区悽逕ｺ繝薙Ν 503蜿ｷ',
    phone: '06-7777-0714',
    website: 'sakakibara.tkcnf.com',
    hours: {
      monday: '9:00縲・8:00',
      tuesday: '9:00縲・8:00',
      wednesday: '9:00縲・8:00',
      thursday: '9:00縲・8:00',
      friday: '9:00縲・8:00',
      saturday: '螳壻ｼ第律',
      sunday: '螳壻ｼ第律'
    },
    description: '螟ｧ髦ｪ蟶ゆｸｭ螟ｮ蛹ｺ縲∝ｺ遲区悽逕ｺ繝ｻ蛹嶺ｹ・ｮ晏ｯｺ逕ｺ繧ｨ繝ｪ繧｢縺ｮ讎雁次遞守炊螢ｫ莠句漁謇縺ｧ縺吶ょ､ｧ髦ｪ繝ｻ蜈ｵ蠎ｫ繝ｻ莠ｬ驛ｽ繝ｻ螂郁憶繝ｻ蜥梧ｭ悟ｱｱ縺ｪ縺ｩ霑醍柄荳蜀・・荳ｭ蟆丈ｼ∵･ｭ讒倥∈縲∵ｯ取怦縺ｮ險ｪ蝠上ｒ騾壹§縺ｦ鮟貞ｭ玲ｱｺ邂励→雋｡蜍咏ｵ悟霧蜉帙・蠑ｷ蛹悶ｒ蠕ｹ蠎慕噪縺ｫ繧ｵ繝昴・繝医＠縺ｾ縺吶・縲檎ｨ守炊螢ｫ縺悟ｹｴ縺ｫ荳蠎ｦ縺励°譚･縺ｪ縺・阪後ｂ縺｣縺ｨ邨悟霧縺ｮ逶ｸ隲・↓荵励▲縺ｦ縺ｻ縺励＞縲・縺薙・繧医≧縺ｪ縺頑か縺ｿ繧偵♀謖√■縺ｮ邨悟霧閠・ｧ倥・縺懊・蠖謎ｺ句漁謇縺ｫ縺贋ｻｻ縺帙￥縺縺輔＞縲・遘√◆縺｡縺ｯ縲∝腰縺ｪ繧狗筏蜻頑嶌菴懈・縺縺代ｒ陦後≧莨夊ｨ井ｺ句漁謇縺ｧ縺ｯ縺ゅｊ縺ｾ縺帙ｓ縲よｯ取怦雋ｴ遉ｾ縺ｸ縺贋ｼｺ縺・☆繧九悟ｷ｡蝗樒屮譟ｻ縲阪ｒ蝓ｺ譛ｬ縺ｨ縺励∫､ｾ髟ｷ縺ｨ逶ｴ謗･鬘斐ｒ蜷医ｏ縺帙※蟇ｾ隧ｱ縺吶ｋ縺薙→繧呈怙繧ょ､ｧ蛻・↓縺励※縺・∪縺吶よ怙譁ｰ縺ｮ讌ｭ邵ｾ繧貞・縺九ｊ繧・☆縺上＃隱ｬ譏弱＠縲∵ｬ｡縺ｮ荳謇九ｒ蜈ｱ縺ｫ閠・∴繧九∽ｼ∵･ｭ縺ｮ謌宣聞繧呈髪縺医ｋ繝代・繝医リ繝ｼ縺ｧ縺ゅｊ縺溘＞縺ｨ閠・∴縺ｦ縺・∪縺吶・縲仙ｽ謎ｺ句漁謇縺ｮ3縺､縺ｮ蠑ｷ縺ｿ縲・1. 邨悟霧縺ｮ隕九∴繧句喧縺ｨPDCA繧ｵ繧､繧ｯ繝ｫ讒狗ｯ・TKC縺ｮ雋｡蜍吶す繧ｹ繝・Β・・X繧ｷ繝ｪ繝ｼ繧ｺ・牙ｰ主・縺ｫ繧医ｋ縲瑚・險亥喧縲阪ｒ謾ｯ謠ｴ縲らｵ悟霧閠・ｧ倩・霄ｫ縺後Μ繧｢繝ｫ繧ｿ繧､繝縺ｧ讌ｭ邵ｾ繧呈滑謠｡縺励∫噪遒ｺ縺ｪ諢乗晄ｱｺ螳壹′縺ｧ縺阪ｋ菴灘宛繧呈ｧ狗ｯ峨＠縺ｾ縺吶・2. 譛ｪ譚･繧貞卸繧狗ｵ悟霧險育判遲門ｮ・譬ｹ諡縺ｮ縺ゅｋ逶ｮ讓呵ｨｭ螳壹°繧牙ｮ溯｡悟庄閭ｽ縺ｪ繧｢繧ｯ繧ｷ繝ｧ繝ｳ繝励Λ繝ｳ縺ｾ縺ｧ縲∫ｵ悟霧險育判縺ｮ遲門ｮ壹ｒ莨ｴ襍ｰ謾ｯ謠ｴ縲ゆｼ∵･ｭ縺ｮ謖∫ｶ夂噪謌宣聞繧偵し繝昴・繝医＠縺ｾ縺吶・3. 驥題檮讖滄未縺九ｉ縺ｮ菫｡鬆ｼ蠎ｦ蜷台ｸ・縲梧嶌髱｢豺ｻ莉倥阪ｄ縲瑚ｨ伜ｸｳ驕ｩ譎よｧ險ｼ譏取嶌縲阪ｒ遨肴･ｵ逧・↓豢ｻ逕ｨ縺励∵ｱｺ邂玲嶌縺ｮ菫｡鬆ｼ諤ｧ繧帝ｫ倥ａ繧九％縺ｨ縺ｧ縲∝・貊代↑陞崎ｳ・・雉・≡隱ｿ驕斐∈縺ｨ郢九￡縺ｾ縺吶・螟ｧ謇狗ｨ守炊螢ｫ豕穂ｺｺ蠖ｹ蜩｡縺九ｉ迢ｬ遶九＠縺滉ｻ｣陦ｨ遞守炊螢ｫ縺後√後♀螳｢讒倥・螟｢縺悟ｮ溘ｋ縺頑焔莨昴＞繧偵＠縺溘＞縲阪→縺・≧蠑ｷ縺・Φ縺・〒縲∝卸讌ｭ謾ｯ謠ｴ縺九ｉ莠区･ｭ謇ｿ邯吶∫嶌邯壼ｯｾ遲悶∪縺ｧ蟷・ｺ・￥蟇ｾ蠢懊＞縺溘＠縺ｾ縺吶・蝣ｺ遲区悽逕ｺ繝ｻ蛹嶺ｹ・ｮ晏ｯｺ逕ｺ繧偵・縺倥ａ螟ｧ髦ｪ蟶ょ・縺ｧ遞守炊螢ｫ繧偵♀謗｢縺励↑繧峨√●縺ｲ蠖謎ｺ句漁謇縺ｸ縲・邨悟霧縺ｮ縺頑か縺ｿ縲√←繧薙↑莠帷ｴｰ縺ｪ縺薙→縺ｧ繧よｧ九＞縺ｾ縺帙ｓ縲ゅ∪縺壹・縺頑ｰ苓ｻｽ縺ｫ縺雁撫縺・粋繧上○縺上□縺輔＞縲・,  // 繝ｦ繝ｼ繧ｶ繝ｼ謠蝉ｾ帙ユ繧ｭ繧ｹ繝育｢ｺ隱肴ｸ医∩・・16譁・ｭ暦ｼ・    attributes: [
      '繝舌Μ繧｢繝輔Μ繝ｼ: 霆頑､・ｭ仙ｯｾ蠢懊・鬧占ｻ雁ｴ・医↑縺暦ｼ・,
      '繧ｵ繝ｼ繝薙せ繧ｪ繝励す繝ｧ繝ｳ: 螳溷ｺ苓・縺ｮ蝟ｶ讌ｭ',
      '險ｭ蛯・ 繝医う繝ｬ'
    ],
    serviceItems: [],  // 繧ｵ繝ｼ繝薙せ鬆・岼譛ｪ險ｭ螳・    menuUrl: null,
    reservationUrl: null
  },
  reviews: {
    totalCount: 2,
    averageRating: 5.0,
    items: [
      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ },   // 螻ｱ逕ｰ謨丞､ｮ 窶・遒ｺ螳夂筏蜻翫ｄ遞主漁逶ｸ隲・↓縺､縺・※邏莠ｺ縺ｫ繧ょ・縺九ｊ繧・☆縺・      { rating: 5, hasReply: true, hasText: true, date: '1縺区怦蜑・ }    // k s 窶・譏弱ｋ縺丈ｸ∝ｯｧ縺ｪ蟇ｾ蠢懊〒髱槫ｸｸ縺ｫ菫｡鬆ｼ縺ｧ縺阪ｋ繝代・繝医リ繝ｼ
    ],
    replyRateNote: '蜈ｨ2莉ｶ遒ｺ隱・ 2/2莉ｶ=100%霑比ｿ｡',
    sentiment: {
      positive: ['蛻・°繧翫ｄ縺吶＞', '荳∝ｯｧ', '菫｡鬆ｼ', '繧｢繝峨ヰ繧､繧ｹ', '繝代・繝医リ繝ｼ'],
      negative: []
    }
  },
  photos: {
    totalCount: 4,
    categories: {
      exterior: true,    // 繝薙Ν螟冶ｦｳ1譫・      interior: true,    // 蜿嶺ｻ倥・繧ｿ繝悶Ξ繝・ヨ1譫・      menu: false,       // 繧ｵ繝ｼ繝薙せ繝｡繝九Η繝ｼ/譁咎≡陦ｨ縺ｪ縺・      staff: false       // 莉｣陦ｨ繝ｻ繧ｹ繧ｿ繝・ヵ蜀咏悄縺ｪ縺・    },
    hasVideo: false
  },
  posts: {
    totalRecent: 4,       // 逶ｴ霑・繝ｶ譛医〒4莉ｶ
    latestDate: '2026-03-10',  // 19譌･蜑・    recentDates: ['2026-03-10', '2026-03-05', '2026-02-02', '2026-01-27'],
    gapMonths: 0,
    hasKeywordContent: true,  // 縲檎嶌邯壹阪梧怦谺｡隧ｦ邂苓｡ｨ縲阪悟ｷ｡蝗樒屮譟ｻ縲阪檎ｵ悟霧縲咲ｭ峨く繝ｼ繝ｯ繝ｼ繝牙性繧
    hasCasualOnly: false,
    hasEvent: false,
    postTypes: ['譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ', '譛譁ｰ諠・ｱ']
  },
  competitors: [
    { name: '遞守炊螢ｫ豕穂ｺｺ譚ｾ譛ｬ 螟ｧ髦ｪ繧ｪ繝輔ぅ繧ｹ', category: '遞守炊螢ｫ', rating: 5.0, reviewCount: 201 },
    { name: '蟾晄搗莨夊ｨ井ｺ句漁謇', category: '遞守炊螢ｫ', rating: 5.0, reviewCount: 44 },
    { name: '豬ｦ驥惹ｼ夊ｨ井ｺ句漁謇', category: '遞守炊螢ｫ', rating: 4.5, reviewCount: 25 },
    { name: '蝣ｺ遲区悽逕ｺ豕募ｾ倶ｼ夊ｨ井ｺ句漁謇', category: '遞守炊螢ｫ', rating: 3.0, reviewCount: 2 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    source: 'Google Maps (browser) 窶・逶ｮ隕也｢ｺ隱肴ｸ医∩',
    searchQuery: '遞守炊螢ｫ 蝣ｺ遲区悽逕ｺ'
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
const baseName = `diagnostic_report_sakakibara_legal_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n笨・HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`笨・NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_sakakibara_legal_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`笨・繝・・繧ｿ: ${jsonPath}`);
