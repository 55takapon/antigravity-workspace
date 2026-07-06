/**
 * 個別指導WAM 久宝寺校 GBP診断テスト
 * 診断日: 2026-04-02
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText, generateSalesPitchText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

// === 収集データ ===
const data = {
  basic: {
    name: '個別指導WAM 久宝寺校',
    category: '受験予備校',
    subCategories: ['学習塾', '個別指導塾'],
    address: '〒581-0063 大阪府八尾市太子堂2丁目1-46 八光第一ビル',
    phone: '072-924-8080',
    website: 'https://k-wam.jp',
    hours: {
      '月曜日': '16:00～21:30',
      '火曜日': '16:00～21:30',
      '水曜日': '16:00～21:30',
      '木曜日': '16:00～21:30',
      '金曜日': '16:00～21:30',
      '土曜日': '定休日',
      '日曜日': '定休日'
    },
    // ユーザー指定：説明文あり、しかし規約違反のハッシュタグ含む
    description: 'みなさん！こんにちは！ 個別指導WAM 久宝寺校の柴藤です！ お子様が家で全く勉強をしない、 学校の成績が下がってきたなど保護者様は様々な悩みを抱えておられます。 面談ではお子様の勉強に対する悩みをお聞きしし、 解決させていただく場でもあります。 個別指導WAM 久宝寺校では一人ひとりに親身なアドバイスでお子様の夢や目標の実現のために、全力で向き合っていきます。 体験授業・勉強相談（無料）を実施していますので、 個別指導WAMにぜひ一度電話・メールなどでお問い合わせください。 皆様にお会いできる日を心よりお待ちしております。 #Wam #wam #ワム #亀井 #竹渕 #龍華 #久宝寺 #小 #中 #高 #中学受験 #高校受験 #大学受験 #入試 #私立 #公立 #英検 #漢検 #定期テスト #定期試験 #定テ',
    attributes: [
      'オンライン授業'
    ],
    services: []
  },
  reviews: {
    totalCount: 2,
    averageRating: 3.0,
    items: [
      {
        rating: 3,
        text: '普通の塾でした。',
        date: '1年前', 
        hasOwnerReply: false,
        hasText: true
      },
      {
        rating: 3,
        text: '',
        date: '2年前',
        hasOwnerReply: false,
        hasText: false
      }
    ]
  },
  photos: {
    totalCount: 9,
    hasExterior: true,
    hasInterior: true,
    hasFood: false,
    hasStaff: true
  },
  posts: {
    latestPostDate: '2025-04-01', // 最新投稿は1年前
    recentCount: 0, // 直近3ヶ月は0
    hasOffer: false,
    hasEvent: false,
    hasKeywordContent: false 
  },
  competitors: [
    { name: '森塾 近鉄八尾校', rating: 4.6, reviewCount: 15 },
    { name: 'ITTO個別指導学院 八尾宮町校', rating: 4.5, reviewCount: 11 },
    { name: '永田塾', rating: 5.0, reviewCount: 8 },
    { name: '創研学院 久宝寺校', rating: 2.2, reviewCount: 5 }
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

// === ファイル出力（命名規則: diagnostic_report_{name}_{YYYYMMDD}）===
const now = new Date();
const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
const dateStr = jst.toISOString().slice(0, 10).replace(/-/g, '');
const baseName = `diagnostic_report_wam_kyuhoji_${dateStr}`;

const html = generateHTML(result, data);

// ハッシュタグ問題を手動でHTMLに差し込む（analyze_gbpが対応していない場合のため）
const htmlWithHashtagWarning = html.replace(/<section id="opportunity">/g, '<section id="opportunity"><div class="alert" style="background:#fff3cd; color:#856404; padding:15px; margin-bottom:20px; border-left:5px solid #ffeeba; border-radius:4px;"><strong>🚨 コンプライアンス警告:</strong> Googleビジネスプロフィールの説明文にハッシュタグ（#）が含まれています。これはGoogleのガイドライン違反（キーワードの詰め込み）に該当し、アカウント停止リスクがあるため、早急な削除・修正を強く推奨します。</div>');

const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, htmlWithHashtagWarning, 'utf-8');
console.log(`\n✅ HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`✅ NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_wam_kyuhoji_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`✅ データ: ${jsonPath}`);

const pitch = generateSalesPitchText(result, data);
const pitchPath = path.join(__dirname, '..', `diagnostic_sales_pitch_wam_kyuhoji_${dateStr}.txt`);
fs.writeFileSync(pitchPath, pitch, 'utf-8');
console.log(`✅ 営業訴求トーク: ${pitchPath}`);
