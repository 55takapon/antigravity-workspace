/**
 * GBP 5軸スコアリングエンジン
 * 収集したGBPデータを5軸で評価し、伸びしろTOP3を選定する
 * 
 * Usage: const result = analyzeGBP(data);
 */

/**
 * 業種別ベンチマーク
 */
const BENCHMARKS = {
  // postTarget: 3ヶ月間の推奨投稿数, postLabel: 推奨頻度の表示テキスト
  restaurant: { label: '飲食店', reviewTarget: [80, 150], photoTarget: 25, postTarget: 24, postLabel: '週2回', keywords: ['居酒屋', 'レストラン', 'カフェ', 'ラーメン', '焼肉', '寿司', 'うどん', 'そば', 'イタリアン', 'フレンチ', '中華', '定食', 'バー', '焼き鳥', 'ダイニング', '食堂', '弁当', 'お好み焼き', 'たこ焼き', '鉄板焼', 'もんじゃ', '鍋', '串カツ', 'ピザ', 'パスタ', 'カレー', 'ハンバーガー', '天ぷら', 'とんかつ'] },
  medical:    { label: 'クリニック', reviewTarget: [30, 70], photoTarget: 15, postTarget: 9, postLabel: '月3回', keywords: ['歯科', '内科', '皮膚科', '眼科', '整形外科', '小児科', '産婦人科', 'クリニック', '医院', '病院', '耳鼻'] },
  bodywork:   { label: '施術院', reviewTarget: [40, 80], photoTarget: 15, postTarget: 12, postLabel: '週1回', keywords: ['整体', '整骨', '鍼灸', 'マッサージ', 'カイロ', '指圧', 'リラクゼーション', 'もみほぐし', '接骨'] },
  education:  { label: '教育', reviewTarget: [20, 50], photoTarget: 10, postTarget: 6, postLabel: '月2回', keywords: ['学習塾', '予備校', 'スクール', '学習', '個別指導', '家庭教師', '英会話', 'プログラミング'] },
  legal:      { label: '士業', reviewTarget: [15, 40], photoTarget: 8, postTarget: 6, postLabel: '月2回', keywords: ['税理士', '司法書士', '弁護士', '行政書士', '社労士', '会計士', '公認会計', '法律事務所'] },
  realEstate: { label: '不動産', reviewTarget: [30, 60], photoTarget: 15, postTarget: 12, postLabel: '週1回', keywords: ['不動産', '賃貸', '売買', 'マンション', 'アパート', '仲介', '住宅'] },
  service:    { label: '工務店', reviewTarget: [15, 40], photoTarget: 20, postTarget: 6, postLabel: '月2回', keywords: ['工務店', 'リフォーム', '建設', '塗装', '住宅', '建築', '内装', '外構', '屋根'] },
  beauty:     { label: '美容', reviewTarget: [50, 120], photoTarget: 25, postTarget: 24, postLabel: '週2回', keywords: ['美容室', 'ヘアサロン', '美容院', 'エステ', 'ネイル', 'まつ毛', '脱毛', '理髪', 'バーバー', '理容'] },
  retail:     { label: '小売', reviewTarget: [20, 60], photoTarget: 25, postTarget: 12, postLabel: '週1回', keywords: ['花屋', 'パン屋', '書店', '雑貨', 'アパレル', '衣料', '酒屋', '家具', '靴', 'ジュエリー', 'ケーキ', '洋菓子', 'ペットショップ'] },
  general:    { label: '汎用', reviewTarget: [30, 80], photoTarget: 8, postTarget: 12, postLabel: '週1回', keywords: [] }
};

/**
 * ランク定義
 */
const RANKS = [
  { rank: 'S', min: 90, color: '🟢', label: '最高水準' },
  { rank: 'A', min: 75, color: '🔵', label: '平均以上' },
  { rank: 'B', min: 50, color: '🟡', label: '平均的' },
  { rank: 'C', min: 30, color: '🟠', label: '改善が必要' },
  { rank: 'D', min: 0,  color: '🔴', label: '早急な対応が必要' }
];

/**
 * スコアからランクを取得
 */
function scoreToRank(score) {
  for (const r of RANKS) {
    if (score >= r.min) return r;
  }
  return RANKS[RANKS.length - 1];
}

/**
 * 業種を自動判定
 */
function detectIndustry(category, name) {
  const text = `${category || ''} ${name || ''}`.toLowerCase();
  for (const [key, bm] of Object.entries(BENCHMARKS)) {
    if (key === 'general') continue;
    if (bm.keywords.some(kw => text.includes(kw))) return key;
  }
  return 'general';
}

/**
 * 軸①: 基本情報の完全度（0-100）
 * 配点: 名前3 + カテゴリ3 + 住所4 + 電話10 + サイト10 + 営業時間10 + 説明文25 + 属性20 + サービス15 = 100
 * 設計原則: Googleのプロファイル強度と乖離しないこと
 */
function scoreBasicInfo(basic) {
  let score = 0;
  const details = [];

  // ビジネス名（3点）— ほぼ全店舗が持つ。差がつかない。
  if (basic.name) { score += 3; } else { details.push('ビジネス名が未設定'); }

  // メインカテゴリ（3点）— ほぼ全店舗が持つ。差がつかない。
  if (basic.category) { score += 3; } else { details.push('カテゴリが未設定'); }

  // 住所（4点）— ほぼ全店舗が持つ。
  if (basic.address) { score += 4; } else { details.push('住所が未設定'); }

  // 電話番号（10点）
  if (basic.phone) { score += 10; } else { details.push('電話番号が未設定'); }

  // ウェブサイト（10点）— SNS/YouTube等のリンクは半分のみ
  if (basic.website) {
    const url = basic.website.toLowerCase();
    const isSNS = ['youtu.be', 'youtube.com', 'instagram.com', 'twitter.com', 'x.com', 'facebook.com', 'line.me', 'tiktok.com'].some(d => url.includes(d));
    if (isSNS) {
      score += 5;
      details.push('ウェブサイトがSNS/動画リンク（公式サイトの設定を推奨）');
    } else {
      score += 10;
    }
  } else {
    details.push('ウェブサイトURLが未設定');
  }

  // 営業時間（10点）
  if (basic.hours && Object.keys(basic.hours).length >= 5) {
    score += 10;
  } else if (basic.hours) {
    score += 5;
    details.push('営業時間の設定が一部不完全');
  } else {
    details.push('営業時間が未設定');
  }

  // 説明文（25点）— MEOの最重要基本項目。未設定は致命的。
  if (basic.description && basic.description.length > 0) {
    const len = basic.description.length;
    if (len >= 500) { score += 25; }
    else if (len >= 200) { score += 18; details.push(`説明文が${len}文字（500文字以上を推奨）`); }
    else if (len >= 50) { score += 10; details.push(`説明文が${len}文字（500文字以上を推奨）`); }
    else { score += 5; details.push(`説明文が${len}文字と短い（500文字以上を推奨）`); }
  } else {
    details.push('説明文が未設定（検索キーワードを含む500文字以上の説明文を推奨）');
  }

  // 属性（20点）— 「未対応」表記のものは除外してカウント
  const attrs = (basic.attributes || []);
  const activeAttrs = attrs.filter(a => !a.includes('未対応'));
  const attrCount = activeAttrs.length;
  if (attrCount >= 10) { score += 20; }
  else if (attrCount >= 5) { score += 15; details.push(`有効な属性が${attrCount}個（10個以上を推奨）`); }
  else if (attrCount >= 3) { score += 10; details.push(`有効な属性が${attrCount}個（10個以上を推奨）`); }
  else if (attrCount >= 1) { score += 5; details.push(`有効な属性が${attrCount}個と少ない（10個以上を推奨）`); }
  else { details.push('属性が未設定'); }

  // サービス項目（15点）— services / serviceItems 両方のフィールド名に対応
  const serviceCount = (basic.services || basic.serviceItems || []).length;
  if (serviceCount >= 5) { score += 15; }
  else if (serviceCount >= 3) { score += 10; details.push(`サービス項目が${serviceCount}個（5個以上を推奨）`); }
  else if (serviceCount >= 1) { score += 5; details.push(`サービス項目が${serviceCount}個と少ない`); }
  else { details.push('サービス項目が未設定'); }

  return { score: Math.min(score, 100), details };
}

/**
 * 軸②: 写真・動画の充実度（0-100）
 */
function scorePhotos(photos, benchmark) {
  let score = 0;
  const details = [];
  const count = photos.totalCount || 0;

  // 写真総枚数（40点）
  if (count >= 30) { score += 40; }
  else if (count >= 20) { score += 30; details.push(`写真${count}枚（${benchmark.photoTarget}枚以上を推奨）`); }
  else if (count >= 10) { score += 20; details.push(`写真${count}枚（${benchmark.photoTarget}枚以上を推奨）`); }
  else if (count >= 5) { score += 10; details.push(`写真${count}枚と少ない（${benchmark.photoTarget}枚以上を推奨）`); }
  else { details.push(`写真が${count}枚と非常に少ない（${benchmark.photoTarget}枚以上を推奨）`); }

  // 写真カテゴリ判定 — hasXxx or categories.xxx の両形式に対応
  const cat = photos.categories || {};
  const hasExterior = photos.hasExterior || cat.exterior;
  const hasInterior = photos.hasInterior || cat.interior;
  const hasFood = photos.hasFood || cat.food || cat.menu;
  const hasStaff = photos.hasStaff || cat.staff;

  // 外観写真（15点）
  if (hasExterior) { score += 15; } else { details.push('外観写真の追加を推奨'); }

  // 内観写真（15点）
  if (hasInterior) { score += 15; } else { details.push('店内写真の追加を推奨'); }

  // 商品/メニュー写真（15点）
  if (hasFood) { score += 15; } else { details.push('商品/メニュー写真の追加を推奨'); }

  // スタッフ写真（15点）
  if (hasStaff) { score += 15; } else { details.push('スタッフ写真の追加を推奨'); }

  return { score: Math.min(score, 100), details };
}

/**
 * 軸③: 口コミの力（0-100）
 */
function scoreReviews(reviews, benchmark) {
  let score = 0;
  const details = [];
  const count = reviews.totalCount || 0;
  const avg = reviews.averageRating || 0;
  const items = reviews.items || [];

  // 口コミ件数（30点）— 競合との差が重要
  const [targetMin, targetMax] = benchmark.reviewTarget;
  if (count >= targetMax) { score += 30; }
  else if (count >= targetMin) {
    score += 20;
    details.push(`口コミ${count}件（業種上位の目安: ${targetMax}件以上）`);
  }
  else if (count >= targetMin * 0.5) {
    score += 10;
    details.push(`口コミ${count}件（業種平均目安: ${targetMin}件以上を推奨）`);
  }
  else if (count > 0) {
    score += 5;
    details.push(`口コミ${count}件と少ない（${targetMin}件以上を推奨）`);
  }
  else { details.push('口コミが0件（まずは10件を目標に）'); }

  // 平均評価（25点）
  if (avg >= 4.5) { score += 25; }
  else if (avg >= 4.0) { score += 20; details.push(`平均評価${avg}星（4.5以上で高い信頼感）`); }
  else if (avg >= 3.5) { score += 10; details.push(`平均評価${avg}星（4.0以上を推奨）`); }
  else if (avg > 0) { score += 0; details.push(`平均評価${avg}星と低め（4.0以上を推奨）`); }

  // オーナー返信率（15点）— 返信は基本動作。件数の方が重要。
  const repliedCount = items.filter(r => r.hasOwnerReply || r.hasReply).length;
  const replyRate = items.length > 0 ? repliedCount / items.length : 0;
  if (replyRate >= 1.0) { score += 15; }
  else if (replyRate >= 0.8) { score += 12; details.push(`口コミ返信率${Math.round(replyRate * 100)}%（100%を推奨）`); }
  else if (replyRate >= 0.5) { score += 7; details.push(`口コミ返信率${Math.round(replyRate * 100)}%（100%を推奨）`); }
  else if (replyRate > 0) { score += 3; details.push(`口コミ返信率${Math.round(replyRate * 100)}%と低い（100%を推奨）`); }
  else if (items.length > 0) { details.push('口コミへの返信がありません（100%返信を推奨）'); }

  // 口コミの鮮度（15点）
  const recentReview = items[0]; // 最新が先頭と仮定
  if (recentReview?.date) {
    const dateText = recentReview.date;
    if (dateText.includes('週間前') || dateText.includes('日前') || dateText.includes('昨日') || dateText.includes('時間前')) {
      score += 15;
    } else if (dateText.includes('か月前') || dateText.includes('ヶ月前')) {
      const months = parseInt(dateText) || 99;
      if (months <= 1) { score += 15; }
      else if (months <= 3) { score += 10; }
      else { score += 5; details.push('最新の口コミから3ヶ月以上経過'); }
    } else {
      score += 5;
    }
  }

  // 口コミの質（10点）
  const detailedCount = items.filter(r => r.hasText || (r.text || '').length >= 50).length;
  const detailedRate = items.length > 0 ? detailedCount / items.length : 0;
  if (detailedRate >= 0.5) { score += 10; }
  else if (detailedRate >= 0.3) { score += 7; }
  else if (detailedRate > 0) { score += 3; }

  // サンプルベースの参考値であることを記録
  const sampleSize = items.length;
  const totalReviewCount = reviews.totalCount || 0;
  const isFullCount = sampleSize >= totalReviewCount * 0.9; // 90%以上取得できていれば全件とみなす

  return {
    score: Math.min(score, 100),
    details,
    replyRate: Math.round(replyRate * 100),
    replyRateNote: isFullCount
      ? `${repliedCount}/${sampleSize}件確認`
      : `${repliedCount}/${sampleSize}件のサンプルに基づく参考値（全${totalReviewCount}件中）`
  };
}

/**
 * 軸④: 投稿の活用度（0-100）
 */
function scorePosts(posts, benchmark) {
  const postTarget = (benchmark && benchmark.postTarget) || 12;
  const postLabel = (benchmark && benchmark.postLabel) || '週1回';
  let score = 0;
  const details = [];

  // recentCount or totalRecent の両形式対応
  const recentCount = posts.recentCount || posts.totalRecent || 0;
  // latestPostDate or latestDate の両形式対応
  const latestPostDate = posts.latestPostDate || posts.latestDate;

  // 投稿ゼロの場合
  if (recentCount === 0 && !latestPostDate) {
    details.push('投稿機能が活用されていません');
    return { score: 0, details };
  }

  // ── 最新投稿の鮮度（25点）──
  if (latestPostDate) {
    const dateText = latestPostDate;
    const isoMatch = dateText.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (isoMatch) {
      const postDate = new Date(dateText);
      const now = new Date();
      const daysDiff = Math.floor((now - postDate) / (1000 * 60 * 60 * 24));
      if (daysDiff <= 7) { score += 25; }
      else if (daysDiff <= 14) { score += 15; }
      else if (daysDiff <= 30) { score += 10; }
      else { score += 3; details.push(`投稿が${daysDiff}日間更新されていません`); }
    } else if (dateText.includes('日前') || dateText.includes('昨日') || dateText.includes('時間前')) {
      score += 25;
    } else if (dateText.includes('週間前')) {
      const weeks = parseInt(dateText) || 99;
      if (weeks <= 1) { score += 25; }
      else if (weeks <= 2) { score += 15; }
      else { score += 10; }
    } else if (dateText.includes('か月前') || dateText.includes('ヶ月前')) {
      const months = parseInt(dateText) || 99;
      if (months <= 1) { score += 5; details.push('投稿が1ヶ月以上更新されていません'); }
      else { details.push(`投稿が${dateText}から更新されていません`); }
    }
  }

  // ── 継続性（25点）── 直近3ヶ月の投稿頻度
  // 週1以上=25, 月2-3=15, 月1=10, 不定期=5
  if (recentCount >= postTarget) { score += 25; }
  else if (recentCount >= Math.ceil(postTarget * 0.5)) { score += 15; }
  else if (recentCount >= 3) { score += 10; details.push(`直近3ヶ月で${recentCount}件（${postLabel}以上を推奨）`); }
  else if (recentCount >= 1) { score += 5; details.push(`直近3ヶ月で${recentCount}件と少ない（${postLabel}以上を推奨）`); }

  // ── 長期空白のペナルティ（-10〜-20点）──
  const gapMonths = posts.gapMonths || 0;
  if (gapMonths >= 6) {
    score -= 20;
    details.push(`${gapMonths}ヶ月間の投稿空白期間あり（継続的な運用が重要）`);
  } else if (gapMonths >= 3) {
    score -= 10;
    details.push(`${gapMonths}ヶ月間の投稿空白期間あり`);
  }

  // ── 投稿内容の質（25点）──
  // hasKeywordContent: 業種キーワードを含む投稿ありか
  // hasCasualOnly: 日常投稿のみか
  if (posts.hasKeywordContent) {
    score += 25;
  } else if (posts.hasCasualOnly !== undefined && posts.hasCasualOnly) {
    score += 5;
    details.push('投稿が日常報告中心（業種キーワードを含む集客投稿を推奨）');
  } else {
    // 情報がない場合は中間点
    score += 10;
  }

  // ── 投稿の種類多様性（25点）──
  let typeCount = 0;
  if (recentCount > 0) typeCount++;
  if (posts.hasOffer) typeCount++;
  if (posts.hasEvent) typeCount++;
  if (typeCount >= 3) { score += 25; }
  else if (typeCount >= 2) { score += 15; }
  else if (typeCount >= 1) { score += 5; }

  return { score: Math.max(Math.min(score, 100), 0), details };
}

/**
 * 軸⑤: 競争力（0-100）
 */
function scoreCompetitiveness(reviews, photos, competitors) {
  if (!competitors || competitors.length === 0) {
    return { score: 50, details: ['競合データが取得できなかったため中間スコアを適用'] };
  }

  let score = 0;
  const details = [];

  const myReviewCount = reviews.totalCount || 0;
  const myRating = reviews.averageRating || 0;
  const myPhotoCount = photos.totalCount || 0;

  const compReviewCounts = competitors.map(c => c.reviewCount).sort((a, b) => b - a);
  const compRatings = competitors.map(c => c.rating);

  // 口コミ件数の順位（35点）
  const reviewRank = compReviewCounts.filter(c => c > myReviewCount).length; // 自分より上の数
  const totalInGroup = competitors.length + 1;
  const reviewPercentile = 1 - (reviewRank / totalInGroup);
  if (reviewPercentile >= 0.8) { score += 35; }
  else if (reviewPercentile >= 0.6) { score += 25; }
  else if (reviewPercentile >= 0.4) { score += 15; details.push(`口コミ件数が競合と比べて中位（${myReviewCount}件）`); }
  else { score += 5; details.push(`口コミ件数が競合に比べて少ない（${myReviewCount}件）`); }

  // 平均評価の比較（35点）
  const avgCompRating = compRatings.reduce((a, b) => a + b, 0) / compRatings.length;
  if (myRating >= avgCompRating + 0.2) { score += 35; }
  else if (myRating >= avgCompRating - 0.1) { score += 20; }
  else { score += 5; details.push(`平均評価が競合平均(${avgCompRating.toFixed(1)})を下回り(${myRating})`); }

  // 写真枚数の比較（30点） — 競合の写真数が取得できない場合はスキップ
  const compWithPhotos = competitors.filter(c => c.photoCount);
  if (compWithPhotos.length > 0) {
    const avgCompPhotos = compWithPhotos.reduce((a, c) => a + c.photoCount, 0) / compWithPhotos.length;
    if (myPhotoCount >= avgCompPhotos) { score += 30; }
    else if (myPhotoCount >= avgCompPhotos * 0.5) { score += 15; }
    else { score += 5; details.push('写真枚数が競合に比べて少ない'); }
  } else {
    score += 15; // 比較不可のため中間
  }

  return { score: Math.min(score, 100), details };
}

/**
 * メイン分析関数
 */
function analyzeGBP(data) {
  // 業種判定
  const industryKey = detectIndustry(data.basic.category, data.basic.name);
  const benchmark = BENCHMARKS[industryKey];

  // 5軸スコアリング
  const axis1 = scoreBasicInfo(data.basic);
  const axis2 = scorePhotos(data.photos, benchmark);
  const axis3 = scoreReviews(data.reviews, benchmark);
  const axis4 = scorePosts(data.posts, benchmark);
  const axis5 = scoreCompetitiveness(data.reviews, data.photos, data.competitors);

  // 総合スコア（重み付き平均）
  const totalScore = Math.round(
    axis1.score * 0.25 +
    axis2.score * 0.20 +
    axis3.score * 0.30 +
    axis4.score * 0.15 +
    axis5.score * 0.10
  );

  const axes = [
    { id: 'basic', label: '基本情報の完全度', weight: 25, ...axis1, rank: scoreToRank(axis1.score) },
    { id: 'photos', label: '写真・動画の充実度', weight: 20, ...axis2, rank: scoreToRank(axis2.score) },
    { id: 'reviews', label: '口コミの力', weight: 30, ...axis3, rank: scoreToRank(axis3.score) },
    { id: 'posts', label: '投稿の活用度', weight: 15, ...axis4, rank: scoreToRank(axis4.score) },
    { id: 'competitive', label: '競争力', weight: 10, ...axis5, rank: scoreToRank(axis5.score) }
  ];

  // 伸びしろTOP3
  const improvementCandidates = axes
    .filter(a => a.score < 90) // S以外
    .sort((a, b) => {
      // 低スコア優先 → 同点なら重み順
      if (a.rank.rank !== b.rank.rank) {
        return a.score - b.score;
      }
      return b.weight - a.weight;
    });

  const top3 = improvementCandidates.slice(0, 3).map((axis, index) => ({
    rank: index + 1,
    axisLabel: axis.label,
    axisId: axis.id,
    currentRank: axis.rank.rank,
    currentScore: axis.score,
    details: axis.details,
    improvement: generateImprovement(axis, data, benchmark)
  }));

  // 機会損失メッセージ
  const opportunityMessage = generateOpportunityMessage(totalScore);

  return {
    businessName: data.basic.name,
    category: data.basic.category,
    industry: { key: industryKey, label: benchmark.label },
    totalScore,
    totalRank: scoreToRank(totalScore),
    axes,
    top3,
    opportunityMessage,
    competitors: data.competitors,
    analyzedAt: new Date().toISOString()
  };
}

/**
 * 改善提案の生成
 */
function generateImprovement(axis, data, benchmark) {
  const improvements = {
    basic: {
      summary: '基本情報の充実化',
      action: 'GBPの基本情報（説明文・属性・サービス項目）を充実させることで、検索での表示機会が広がる可能性があります',
      effort: '初期設定: 約1〜2時間',
      impact: '検索クエリとの関連性向上が期待できます'
    },
    photos: {
      summary: `写真の追加（現在${data.photos.totalCount}枚 → ${benchmark.photoTarget}枚以上を推奨）`,
      action: '外観・店内・商品/メニュー・スタッフ等のカテゴリ別に写真を追加することで、閲覧者の来店意欲を高める効果が期待できます',
      effort: 'プロ撮影: 半日〜1日 / 自社撮影: 2〜3時間＋月次追加',
      impact: '写真の充実はCTRの改善に寄与する傾向があります'
    },
    reviews: {
      summary: `口コミの強化（${data.reviews.totalCount}件 / 返信率 約${axis.replyRate || 0}%・参考値）`,
      action: '来店顧客への口コミ依頼の仕組み化と、全口コミへの丁寧な返信で信頼性の向上が見込まれます',
      effort: '返信体制構築: 初期2〜3時間＋日常運用1件5〜10分',
      impact: '口コミはローカル検索の重要なランキング要因の一つです'
    },
    posts: {
      summary: '投稿の定期更新',
      action: '最新情報・写真・イベント情報を定期的に投稿することで、GBPの活性度を高める効果が期待できます',
      effort: '投稿企画・写真撮影・文案作成: 1投稿あたり30〜60分、月4回程度',
      impact: '投稿頻度はGBPの「鮮度」として評価される傾向があります'
    },
    competitive: {
      summary: '競合との差別化',
      action: '口コミ・写真・投稿の各項目で競合を上回ることで、ローカルパックでの上位表示の可能性が高まります',
      effort: '総合的な取り組み: 月次で3〜5時間＋継続的な改善',
      impact: '同エリアの競合との相対的な位置づけの改善が期待できます'
    }
  };

  return improvements[axis.id] || improvements.basic;
}

/**
 * 機会損失メッセージの生成
 */
function generateOpportunityMessage(totalScore) {
  const rank = scoreToRank(totalScore);
  const messages = {
    S: '現時点で非常に高い水準で運用されています。微調整を加えることで、さらなる集客効果の最大化が見込まれます。',
    A: 'しっかりと運用されていますが、いくつかの項目を改善することで、さらなる集客効果が期待できます。',
    B: 'いくつかの項目に改善の余地があり、現在取りこぼしている可能性のある顧客層にアプローチできると考えられます。',
    C: '複数の重要項目に改善の余地があり、本来獲得できるはずの集客機会を逃している可能性があります。改善の優先度が高い状態です。',
    D: '基本的な設定から見直しが必要な状態です。本来の集客力を大きく下回っている可能性があり、早急な対応をおすすめします。'
  };
  return messages[rank.rank];
}

module.exports = { analyzeGBP, BENCHMARKS, RANKS, scoreToRank, detectIndustry };
