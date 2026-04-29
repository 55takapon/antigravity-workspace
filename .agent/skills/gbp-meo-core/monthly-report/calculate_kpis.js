/**
 * KPI計算 — 前月比・アクション率・推奨アクション自動判定
 */

/**
 * 前月比を計算する
 * @param {number|null} current - 当月値
 * @param {number|null} previous - 前月値
 * @returns {Object} { value, percent, trend }
 */
function calcDelta(current, previous) {
  if (current === null || current === undefined) return { value: null, percent: null, trend: '—' };
  if (previous === null || previous === undefined || previous === 0) {
    return { value: current, percent: null, trend: 'new' };
  }

  const delta = current - previous;
  const percent = Math.round((delta / previous) * 100);
  const trend = delta > 0 ? 'up' : delta < 0 ? 'down' : 'flat';

  return { value: delta, percent, trend };
}

/**
 * メインKPIをまとめる
 */
function calculateMainKPIs(data) {
  const { performance, prevPerformance } = data;

  const views = performance['閲覧数（合計）'] ?? null;
  const clicks = performance['ウェブサイトクリック数'] ?? null;
  const calls = performance['電話発信数'] ?? null;
  const routes = performance['ルート検索数'] ?? null;

  const prevViews = prevPerformance['閲覧数（合計）'] ?? null;
  const prevClicks = prevPerformance['ウェブサイトクリック数'] ?? null;
  const prevCalls = prevPerformance['電話発信数'] ?? null;
  const prevRoutes = prevPerformance['ルート検索数'] ?? null;

  return {
    views: {
      label: '閲覧数',
      icon: '👁',
      value: views,
      delta: calcDelta(views, prevViews),
    },
    clicks: {
      label: 'Webクリック',
      icon: '🖱',
      value: clicks,
      delta: calcDelta(clicks, prevClicks),
    },
    calls: {
      label: '電話発信',
      icon: '📞',
      value: calls,
      delta: calcDelta(calls, prevCalls),
    },
    routes: {
      label: 'ルート検索',
      icon: '📍',
      value: routes,
      delta: calcDelta(routes, prevRoutes),
    },
  };
}

/**
 * アクション率を計算する
 */
function calculateActionRates(performance) {
  const views = performance['閲覧数（合計）'];
  if (!views || views === 0) return { clickRate: null, callRate: null, routeRate: null, totalRate: null };

  const clicks = performance['ウェブサイトクリック数'] || 0;
  const calls = performance['電話発信数'] || 0;
  const routes = performance['ルート検索数'] || 0;

  const clickRate = ((clicks / views) * 100).toFixed(1);
  const callRate = ((calls / views) * 100).toFixed(1);
  const routeRate = ((routes / views) * 100).toFixed(1);
  const totalRate = (((clicks + calls + routes) / views) * 100).toFixed(1);

  return {
    clickRate: parseFloat(clickRate),
    callRate: parseFloat(callRate),
    routeRate: parseFloat(routeRate),
    totalRate: parseFloat(totalRate),
  };
}

/**
 * 推奨アクションを自動判定する（最大3件）
 * @param {Object} data - レポートデータ
 * @param {string[]} skipRules - 除外するルールID一覧
 * @param {number|null} targetReviewCount - 目標口コミ数
 * 
 * ルールID一覧:
 *   views_down      — 閲覧数の前月比減少
 *   reviews         — 口コミ件数不足（10件未満）
 *   reviews_target  — 口コミが目標に未達
 *   reply_rate      — 口コミ返信率
 *   posts           — 投稿数不足
 *   calls           — 電話発信率
 */
function generateRecommendations(data, skipRules = [], targetReviewCount = null) {
  const recommendations = [];
  const { performance, prevPerformance, reviews, posts } = data;
  const skip = new Set(skipRules);

  // 1. 閲覧数の減少チェック (ID: views_down)
  if (!skip.has('views_down')) {
    const views = performance['閲覧数（合計）'];
    const prevViews = prevPerformance['閲覧数（合計）'];
    if (views && prevViews && views < prevViews * 0.9) {
      recommendations.push({
        priority: '★★★',
        action: '閲覧数が前月比10%以上減少しています',
        detail: '投稿頻度を増やしてGBPの「鮮度」を回復させましょう。季節イベントに連動した投稿も効果的です。',
      });
    }
  }

  // 2. 口コミ件数チェック (ID: reviews) — 10件未満の場合
  if (!skip.has('reviews')) {
    const reviewCount = reviews['口コミ総数（累計）'];
    if (reviewCount !== null && reviewCount !== undefined && reviewCount < 10) {
      recommendations.push({
        priority: '★★★',
        action: `口コミ総数が${reviewCount}件です（10件以上推奨）`,
        detail: '口コミ10件未満はユーザーの信頼ラインを下回ります。サービス提供後のタイミングで口コミ依頼の仕組みを構築しましょう。',
      });
    }
  }

  // 2b. 口コミ目標未達チェック (ID: reviews_target) — 目標の半分未満の場合
  if (!skip.has('reviews_target') && targetReviewCount) {
    const reviewCount = reviews['口コミ総数（累計）'];
    if (reviewCount !== null && reviewCount !== undefined && reviewCount >= 10 && reviewCount < targetReviewCount) {
      const views = performance['閲覧数（合計）'];
      const viewsNote = views && views >= 1000
        ? '閲覧数は十分にあるため、口コミを増やすことで問い合わせ増が見込めます。'
        : '口コミ数の増加はローカル検索のランキング改善に直結します。';
      recommendations.push({
        priority: '★★★',
        action: `口コミ${reviewCount}件 → 目標${targetReviewCount}件（口コミ促進を強化）`,
        detail: `${viewsNote}来店時・サービス提供後のタイミングで口コミ依頼の仕組みを構築しましょう。`,
      });
    }
  }

  // 3. 口コミ返信率チェック (ID: reply_rate)
  if (!skip.has('reply_rate')) {
    const replyRate = reviews['返信率（%）'];
    if (replyRate !== null && replyRate !== undefined && replyRate < 100) {
      recommendations.push({
        priority: '★★★',
        action: `口コミ返信率が${replyRate}%です（100%推奨）`,
        detail: '未返信の口コミに48時間以内に返信しましょう。口コミ返信率はローカル検索のランキング要因です。',
      });
    }
  }

  // 4. 投稿数チェック (ID: posts) — 業種別の閾値で判定
  if (!skip.has('posts')) {
    const postCount = posts['当月投稿数'];
    // 業種別の投稿頻度目安（gbp-meo-core/SKILL.md セクション8.7準拠）
    const industry = (data.header && data.header.industry) || '';
    const postThresholds = {
      '飲食':   { min: 8, label: '月8件=週2回' },
      '居酒屋': { min: 8, label: '月8件=週2回' },
      '美容':   { min: 8, label: '月8件=週2回' },
      'エステ': { min: 8, label: '月8件=週2回' },
      'ネイル': { min: 8, label: '月8件=週2回' },
      '歯科':   { min: 8, label: '月8件=週2回' },
      'クリニック': { min: 8, label: '月8件=週2回' },
      '整体':   { min: 8, label: '月8件=週2回' },
      '施術':   { min: 8, label: '月8件=週2回' },
      '塾':     { min: 8, label: '月8件=週2回' },
      '学習':   { min: 8, label: '月8件=週2回' },
      '士業':   { min: 4, label: '月4件=週1回' },
      '司法書士': { min: 4, label: '月4件=週1回' },
      '税理士': { min: 4, label: '月4件=週1回' },
      '行政書士': { min: 4, label: '月4件=週1回' },
      '弁護士': { min: 4, label: '月4件=週1回' },
      '不動産': { min: 8, label: '月8件=週2回' },
      '工務店': { min: 6, label: '月6件=週1.5回' },
      'リフォーム': { min: 6, label: '月6件=週1.5回' },
      '小売':   { min: 8, label: '月8件=週2回' },
    };
    // 業種名に部分一致でマッチ（デフォルトは月4件）
    let threshold = { min: 4, label: '月4件=週1回' };
    for (const [key, val] of Object.entries(postThresholds)) {
      if (industry.includes(key)) { threshold = val; break; }
    }
    if (postCount !== null && postCount !== undefined && postCount < threshold.min) {
      // 士業系で投稿が実施されている場合（>=1件）は肯定的メッセージ
      // （競合が投稿ゼロの業界では投稿しているだけで優位）
      const isLegal = ['士業','司法書士','税理士','行政書士','弁護士'].some(k => industry.includes(k));
      if (isLegal && postCount >= 1) {
        recommendations.push({
          priority: '★★☆',
          action: `当月の投稿が${postCount}件です`,
          detail: '定期的に投稿していくことで、GBPの「活性度」が向上し、検索表示回数の改善が期待できます。',
        });
      } else {
        recommendations.push({
          priority: '★★☆',
          action: `当月の投稿が${postCount}件です（${threshold.label}推奨）`,
          detail: '投稿頻度を上げることでGBPの「活性度」が向上し、検索表示回数の改善が期待できます。',
        });
      }
    }
  }

  // 5. 電話発信率チェック (ID: calls)
  if (!skip.has('calls')) {
    const rates = calculateActionRates(performance);
    if (rates.callRate !== null && rates.callRate < 2) {
      recommendations.push({
        priority: '★★☆',
        action: `電話発信率が${rates.callRate}%と低めです`,
        detail: '「電話で相談OK」「無料相談受付中」などのCTAを投稿に含めることで改善が期待できます。',
      });
    }
  }

  // 優先度順にソート
  recommendations.sort((a, b) => b.priority.localeCompare(a.priority));

  return recommendations.slice(0, 3); // 最大3件
}

/**
 * 過去6ヶ月のトレンドデータを抽出する（グラフ用）
 */
function extractTrend(allData, currentMonth, metricKey) {
  const trend = [];
  const months = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];

  for (let i = 5; i >= 0; i--) {
    const m = currentMonth - i;
    if (m < 1) continue;
    const val = allData[m] ? allData[m][metricKey] : null;
    trend.push({ month: months[m - 1], value: val });
  }

  return trend;
}

module.exports = {
  calcDelta,
  calculateMainKPIs,
  calculateActionRates,
  generateRecommendations,
  extractTrend,
};
