/**
 * analyze_reviews.js
 * 口コミデータのテキスト分析エンジン
 * 
 * Usage:
 *   node analyze_reviews.js --input review_data_xxx.json [--industry restaurant] [--benchmark competitor.json]
 * 
 * 分析項目:
 *   1. 評価分布（星1-5の件数・割合・平均・中央値）
 *   2. テーマ分類（業種別キーワード辞書ベース）
 *   3. 感情分析（ポジティブ/ネガティブ/中立）
 *   4. 頻出キーワード（肯定TOP10 / 否定TOP10）
 *   5. 強み抽出（高評価口コミの共通テーマ）
 *   6. 弱み・改善点抽出（低〜中評価のテーマ）
 *   7. オーナー返信分析
 *   8. 時系列分析
 */

const fs = require('fs');
const path = require('path');

// === JST日付生成 ===
function getJSTDateStr() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10).replace(/-/g, '');
}

// === 業種別テーマ分類辞書 ===
const THEME_DICTIONARIES = {
  restaurant: {
    '味・品質': ['美味し', 'おいし', 'うまい', '旨い', '絶品', '最高', '本格', '風味', 'ジューシー', '柔らか', '出来たて', '揚げたて', '作りたて', '手作り', '辛', '甘', '酸味'],
    '接客・サービス': ['接客', '親切', '笑顔', '気さく', '丁寧', '感じが良', '愛想', 'アットホーム', '店員', 'スタッフ', 'マスター', 'オーナー', '店主', '対応'],
    '雰囲気・清潔感': ['雰囲気', '清潔', 'きれい', 'キレイ', 'おしゃれ', '居心地', '落ち着', 'リラックス', '内装', '店内', '素敵'],
    '価格・コスパ': ['コスパ', '安い', 'お手頃', 'リーズナブル', '値段', '価格', '600円', '手頃'],
    '立地・アクセス': ['駅', '近く', '徒歩', 'アクセス', '場所', '立地', '税務署'],
    '待ち時間・利便性': ['待ち', '予約', 'テイクアウト', '持ち帰り', 'Uber', 'LINE', '注文してから', 'スムーズ'],
    'メニュー・品揃え': ['メニュー', '種類', 'バリエーション', '選べ', 'セット', 'お弁当', 'トッポッキ', 'チーズボール', 'サイドメニュー'],
    'リピート意向': ['また', 'リピ', '通い', '毎日', '何度も', '定期的', '絶対にまた', 'おかわり']
  },
  medical: {
    '技術・腕': ['上手', '腕', '技術', '治療', '施術', '的確', '正確'],
    '説明の丁寧さ': ['説明', '丁寧', '分かりやす', 'わかりやす', '親切', '相談'],
    '痛み・不安配慮': ['痛', '不安', '怖', '安心', '優し', 'リラックス'],
    '待ち時間': ['待ち', '予約', 'スムーズ', '時間通り'],
    '設備・清潔感': ['設備', '清潔', 'きれい', '新しい', '最新'],
    'スタッフ': ['スタッフ', '受付', '看護', '衛生', '対応']
  },
  legal: {
    '専門性': ['専門', '知識', '経験', '信頼', '的確', 'プロ'],
    '対応速度': ['迅速', '早い', 'スピーディ', 'すぐ', 'レスポンス'],
    '説明の分かりやすさ': ['説明', '分かりやす', 'わかりやす', '丁寧', '親身'],
    '費用': ['費用', '料金', '価格', 'リーズナブル', '良心的'],
    '人柄': ['人柄', '親切', '優し', '話しやす', '気さく', '安心']
  },
  beauty: {
    '技術・仕上がり': ['技術', '上手', '仕上がり', 'カット', 'カラー', 'デザイン', '似合'],
    'カウンセリング': ['カウンセリング', '相談', '提案', '希望', 'ヒアリング'],
    '雰囲気': ['雰囲気', 'おしゃれ', '居心地', 'リラックス', '落ち着'],
    '価格': ['価格', '料金', 'コスパ', 'リーズナブル'],
    'スタッフ': ['スタッフ', 'スタイリスト', '接客', '対応', '感じが良']
  },
  general: {
    '品質': ['品質', '良い', '素晴らし', '最高', '美味し', 'おいし', '上手'],
    '接客': ['接客', '対応', '親切', '丁寧', '笑顔', '気さく'],
    '雰囲気': ['雰囲気', '清潔', 'きれい', 'おしゃれ', '居心地'],
    '価格': ['価格', 'コスパ', '安い', 'リーズナブル', 'お手頃'],
    '立地': ['駅', '近く', 'アクセス', '便利', '立地'],
    'その他': []
  }
};

// === 感情分析辞書 ===
const SENTIMENT = {
  positive: ['美味し', 'おいし', '最高', '素晴らし', '嬉し', '楽し', '満足', 'おすすめ', 'オススメ', 'リピ', 'また行', 'また来', '大好き', '絶品', '感動', '幸せ', '感謝', '丁寧', '親切', '笑顔', 'コスパ', '本格', 'ジューシー', '柔らか', 'お気に入り', '癖になる', '間違いない', '文句なし', '大満足'],
  negative: ['残念', '不満', '微妙', '期待外れ', '冷た', 'うるさ', '騒', '高い', '不味', 'まずい', '汚', '狭', '遅い', '待たさ', '対応が悪', '感じが悪', '二度と', '不衛生', '物足りな', '普通', 'イマイチ', 'いまいち', 'イライラ', '改善', '最悪', 'ひどい', '酷い', '雑', '文句', '怒', '悲し', '嫌']
};

// === テーマ分類 ===
function classifyThemes(reviews, industry = 'restaurant') {
  const dict = THEME_DICTIONARIES[industry] || THEME_DICTIONARIES.general;
  const themeResults = {};

  for (const theme of Object.keys(dict)) {
    themeResults[theme] = { count: 0, positive: 0, negative: 0, neutral: 0, examples: [] };
  }

  for (const r of reviews) {
    if (!r.text) continue; // テキストがないものはスキップ
    const text = r.text;
    const isPositive = r.rating >= 4;
    const isNegative = r.rating <= 2;

    for (const [theme, keywords] of Object.entries(dict)) {
      if (keywords.length === 0) continue;
      const matched = keywords.some(kw => text.includes(kw));
      if (matched) {
        themeResults[theme].count++;
        if (isPositive) themeResults[theme].positive++;
        else if (isNegative) themeResults[theme].negative++;
        else themeResults[theme].neutral++;

        if (themeResults[theme].examples.length < 5) { // 少し多めに取得しておき後で重複排除
          themeResults[theme].examples.push({
            name: r.author || r.name,
            rating: r.rating,
            excerpt: text.length > 100 ? text.substring(0, 100) + '...' : text
          });
        }
      }
    }
  }

  return themeResults;
}

// === 感情分析 ===
function analyzeSentiment(reviews) {
  const results = { positive: 0, negative: 0, neutral: 0 };
  const details = [];

  for (const r of reviews) {
    const text = r.text;
    let posScore = 0;
    let negScore = 0;

    for (const kw of SENTIMENT.positive) {
      if (text.includes(kw)) posScore++;
    }
    for (const kw of SENTIMENT.negative) {
      if (text.includes(kw)) negScore++;
    }

    // 星評価も加味
    if (r.rating >= 4) posScore += 2;
    if (r.rating <= 2) negScore += 2;

    let sentiment;
    if (posScore > negScore) {
      sentiment = 'positive';
      results.positive++;
    } else if (negScore > posScore) {
      sentiment = 'negative';
      results.negative++;
    } else {
      sentiment = 'neutral';
      results.neutral++;
    }

    details.push({ name: r.name, rating: r.rating, sentiment, posScore, negScore });
  }

  return { summary: results, details };
}

// === 評価分布 ===
function analyzeRatingDistribution(reviews) {
  const dist = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  const ratings = [];

  for (const r of reviews) {
    if (r.rating >= 1 && r.rating <= 5) {
      dist[r.rating]++;
      ratings.push(r.rating);
    }
  }

  const total = ratings.length;
  const avg = total > 0 ? (ratings.reduce((a, b) => a + b, 0) / total) : 0;
  const sorted = [...ratings].sort((a, b) => a - b);
  const median = total > 0 ? sorted[Math.floor(total / 2)] : 0;

  const percentages = {};
  for (const [star, count] of Object.entries(dist)) {
    percentages[star] = total > 0 ? Math.round((count / total) * 1000) / 10 : 0;
  }

  return {
    distribution: dist,
    percentages,
    average: Math.round(avg * 100) / 100,
    median,
    total
  };
}

// === 頻出キーワード抽出 ===
function extractKeywords(reviews) {
  const positiveWords = {};
  const negativeWords = {};

  // 肯定的キーワード
  for (const r of reviews.filter(r => r.rating >= 4)) {
    for (const kw of SENTIMENT.positive) {
      if (r.text.includes(kw)) {
        positiveWords[kw] = (positiveWords[kw] || 0) + 1;
      }
    }
  }

  // 否定的キーワード
  for (const r of reviews) {
    for (const kw of SENTIMENT.negative) {
      if (r.text.includes(kw)) {
        negativeWords[kw] = (negativeWords[kw] || 0) + 1;
      }
    }
  }

  // ソートしてTOP10
  const topPositive = Object.entries(positiveWords)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([word, count]) => ({ word, count }));

  const topNegative = Object.entries(negativeWords)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([word, count]) => ({ word, count }));

  return { positive: topPositive, negative: topNegative };
}

// === 強み・弱み抽出 ===
function extractStrengthsWeaknesses(themeResults, reviews) {
  const globallyUsedQuotes = []; // 全テーマで共有する使用済み引用リスト

  // 重複排除ロジック：例文の類似度をチェック
  function deduplicateExamples(examples) {
    const unique = [];
    for (const ex of examples) {
      // 既存のものと50%以上文字が被っていないか簡易チェック
      let isDuplicate = false;
      const combinedList = [...unique, ...globallyUsedQuotes];
      
      for (const u of combinedList) {
        // IDや名前が同じならそもそも除外
        if (ex.name === u.name) {
           isDuplicate = true; break;
        }

        const shorter = Math.min(ex.excerpt.length, u.excerpt ? u.excerpt.length : u.length);
        const compareText = u.excerpt || u;
        let matchCount = 0;
        for (let i = 0; i < shorter; i++) {
          if (ex.excerpt[i] === compareText[i]) matchCount++;
        }
        if (shorter > 10 && (matchCount / shorter) > 0.5) {
          isDuplicate = true; break;
        }
      }
      if (!isDuplicate) {
        unique.push(ex);
        globallyUsedQuotes.push(ex); // グローバルリストに追加
      }
      if (unique.length >= 2) break; // TOP 2 examples
    }
    return unique;
  }

  // 強み: 高頻度かつポジティブ率の高いテーマ
  const strengths = Object.entries(themeResults)
    .filter(([, data]) => data.count > 0 && data.positive > 0)
    .sort((a, b) => b[1].positive - a[1].positive)
    .slice(0, 5)
    .map(([theme, data]) => ({
      theme,
      mentionCount: data.count,
      positiveCount: data.positive,
      examples: deduplicateExamples(data.examples)
    }));

  // 弱み: ネガティブ言及のあるテーマ、または中〜低評価口コミのテーマ
  const weaknesses = Object.entries(themeResults)
    .filter(([, data]) => data.negative > 0 || data.neutral > 0)
    .sort((a, b) => (b[1].negative + b[1].neutral) - (a[1].negative + a[1].neutral))
    .slice(0, 5)
    .map(([theme, data]) => ({
      theme,
      mentionCount: data.count,
      negativeCount: data.negative,
      neutralCount: data.neutral,
      examples: deduplicateExamples(data.examples)
    }));

  // 低評価口コミからの具体的な改善点（星3以下でテキストあり）
  // スクレイピング時の重複を排除するため、author名で一意にする
  const uniqueLowRated = [];
  const seenAuthors = new Set();
  
  reviews.filter(r => r.rating <= 3 && r.text && r.text.length > 5).forEach(r => {
    const author = r.author || r.name;
    if (!seenAuthors.has(author)) {
      seenAuthors.add(author);
      uniqueLowRated.push({
        name: author,
        rating: r.rating,
        text: r.text,
        date: r.dateText || r.date
      });
    }
  });

  return { strengths, weaknesses, lowRatedReviews: uniqueLowRated };
}

// === オーナー返信分析 ===
function analyzeOwnerReplies(reviews) {
  const total = reviews.length; // 母数は全件！
  const withReply = reviews.filter(r => r.ownerReply && r.ownerReply.length > 0).length;
  const replyRate = total > 0 ? Math.round((withReply / total) * 1000) / 10 : 0;

  // テンプレ返信 vs 個別対応の判定（返信文の多様性をチェック）
  const replyTexts = reviews.filter(r => r.hasOwnerReply).map(r => r.ownerReplyText);
  let templateCount = 0;
  let personalCount = 0;

  for (let i = 0; i < replyTexts.length; i++) {
    let isTemplate = false;
    for (let j = i + 1; j < replyTexts.length; j++) {
      // 類似度チェック（60%以上一致ならテンプレと判定）
      const shorter = Math.min(replyTexts[i].length, replyTexts[j].length);
      if (shorter > 0) {
        let matchChars = 0;
        for (let k = 0; k < shorter; k++) {
          if (replyTexts[i][k] === replyTexts[j][k]) matchChars++;
        }
        if (matchChars / shorter > 0.6) {
          isTemplate = true;
          break;
        }
      }
    }
    if (isTemplate) templateCount++;
    else personalCount++;
  }

  return {
    total,
    withReply,
    replyRate,
    templateEstimate: templateCount,
    personalEstimate: personalCount,
    quality: replyRate >= 80 ? '良好' : replyRate >= 50 ? '改善の余地あり' : '要改善'
  };
}

// === 時系列分析 ===
function analyzeTimeline(reviews) {
  const periods = {
    '直近3ヶ月': 0,
    '3-6ヶ月前': 0,
    '6ヶ月-1年前': 0,
    '1年以上前': 0
  };

  for (const r of reviews) {
    const d = r.date || '';
    if (d.includes('か月前') || d.includes('ヶ月前')) {
      const m = d.match(/(\d+)/);
      if (m) {
        const months = parseInt(m[1], 10);
        if (months <= 3) periods['直近3ヶ月']++;
        else if (months <= 6) periods['3-6ヶ月前']++;
        else periods['6ヶ月-1年前']++;
      }
    } else if (d.includes('週間前') || d.includes('日前')) {
      periods['直近3ヶ月']++;
    } else if (d.includes('年前')) {
      const m = d.match(/(\d+)/);
      if (m && parseInt(m[1], 10) >= 2) {
        periods['1年以上前']++;
      } else {
        periods['6ヶ月-1年前']++;
      }
    } else {
      periods['1年以上前']++;
    }
  }

  return periods;
}

// === メイン分析処理 ===
function analyzeReviews(inputPath, options = {}) {
  const industry = options.industry || 'restaurant';
  const benchmarkPath = options.benchmark || null;

  // 入力データ読み込み
  const reviewData = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
  const reviews = reviewData.reviews || [];
  
  // スクレイピングされた公式メタデータがあれば取得（なければフォールバック）
  const metadata = reviewData.metadata || {
    averageRating: 0,
    totalReviews: reviews.length,
    businessCategory: 'restaurant'
  };

  const businessCategory = metadata.businessCategory || 'restaurant';
  const businessName = reviewData.businessName || reviewData.clientName || 'Unknown';
  const clientId = reviewData.clientId || businessName.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');

  console.log(`\n📊 口コミ分析を開始します...`);
  console.log(`   ビジネス名: ${businessName}`);
  console.log(`   公式総口コミ件数: ${metadata.totalReviews} (うち分析対象: ${reviews.length})`);
  console.log(`   公式平均評価: ${metadata.averageRating}`);
  console.log(`   公式業種カテゴリ: ${businessCategory}\n`);

  // テキスト付きの口コミのみを抽出（言語分析用）
  const textReviews = reviews.filter(r => r.text && r.text.length > 0);

  // 各分析を実行
  const ratingDist = analyzeRatingDistribution(reviews); // 評価分布は全件
  console.log('   ✅ 評価分布分析完了');

  const themes = classifyThemes(textReviews, industry); // テーマ分類はテキストありのみ
  console.log('   ✅ テーマ分類完了');

  const sentiment = analyzeSentiment(textReviews);
  console.log('   ✅ 感情分析完了');

  const keywords = extractKeywords(textReviews);
  console.log('   ✅ 頻出キーワード抽出完了');

  const { strengths, weaknesses, lowRatedReviews } = extractStrengthsWeaknesses(themes, textReviews);
  console.log('   ✅ 強み/弱み抽出完了');

  const ownerReply = analyzeOwnerReplies(reviews); // 返信分析は全件
  console.log('   ✅ オーナー返信分析完了');

  // ベンチマーク比較（オプション）
  let benchmark = null;
  if (benchmarkPath && fs.existsSync(benchmarkPath)) {
    const benchData = JSON.parse(fs.readFileSync(benchmarkPath, 'utf-8'));
    const benchReviews = benchData.reviews || benchData;
    benchmark = {
      businessName: benchData.businessName || 'Competitor',
      rating: analyzeRatingDistribution(benchReviews),
      themes: classifyThemes(benchReviews, industry),
      ownerReply: analyzeOwnerReplies(benchReviews)
    };
    console.log('   ✅ ベンチマーク比較完了');
  }

  // 分析結果をJSONとして保存
  const analysis = {
    clientId,
    businessName,
    analyzedAt: new Date().toISOString(),
    scrapedUrl: reviewData.scrapedUrl || '',
    metadata: metadata, // 公式の総合件数・評価・カテゴリ
    analyzedCount: textReviews.length, // テキストがあって分析した件数
    ratingDistribution: ratingDist,
    themeAnalysis: themes,
    sentimentAnalysis: sentiment.summary,
    keywords,
    strengths,
    weaknesses,
    lowRatedReviews,
    ownerReplyAnalysis: ownerReply,
    benchmark
  };

  // 出力
  const dateStr = getJSTDateStr();
  const outputName = `review_analysis_${clientId}_${dateStr}.json`;
  const outputPath = path.join(__dirname, '..', outputName);

  fs.writeFileSync(outputPath, JSON.stringify(analysis, null, 2), 'utf-8');
  console.log(`\n✅ 分析完了！ → ${outputPath}\n`);

  return analysis;
}

// === CLI実行 ===
if (require.main === module) {
  const args = process.argv.slice(2);
  const inputIdx = args.indexOf('--input');
  const industryIdx = args.indexOf('--industry');
  const benchmarkIdx = args.indexOf('--benchmark');

  if (inputIdx === -1) {
    console.error('Usage: node analyze_reviews.js --input <file.json> [--industry restaurant|medical|legal|beauty|general] [--benchmark <competitor.json>]');
    process.exit(1);
  }

  const inputPath = args[inputIdx + 1];
  const options = {
    industry: industryIdx !== -1 ? args[industryIdx + 1] : 'restaurant',
    benchmark: benchmarkIdx !== -1 ? args[benchmarkIdx + 1] : null
  };

  analyzeReviews(inputPath, options);
}

module.exports = { analyzeReviews };
