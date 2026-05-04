/**
 * render_review_report.js
 * 口コミ分析結果からHTMLレポートを生成
 * 
 * Usage:
 *   node render_review_report.js --input review_analysis_xxx.json --business-name "ビジネス名"
 */

const fs = require('fs');
const path = require('path');

// === JST日付生成 ===
function getJSTDateStr() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10).replace(/-/g, '');
}

// === 星アイコン生成 ===
function renderStars(rating) {
  return '★'.repeat(rating) + '☆'.repeat(5 - rating);
}

// === 評価分布バーチャート ===
function renderRatingChart(dist, total) {
  let html = '<div class="rating-chart">';
  for (let star = 5; star >= 1; star--) {
    const count = dist[star] || 0;
    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
    html += `
      <div class="rating-row">
        <span class="star-label">${renderStars(star)}</span>
        <div class="bar-container">
          <div class="bar" style="width: ${pct}%;"></div>
        </div>
        <span class="bar-count">${count}件 (${pct}%)</span>
      </div>`;
  }
  html += '</div>';
  return html;
}

// === 強み/弱みセクション ===
function renderInsightSection(items, emoji, title) {
  if (!items || items.length === 0) return `<div class="insight-section"><h3>${emoji} ${title}</h3><p class="no-data">該当するデータがありません</p></div>`;

  let html = `<div class="insight-section"><h3>${emoji} ${title}</h3>`;
  items.forEach((item, idx) => {
    const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉';
    html += `
      <div class="insight-card ${idx < 3 ? 'top3' : ''}">
        <div class="insight-header">
          <span class="insight-rank">${medal}</span>
          <span class="insight-theme">${item.theme}</span>
          <span class="insight-count">言及 ${item.mentionCount}件</span>
        </div>`;
    
    if (item.examples && item.examples.length > 0) {
      html += '<div class="insight-examples">';
      for (const ex of item.examples.slice(0, 2)) {
        html += `<blockquote class="review-quote">
          <span class="quote-rating">${renderStars(ex.rating)}</span>
          <span class="quote-name">${escapeHtml(ex.name)}</span>
          <p>「${escapeHtml(ex.excerpt)}」</p>
        </blockquote>`;
      }
      html += '</div>';
    }
    html += '</div>';
  });
  html += '</div>';
  return html;
}

// === テーマ分析マトリクス ===
function renderThemeMatrix(themes) {
  let html = `
    <table class="theme-matrix">
      <thead>
        <tr><th>テーマ</th><th>言及数</th><th>ポジティブ</th><th>ネガティブ</th><th>中立</th><th>評価</th></tr>
      </thead>
      <tbody>`;

  const sorted = Object.entries(themes)
    .filter(([, d]) => d.count > 0)
    .sort((a, b) => b[1].count - a[1].count);

  for (const [theme, data] of sorted) {
    const total = data.positive + data.negative + data.neutral;
    const posRate = total > 0 ? Math.round((data.positive / total) * 100) : 0;
    let evalIcon;
    if (posRate >= 80) evalIcon = '🟢 高評価';
    else if (posRate >= 50) evalIcon = '🟡 混在';
    else evalIcon = '🔴 要改善';

    html += `
      <tr>
        <td class="theme-name">${theme}</td>
        <td class="num">${data.count}</td>
        <td class="num positive">${data.positive}</td>
        <td class="num negative">${data.negative}</td>
        <td class="num neutral">${data.neutral}</td>
        <td>${evalIcon}</td>
      </tr>`;
  }

  html += '</tbody></table>';
  return html;
}

// === キーワードテーブル ===
function renderKeywordTable(keywords) {
  let html = '<div class="keyword-section"><div class="keyword-col">';
  html += '<h4>✅ 肯定的キーワード TOP10</h4><table class="keyword-table"><thead><tr><th>#</th><th>キーワード</th><th>出現回数</th></tr></thead><tbody>';
  keywords.positive.forEach((kw, i) => {
    html += `<tr><td>${i + 1}</td><td>${escapeHtml(kw.word)}</td><td>${kw.count}</td></tr>`;
  });
  html += '</tbody></table></div>';

  html += '<div class="keyword-col">';
  html += '<h4>⚠️ 否定的キーワード</h4>';
  if (keywords.negative.length > 0) {
    html += '<table class="keyword-table"><thead><tr><th>#</th><th>キーワード</th><th>出現回数</th></tr></thead><tbody>';
    keywords.negative.forEach((kw, i) => {
      html += `<tr><td>${i + 1}</td><td>${escapeHtml(kw.word)}</td><td>${kw.count}</td></tr>`;
    });
    html += '</tbody></table>';
  } else {
    html += '<p class="no-data">否定的キーワードは検出されませんでした</p>';
  }
  html += '</div></div>';
  return html;
}

// === HTMLエスケープ ===
function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// === メインHTML生成 ===
function renderReport(analysisPath, businessNameOverride) {
  const analysis = JSON.parse(fs.readFileSync(analysisPath, 'utf-8'));
  const businessName = businessNameOverride || analysis.businessName || 'Unknown';
  const rd = analysis.ratingDistribution;
  const sa = analysis.sentimentAnalysis;
  const oa = analysis.ownerReplyAnalysis;
  const tl = analysis.timeline;

  const metadata = analysis.metadata || {};
  const officialTotalCount = analysis.officialTotalCount || metadata.totalReviews || rd.total;
  const textReviewCount = analysis.textReviewCount || analysis.analyzedCount || rd.total;
  const avgRating = analysis.storeRating || metadata.averageRating || rd.average;
  const businessCategory = analysis.businessCategory || metadata.businessCategory || '';

  // エグゼクティブサマリー生成
  const topStrength = analysis.strengths[0]?.theme || '（分析中）';
  const topWeakness = analysis.weaknesses[0]?.theme || '特になし';
  const summary = `
    Googleマップ上の公式口コミ総件数 <strong>${officialTotalCount}件</strong>（星のみ含む全評価）、うちテキストコメントあり <strong>${textReviewCount}件</strong>を分析。
    総合評価 <strong>${avgRating}</strong>。
    最大の強みは「<strong>${topStrength}</strong>」。
    ${analysis.weaknesses.length > 0 ? `改善余地があるのは「<strong>${topWeakness}</strong>」。` : '目立った改善点はなし。'}
    ${oa.replyRate >= 80 ? 'オーナー返信率は良好。' : `オーナー返信率 ${oa.replyRate}% — 改善が推奨されます。`}
  `;

  const html = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(businessName)} 口コミ分析レポート</title>
  <style>
    :root {
      --primary: #1a2f5e;
      --primary-mid: #2a4a8a;
      --primary-light: #e8edf7;
      --accent: #c9a84c;
      --accent-light: #fdf6e3;
      --success: #1a6b3c;
      --success-light: #e8f4ed;
      --warning: #9a6200;
      --warning-light: #fdf3e0;
      --danger: #b3261e;
      --danger-light: #fdf0ef;
      --bg: #f4f5f8;
      --surface: #ffffff;
      --surface-alt: #eef0f5;
      --border: #d0d4e0;
      --text: #1a1e2e;
      --text-secondary: #5a6070;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Segoe UI', 'Noto Sans JP', 'Hiragino Sans', sans-serif;
      color: var(--text);
      background: var(--bg);
      line-height: 1.7;
      font-size: 14px;
    }

    .report-container {
      max-width: 820px;
      margin: 0 auto;
      padding: 40px 32px;
    }

    /* === ヘッダー === */
    .report-header {
      text-align: center;
      padding: 40px 32px;
      background: linear-gradient(150deg, #0f1e45 0%, #1a2f5e 50%, #22408c 100%);
      color: white;
      border-radius: 16px;
      margin-bottom: 32px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 8px 32px rgba(15,30,69,0.25);
    }
    .report-header::before {
      content: '';
      position: absolute;
      top: -40px; right: -40px;
      width: 200px; height: 200px;
      background: rgba(201,168,76,0.12);
      border-radius: 50%;
    }
    .report-header::after {
      content: '';
      position: absolute;
      bottom: -60px; left: -30px;
      width: 160px; height: 160px;
      background: rgba(255,255,255,0.05);
      border-radius: 50%;
    }
    .report-header h1 {
      font-size: 26px;
      font-weight: 700;
      margin-bottom: 6px;
      letter-spacing: 0.03em;
    }
    .report-header .gold-line {
      width: 48px;
      height: 2px;
      background: var(--accent);
      margin: 10px auto;
      border-radius: 2px;
    }
    .report-header .subtitle {
      font-size: 17px;
      opacity: 0.95;
      font-weight: 500;
    }
    .report-header .date {
      font-size: 12px;
      opacity: 0.65;
      margin-top: 10px;
      letter-spacing: 0.02em;
    }

    /* === サマリーカード === */
    .summary-card {
      background: var(--surface);
      border-left: 4px solid var(--primary);
      padding: 20px 24px;
      border-radius: 0 10px 10px 0;
      margin-bottom: 32px;
      font-size: 14px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .summary-card h2 {
      font-size: 15px;
      color: var(--primary);
      margin-bottom: 8px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }

    /* === スコアハイライト === */
    .score-highlight {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-bottom: 32px;
      flex-wrap: wrap;
    }
    .score-box {
      text-align: center;
      padding: 22px 20px;
      border-radius: 14px;
      min-width: 140px;
      flex: 1;
      box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    }
    .score-box.rating { background: var(--primary); color: white; }
    .score-box.count { background: var(--surface); border: 2px solid var(--primary-light); }
    .score-box.reply { background: var(--accent-light); border: 2px solid #e8d59a; }
    .score-box .score-value {
      font-size: 34px;
      font-weight: 700;
      display: block;
      letter-spacing: -0.01em;
    }
    .score-box.rating .score-value { color: white; }
    .score-box.count .score-value { color: var(--primary); }
    .score-box.reply .score-value { color: var(--warning); }
    .score-box .score-label {
      font-size: 11px;
      margin-top: 4px;
      letter-spacing: 0.03em;
    }
    .score-box.rating .score-label { color: rgba(255,255,255,0.75); }
    .score-box.count .score-label { color: var(--text-secondary); }
    .score-box.reply .score-label { color: var(--warning); }

    /* === セクション === */
    section { margin-bottom: 36px; }
    section h2 {
      font-size: 16px;
      font-weight: 700;
      color: var(--primary);
      border-bottom: 2px solid var(--primary);
      padding-bottom: 8px;
      margin-bottom: 16px;
      letter-spacing: 0.03em;
    }

    /* === 評価分布チャート === */
    .rating-chart { margin-bottom: 16px; }
    .rating-row {
      display: flex;
      align-items: center;
      margin-bottom: 6px;
      gap: 8px;
    }
    .star-label { font-size: 12px; width: 80px; color: var(--accent); flex-shrink: 0; }
    .bar-container {
      flex: 1;
      background: var(--surface-alt);
      border-radius: 6px;
      height: 20px;
      overflow: hidden;
    }
    .bar {
      height: 100%;
      background: linear-gradient(90deg, var(--primary) 0%, var(--primary-mid) 100%);
      border-radius: 6px;
      min-width: 2px;
    }
    .bar-count { font-size: 12px; color: var(--text-secondary); width: 80px; text-align: right; flex-shrink: 0; }

    /* === インサイトカード === */
    .insight-section h3 { font-size: 15px; margin-bottom: 12px; color: var(--primary); }
    .insight-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 12px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .insight-card.top3 { border-left: 4px solid var(--accent); }
    .insight-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
    .insight-rank { font-size: 20px; }
    .insight-theme { font-weight: 700; font-size: 15px; color: var(--primary); }
    .insight-count { color: var(--text-secondary); font-size: 12px; margin-left: auto; }
    .review-quote {
      background: var(--surface-alt);
      border-left: 3px solid var(--accent);
      padding: 8px 12px;
      margin: 6px 0;
      border-radius: 0 8px 8px 0;
      font-size: 13px;
    }
    .review-quote p { margin-top: 4px; color: var(--text); }
    .quote-rating { font-size: 11px; color: var(--accent); }
    .quote-name { font-size: 11px; color: var(--text-secondary); margin-left: 8px; }

    /* === テーブル === */
    table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 13px; }
    th { background: var(--primary); color: white; padding: 9px 12px; text-align: left; font-weight: 600; letter-spacing: 0.02em; }
    td { padding: 8px 12px; border-bottom: 1px solid var(--border); background: var(--surface); }
    tr:nth-child(even) td { background: var(--surface-alt); }
    td.num { text-align: center; }
    td.positive { color: var(--success); font-weight: 600; }
    td.negative { color: var(--danger); font-weight: 600; }
    td.neutral { color: var(--text-secondary); }
    .theme-name { font-weight: 600; color: var(--primary); }

    /* === キーワード === */
    .keyword-section { display: flex; gap: 24px; flex-wrap: wrap; }
    .keyword-col { flex: 1; min-width: 200px; }
    .keyword-col h4 { font-size: 14px; margin-bottom: 8px; color: var(--primary); font-weight: 700; }
    .keyword-table { font-size: 13px; }
    .no-data { color: var(--text-secondary); font-style: italic; font-size: 13px; }

    /* === オーナー返信 === */
    .reply-stats { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; }
    .reply-stat {
      background: var(--surface);
      border: 1px solid var(--border);
      padding: 14px 16px;
      border-radius: 10px;
      flex: 1;
      min-width: 120px;
      text-align: center;
      box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .reply-stat .value { font-size: 24px; font-weight: 700; color: var(--primary); }
    .reply-stat .label { font-size: 11px; color: var(--text-secondary); letter-spacing: 0.02em; }

    /* === フッター === */
    .report-footer {
      text-align: center;
      padding: 24px;
      color: var(--text-secondary);
      font-size: 12px;
      border-top: 1px solid var(--border);
      margin-top: 40px;
      letter-spacing: 0.02em;
    }

    /* === 低評価口コミ === */
    .low-rated-review {
      background: var(--danger-light);
      border-left: 3px solid var(--danger);
      padding: 12px 16px;
      margin-bottom: 8px;
      border-radius: 0 8px 8px 0;
    }
    .low-rated-header { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
    .low-rated-text { font-size: 13px; }

    @media print {
      body { font-size: 11px; background: white; }
      .report-container { padding: 20px; max-width: 100%; }
      .report-header { break-after: avoid; }
      section { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <div class="report-container">
    
    <header class="report-header">
      <h1>口コミ分析レポート</h1>
      <div class="gold-line"></div>
      <div class="subtitle">${escapeHtml(businessName)} 様</div>
      <div class="date">分析日: ${analysis.analyzedAt ? analysis.analyzedAt.substring(0, 10) : ''} ｜ 公式総件数: ${officialTotalCount}件（星のみ含む全評価）｜ テキストあり: ${textReviewCount}件（分析対象）</div>
    </header>

    <!-- エグゼクティブサマリー -->
    <div class="summary-card">
      <h2>📋 エグゼクティブサマリー</h2>
      <p>${summary}</p>
    </div>

    <!-- スコアハイライト -->
    <div class="score-highlight">
      <div class="score-box rating">
        <span class="score-value">${avgRating}</span>
        <span class="score-label">総合評価</span>
      </div>
      <div class="score-box count">
        <span class="score-value">${officialTotalCount}</span>
        <span class="score-label">公式総口コミ件数</span>
      </div>
      <div class="score-box reply">
        <span class="score-value">${oa.replyRate}%</span>
        <span class="score-label">返信率</span>
      </div>
    </div>

    <!-- 評価分布はGoogleマップ上で確認可能なため非表示 -->

    <!-- 強みTOP3 -->
    <section>
      <h2>💪 強み分析</h2>
      ${renderInsightSection(analysis.strengths, '💪', '口コミで評価されているポイント')}
    </section>

    <!-- 改善ポイント -->
    <section>
      <h2>📝 改善ポイント</h2>
      ${analysis.weaknesses.length > 0 
        ? renderInsightSection(analysis.weaknesses, '📝', '改善が見込まれるポイント')
        : '<p class="no-data">明確な改善ポイントは検出されませんでした（非常に高評価です）</p>'}
      ${analysis.lowRatedReviews.length > 0 ? `
        <h3 style="margin-top:16px;margin-bottom:8px;">⚠️ 低〜中評価の口コミ（${analysis.lowRatedReviews.length}件）</h3>
        ${analysis.lowRatedReviews.map(r => `
          <div class="low-rated-review">
            <div class="low-rated-header">
              <span>${renderStars(r.rating)} ${escapeHtml(r.name)}</span>
              <span>${escapeHtml(r.date)}</span>
            </div>
            <div class="low-rated-text">「${escapeHtml(r.text.length > 200 ? r.text.substring(0, 200) + '...' : r.text)}」</div>
          </div>`).join('')}
      ` : ''}
    </section>

    <!-- テーマ別分析 -->
    <section>
      <h2>🏷️ テーマ別分析マトリクス</h2>
      ${renderThemeMatrix(analysis.themeAnalysis)}
    </section>

    <!-- 頻出キーワード -->
    <section>
      <h2>🔑 頻出キーワード</h2>
      ${renderKeywordTable(analysis.keywords)}
    </section>

    <!-- オーナー返信分析 -->
    <section>
      <h2>💬 オーナー返信分析</h2>
      <div class="reply-stats">
        <div class="reply-stat">
          <div class="value">${oa.withReply}/${oa.total}</div>
          <div class="label">返信済み/全体</div>
        </div>
        <div class="reply-stat">
          <div class="value">${oa.replyRate}%</div>
          <div class="label">返信率</div>
        </div>
        <div class="reply-stat">
          <div class="value">${oa.quality}</div>
          <div class="label">評価</div>
        </div>
      </div>
      ${oa.templateEstimate > 0 ? `<p style="font-size:13px;color:var(--text-secondary);">※ 推定テンプレ返信: ${oa.templateEstimate}件 / 個別対応: ${oa.personalEstimate}件</p>` : ''}
    </section>

    <!-- 時系列分析はデータ不正確のため非表示 -->

    ${analysis.benchmark ? `
    <!-- ベンチマーク比較 -->
    <section>
      <h2>🏆 競合ベンチマーク比較</h2>
      <table>
        <thead>
          <tr><th>項目</th><th>${escapeHtml(businessName)}</th><th>${escapeHtml(analysis.benchmark.businessName)}</th></tr>
        </thead>
        <tbody>
          <tr><td>平均評価</td><td class="num">${rd.average}</td><td class="num">${analysis.benchmark.rating.average}</td></tr>
          <tr><td>口コミ件数</td><td class="num">${rd.total}</td><td class="num">${analysis.benchmark.rating.total}</td></tr>
          <tr><td>返信率</td><td class="num">${oa.replyRate}%</td><td class="num">${analysis.benchmark.ownerReply.replyRate}%</td></tr>
        </tbody>
      </table>
    </section>
    ` : ''}

    <!-- フッター -->
    <footer class="report-footer">
      <p>本レポートはGoogleマップ上の公開口コミ情報に基づく分析です。</p>
      <p>口コミ分析・返信代行・GBP運用代行のご相談は、お気軽にお問い合わせください。</p>
    </footer>

  </div>
</body>
</html>`;

  // 出力
  const dateStr = getJSTDateStr();
  const clientId = analysis.clientId || (analysis.businessName || 'unknown').toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_');
  const outputName = `review_report_${clientId}_${dateStr}.html`;
  const outputPath = path.join(__dirname, '..', outputName);

  fs.writeFileSync(outputPath, html, 'utf-8');
  console.log(`✅ HTMLレポート生成完了 → ${outputPath}`);

  return outputPath;
}

// === CLI実行 ===
if (require.main === module) {
  const args = process.argv.slice(2);
  const inputIdx = args.indexOf('--input');
  const nameIdx = args.indexOf('--business-name');

  if (inputIdx === -1) {
    console.error('Usage: node render_review_report.js --input <analysis.json> [--business-name "ビジネス名"]');
    process.exit(1);
  }

  const inputPath = args[inputIdx + 1];
  const businessName = nameIdx !== -1 ? args[nameIdx + 1] : null;

  renderReport(inputPath, businessName);
}

module.exports = { renderReport };
