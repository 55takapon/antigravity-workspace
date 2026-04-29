/**
 * 個別指導WAM 八尾永畑校 GBP診断テスト
 * 診断日: 2026-04-02
 */
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText, generateSalesPitchText } = require('./generate_report');
const fs = require('fs');
const path = require('path');

// === 収集データ ===
const data = {
  basic: {
    name: '個別指導WAM 八尾永畑校',
    category: '受験予備校',
    subCategories: ['学習塾', '個別指導塾'],
    address: '〒581-0083 大阪府八尾市永畑町1丁目2-43',
    phone: '072-927-6927',
    website: 'https://k-wam.jp',
    hours: {
      '月曜日': '13:00～21:30',
      '火曜日': '13:00～21:30',
      '水曜日': '13:00～21:30',
      '木曜日': '13:00～21:30',
      '金曜日': '13:00～21:30',
      '土曜日': '定休日',
      '日曜日': '定休日'
    },
    // ユーザー指定：説明文あり、しかし規約違反のハッシュタグ含む
    description: '個別指導塾ならではの、生徒さん一人一人に合わせたカリキュラムを提供いたします。勉強の楽しさを知り、少しずつステップアップして、自信を持って継続していく。我々のノウハウでお子さんの成長を促していきます。詳細はWAM久宝寺校までお問い合わせください。 #Wam #wam #ワム #八尾 #八尾市 #龍華 #永畑 #志紀 #安中 #高美南 #八尾高 #JR八尾 #小 #中 #高 #中学受験 #高校受験 #大学受験 #入試 #私立 #公立 #英検 #漢検 #定期テスト #定期試験 #定テ',
    attributes: [
      'オンライン授業'
    ],
    services: []
  },
  reviews: {
    totalCount: 0,
    averageRating: 0.0,
    items: [] // 口コミゼロ
  },
  photos: {
    totalCount: 27, // ユーザー指定：写真は27枚あり
    hasExterior: true,
    hasInterior: true,
    hasFood: false,
    hasStaff: true
  },
  posts: {
    latestPostDate: null, 
    recentCount: 0, 
    hasOffer: false,
    hasEvent: false,
    hasKeywordContent: false 
  },
  competitors: [
    { name: '個別指導マーベル 高美校', rating: 4.9, reviewCount: 27 },
    { name: '個別指導キャンパス 八尾校', rating: 4.5, reviewCount: 24 },
    { name: '神尾塾', rating: 4.3, reviewCount: 6 },
    { name: '個別指導の学習塾 スクールIE 太子堂校', rating: 5.0, reviewCount: 5 }
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
const baseName = `diagnostic_report_wam_yao_nagahata_${dateStr}`;

const html = generateHTML(result, data);

// 同一オーナー（久宝寺校）との統一性を持たせるため、ハッシュタグに対する警告アラートを追加
const htmlWithHashtagWarning = html.replace(/<section id="opportunity">/g, '<section id="opportunity"><div class="alert" style="background:#fff3cd; color:#856404; padding:15px; margin-bottom:20px; border-left:5px solid #ffeeba; border-radius:4px;"><strong>🚨 コンプライアンス警告:</strong> Googleビジネスプロフィールの説明文にハッシュタグ（#）が含まれています。これはGoogleのガイドライン違反（キーワードの詰め込み）に該当し、アカウント停止リスクがあるため、早急な削除・修正を強く推奨します。</div>');

const htmlPath = path.join(__dirname, '..', `${baseName}.html`);
fs.writeFileSync(htmlPath, htmlWithHashtagWarning, 'utf-8');
console.log(`\n✅ HTML: ${htmlPath}`);

const text = generateNotebookText(result, data);
const textPath = path.join(__dirname, '..', `${baseName}_notebook.txt`);
fs.writeFileSync(textPath, text, 'utf-8');
console.log(`✅ NotebookLM: ${textPath}`);

const jsonPath = path.join(__dirname, '..', `diagnostic_data_wam_yao_nagahata_${dateStr}.json`);
fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
console.log(`✅ データ: ${jsonPath}`);

const pitch = generateSalesPitchText(result, data);
const pitchPath = path.join(__dirname, '..', `diagnostic_sales_pitch_wam_yao_nagahata_${dateStr}.txt`);
fs.writeFileSync(pitchPath, pitch, 'utf-8');
console.log(`✅ 営業訴求トーク: ${pitchPath}`);
