/**
 * 芝本司法書士事務所 GBP診断テスト
 * 診断日: 2026-03-30
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

// === 収集データ ===
const data = {
  basic: {
    name: '芝本司法書士事務所',
    category: '司法書士',
    subCategories: [],
    address: '〒675-0054 兵庫県加古川市米田町平津663番地の20',
    phone: '079-455-7889',
    website: 'https://peraichi.com/landing_pages/view/t1eqp',
    hours: {
      '月曜日': '9:00～17:00',
      '火曜日': '9:00～17:00',
      '水曜日': '9:00～17:00',
      '木曜日': '9:00～17:00',
      '金曜日': '9:00～17:00',
      '土曜日': '定休日',
      '日曜日': '定休日'
    },
    description: '【加古川市で相続・成年後見・不動産名義変更なら芝本司法書士事務所へ】 相続手続きや成年後見、不動産の名義変更など、何から手をつければいいかお悩みではありませんか？ 兵庫県加古川市の芝本司法書士事務所では、相続・成年後見・不動産名義変更を中心に、司法書士業務全般を幅広く承っております。 相続手続きは、遺産分割協議書の作成から相続登記まで、複雑な手続きをトータルでサポートいたします。はじめての方でも安心してご相談いただけるよう、わかりやすい言葉で丁寧にご説明いたします。 成年後見については、認知症・知的障がい・精神障がいなどにより判断能力が不十分な方の財産管理・身上保護を支援します。法定後見・任意後見どちらにも対応しており、ご本人とご家族が安心して暮らせるよう寄り添ってまいります。 不動産の名義変更は、売買・贈与・離婚による財産分与などあらゆるケースに対応。迅速かつ正確に手続きを進めます。 その他、会社設立・商業登記・抵当権抹消・債務整理など、どんな小さなことでもお気軽にご相談ください。 加古川市・姫路市・明石市・高砂市を中心に兵庫県全域からのご依頼を承っております。',
    attributes: [
      '車椅子対応の入口: なし',
      '敷地内駐車場: あり',
      '無料駐車場: あり'
    ],
    services: []
  },
  reviews: {
    totalCount: 1,
    averageRating: 5.0,
    items: [
      {
        rating: 5,
        text: '',
        date: '1年前',
        hasOwnerReply: false,
        hasText: false
      }
    ]
  },
  photos: {
    totalCount: 7,
    hasExterior: true,
    hasInterior: true,
    hasFood: true,  // サービス案内看板はサービス写真として扱う
    hasStaff: false
  },
  posts: {
    latestPostDate: '2026-03-25',  // 5日前
    recentCount: 2,  // 直近3ヶ月で2件
    hasOffer: false,
    hasEvent: false,
    hasKeywordContent: true  // 相続登記・抵当権抹消という業種キーワード含む投稿あり
  },
  competitors: [
    { name: '司法書士かたひら法務事務所', rating: 5.0, reviewCount: 4 },
    { name: 'まつい司法書士事務所', rating: 5.0, reviewCount: 2 },
    { name: '大西雅明司法書士事務所', rating: 0, reviewCount: 0 },
    { name: '司法書士 鹿間事務所', rating: 1.0, reviewCount: 1 },
    { name: '司法書士・行政書士丸山雅史事務所', rating: 5.0, reviewCount: 6 },
    { name: '司法書士宮本秀晃事務所', rating: 4.7, reviewCount: 3 },
    { name: '高峰司法書士事務所', rating: 3.0, reviewCount: 2 }
  ]
};

// === 分析実行 ===
const result = analyzeGBP(data);

// === コンソール出力 ===
console.log('='.repeat(60));
console.log(`📊 ${result.businessName} GBP診断結果`);
console.log('='.repeat(60));
console.log(`業種判定: ${result.industry.label}`);
console.log(`総合スコア: ${result.totalScore}/100 → ${result.totalRank.rank}ランク（${result.totalRank.label}）`);
console.log('');

console.log('--- 5軸スコア ---');
for (const a of result.axes) {
  console.log(`  ${a.rank.rank} ${a.label}: ${a.score}点`);
  if (a.details.length > 0) {
    for (const d of a.details) {
      console.log(`    ⚠ ${d}`);
    }
  }
}
console.log('');

console.log('--- 伸びしろ TOP3 ---');
const medals = ['🥇', '🥈', '🥉'];
for (let i = 0; i < result.top3.length; i++) {
  const item = result.top3[i];
  console.log(`${medals[i]} ${item.improvement.summary}`);
  console.log(`   現在: ${item.currentRank}ランク（${item.currentScore}点）`);
  console.log(`   方向性: ${item.improvement.action}`);
  console.log('');
}

console.log('--- 競合比較 ---');
console.log(`★ ${result.businessName}: ${data.reviews.averageRating}★ / ${data.reviews.totalCount}件`);
for (const c of data.competitors) {
  console.log(`  ${c.name}: ${c.rating || '-'}★ / ${c.reviewCount}件`);
}

// === ファイル出力（命名規則: diagnostic_report_{name}_{YYYYMMDD}）===
// JST固定で日付生成（UTC+9）— toISOString()はUTCのため日本時間とズレる
const now = new Date();
const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const dateStr = jst.toISOString().slice(0, 10).replace(/-/g, '');
const baseName = `diagnostic_report_shibamoto_legal_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n✅ HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`✅ NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_shibamoto_legal_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`✅ データ: ${jsonPath}`);
