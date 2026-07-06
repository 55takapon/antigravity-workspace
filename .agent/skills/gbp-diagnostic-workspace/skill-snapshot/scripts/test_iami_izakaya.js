/**
 * iami テスト実行用データ
 * ブラウザで手動収集したデータに基づくスコアリング＋レポート生成
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

// ブラウザ収集データ
const data = {
  basic: {
    name: 'iami (アイアムアイ)',
    category: '居酒屋',
    subCategories: [],
    address: '〒675-0038 兵庫県加古川市加古川町木村65 やかたビル 東3C',
    phone: '079-490-4425',
    website: 'http://iamikakogawa.com/',
    hours: {
      '月': '18:00–翌0:00',
      '火': '18:00–翌0:00',
      '水': '18:00–翌0:00',
      '木': '18:00–翌0:00',
      '金': '18:00–翌0:00',
      '土': '18:00–翌0:00',
      '日': '定休日'
    },
    description: '加古川でおいしい居酒屋やキッチンバーをお探しなら「iamiアイアムアイ加古川」へ。 国産ぷりぷりもつを使った名物もつ鍋をはじめ、震度5でも崩れないと評されるだし巻きたまご、特製マヨソースのエビマヨ、赤ワインソースで仕上げる手作りハンバーグなど、手間を惜しまないこだわり料理が揃うくつろぎキッチンバーです。 日本酒にも強く、加古川の地酒「盛典」を中心に、季節の限定酒や全国の銘酒を多数ラインナップ。ビール・サワー・ハイボールはもちろん、スペシャルティコーヒー豆「モカへレフ」を使ったアイリッシュコーヒーなど、飲めない方でも楽しめるドリンクも豊富です。 店内はカウンター中心の落ち着いた空間で、お一人様の晩酌、デート、友人との食事にも最適。飲み放題付きコースは5,000円〜と宴会や歓送迎会に使いやすく、貸し切り相談やオードブル注文にも対応。 JR加古川駅から徒歩15分、駐車場1台あり。雨の日はファーストドリンク半額クーポンをご用意。 こだわり料理と地酒をくつろぎの空間で楽しみたい方は、ぜひ当店へ。', // Google検索で確認。Googleマップブラウザ版では投稿に隠れて非表示
    attributes: [
      // サービスオプション
      'イートイン', '店先受取可', '宅配', 'テイクアウト',
      // サービス
      'アルコール飲料', 'ビール', 'ワイン', '小皿料理',
      // 特徴
      '飲み放題',
      // 設備
      'Wi-Fi', '無料Wi-Fiあり', 'トイレ', '禁煙', '男女共用トイレ',
      // 雰囲気
      'カジュアル', '落ち着く'
    ],
    services: [
      'ランチ', 'ディナー', 'デザート', '座席があるお店', 'テーブルサービス'
    ]
  },
  reviews: {
    totalCount: 31,
    averageRating: 4.6,
    items: [
      { rating: 5, hasReply: true, hasText: false, date: '3週間前' },
      { rating: 5, hasReply: true, hasText: true, date: '1か月前' },
      { rating: 5, hasReply: true, hasText: true, date: '1年前' },
      { rating: 5, hasReply: false, hasText: true, date: '2年前' },
      { rating: 5, hasReply: false, hasText: true, date: '2年前' },
      { rating: 5, hasReply: false, hasText: true, date: '3年前' },
      { rating: 5, hasReply: true, hasText: true, date: '3年前' },
      { rating: 5, hasReply: false, hasText: false, date: '3年前' },
      { rating: 5, hasReply: false, hasText: true, date: '2年前' },
      { rating: 5, hasReply: false, hasText: true, date: '3年前' },
      { rating: 5, hasReply: false, hasText: true, date: '3年前' },
      { rating: 5, hasReply: false, hasText: true, date: '2年前' },
      { rating: 5, hasReply: false, hasText: false, date: '3年前' },
      { rating: 5, hasReply: false, hasText: false, date: '3年前' },
      { rating: 4, hasReply: false, hasText: false, date: '2年前' }
    ]
  },
  photos: {
    totalCount: 50,
    categories: ['すべて', '料理', '雰囲気', 'メニュー'],
    hasExterior: false,
    hasInterior: true,
    hasFood: true,
    hasStaff: false
  },
  posts: {
    totalRecent: 3,
    latestDate: '2026-03-19',
    recentDates: ['2026-03-19', '2026-03-12', '2026-03-05'],
    gapMonths: 0,
    hasKeywordContent: true,
    hasCasualOnly: false,
    hasEvent: true,
    postTypes: ['最新情報', '最新情報', '最新情報']
  },
  competitors: [
    { name: 'ほっこり串焼酒場 あし跡', category: '居酒屋', rating: 4.3, reviewCount: 127 },
    { name: '源べえ', category: '居酒屋', rating: 4.3, reviewCount: 413 },
    { name: 'ととや', category: '居酒屋', rating: 4.1, reviewCount: 94 },
    { name: '元祖五感スパイス焼鳥 とりDEビアーとりこ店', category: '居酒屋', rating: 4.7, reviewCount: 48 },
    { name: '燦縁～さんえん～', category: '居酒屋', rating: 4.5, reviewCount: 11 }
  ],
  meta: {
    scrapedAt: new Date().toISOString(),
    sourceUrl: 'https://maps.app.goo.gl/7jwtHLUZhGsBGQcKA'
  }
};

// 分析実行
const result = analyzeGBP(data);

console.log('=== スコアリング結果 ===');
console.log(`ビジネス名: ${result.businessName}`);
console.log(`業種判定: ${result.industry.label}`);
console.log(`総合スコア: ${result.totalRank.rank} (${result.totalScore}/100)\n`);
console.log('5軸スコア:');
for (const axis of result.axes) {
  console.log(`  ${axis.rank.rank} ${axis.label}: ${axis.score}点`);
}
console.log('\n伸びしろTOP3:');
for (const item of result.top3) {
  console.log(`  ${item.rank}. ${item.improvement.summary}`);
}

// レポート生成
const outputDir = path.join(__dirname, '..');
// JST固定で日付生成（UTC+9）
const now = new Date();
const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const timestamp = jst.toISOString().slice(0, 10).replace(/-/g, '');

const html = generateHTML(result, data);
const htmlFile = path.join(outputDir, `diagnostic_report_iami_izakaya_${timestamp}.html`);
fs.writeFileSync(htmlFile, html, 'utf-8');
console.log(`\n✅ HTML: ${htmlFile}`);

const notebook = generateNotebookText(result, data);
const notebookFile = path.join(outputDir, `diagnostic_report_iami_izakaya_${timestamp}_notebook.txt`);
fs.writeFileSync(notebookFile, notebook, 'utf-8');
console.log(`✅ NotebookLM: ${notebookFile}`);

const jsonFile = path.join(outputDir, `diagnostic_data_iami_izakaya_${timestamp}.json`);
fs.writeFileSync(jsonFile, JSON.stringify(result, null, 2), 'utf-8');
console.log(`✅ データ: ${jsonFile}`);
