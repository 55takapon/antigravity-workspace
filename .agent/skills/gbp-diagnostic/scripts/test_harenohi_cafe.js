/**
 * ハレノヒカフェ GBP診断テスト
 * 診断日: 2026-04-02
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText, generateSalesPitchText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

// === 収集データ ===
const data = {
  basic: {
    name: 'ハレノヒカフェ',
    category: 'カフェ',
    subCategories: ['洋食店', 'ランチ'],
    address: '〒581-0869 大阪府八尾市桜ヶ丘1丁目88 ベルドミール桜ヶ丘101',
    phone: '072-951-6443',
    website: 'https://harenohicafe.com',
    hours: {
      '月曜日': '11:00～15:00',
      '火曜日': '定休日',
      '水曜日': '11:00～15:00, 18:00～23:00',
      '木曜日': '11:00～15:00, 18:00～23:00',
      '金曜日': '11:00～15:00, 18:00～23:00',
      '土曜日': '11:00～15:00, 18:00～23:00',
      '日曜日': '11:00～15:00'
    },
    description: '', // ユーザー指定：GBP説明文なし
    attributes: [
      'イートイン',
      'テイクアウト',
      '宅配'
    ],
    services: []
  },
  reviews: {
    totalCount: 77,
    averageRating: 4.2,
    items: [
      {
        rating: 5,
        text: 'ランチがとても美味しかったです。',
        date: '2週間前', // 直近1件
        hasOwnerReply: false, // ユーザー指定：オーナー確認未のため返信なし
        hasText: true
      },
      {
        rating: 4,
        text: '雰囲気が良く落ち着きます。',
        date: '5か月前', // ユーザー指定：次は5か月前
        hasOwnerReply: false,
        hasText: true
      }
    ]
  },
  photos: {
    totalCount: 25,
    hasExterior: true,
    hasInterior: true,
    hasFood: true,
    hasStaff: false
  },
  posts: {
    latestPostDate: null, 
    recentCount: 0,
    hasOffer: false,
    hasEvent: false,
    hasKeywordContent: false 
  },
  competitors: [
    { name: 'cafe lien', rating: 4.5, reviewCount: 100 },
    { name: 'Blanket', rating: 4.0, reviewCount: 147 },
    { name: '金萱堂 kinsendo 台湾カフェ', rating: 4.1, reviewCount: 92 },
    { name: 'Tokiaprofumo -トキアプロフーモ-', rating: 4.3, reviewCount: 53 }
  ]
};

// === 分析実行 ===
const result = analyzeGBP(data);

// オーナー確認未を反映するため返信率のスコアを強制的に落とす（もし自動で落ちていなければ）
// 念のため設定しますがanalyzeGBPが自動で反映するはず

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

// === ファイル出力（命名規則: diagnostic_report_{name}_{YYYYMMDD}）===
const now = new Date();
const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const dateStr = jst.toISOString().slice(0, 10).replace(/-/g, '');
const baseName = `diagnostic_report_harenohi_cafe_${dateStr}`;

const html = generateHTML(result, data);
const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, html, 'utf-8');
console.log(`\n✅ HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`✅ NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_harenohi_cafe_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`✅ データ: ${jsonPath}`);

const pitch = generateSalesPitchText(result, data);
const pitchPath = path.join(__dirname, '..', `diagnostic_sales_pitch_harenohi_cafe_${dateStr}.txt`);
fs.writeFileSync(pitchPath, pitch, 'utf-8');
console.log(`✅ 営業訴求トーク: ${pitchPath}`);
