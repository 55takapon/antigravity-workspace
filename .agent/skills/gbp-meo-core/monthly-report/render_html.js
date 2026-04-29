/**
 * HTMLテンプレート — GBP月次パフォーマンスレポート
 * 診断レポートと同じネイビー系配色。ロゴ・連絡先なし。
 */

/**
 * 数値をフォーマットする（カンマ区切り）
 */
function formatNumber(n) {
  if (n === null || n === undefined) return '—';
  return n.toLocaleString('ja-JP');
}

/**
 * 前月比の表示を生成
 */
function deltaHTML(delta) {
  if (!delta || delta.percent === null) return '';
  const color = delta.trend === 'up' ? '#22c55e' : delta.trend === 'down' ? '#ef4444' : '#94a3b8';
  const arrow = delta.trend === 'up' ? '▲' : delta.trend === 'down' ? '▼' : '→';
  return `<span style="color:${color};font-size:13px;font-weight:600">${arrow}${Math.abs(delta.percent)}%</span>`;
}

/**
 * SVGミニ折れ線グラフを生成
 */
function renderSVGChart(trendData, color = '#3b82f6') {
  if (!trendData || trendData.length === 0) return '';

  const values = trendData.map(d => d.value).filter(v => v !== null && v !== undefined);
  if (values.length < 2) return '<div style="color:#94a3b8;font-size:12px;text-align:center;padding:20px">データ不足（2ヶ月以上必要）</div>';

  const width = 680;
  const height = 140;
  const padding = { top: 20, right: 20, bottom: 35, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const maxVal = Math.max(...values) * 1.1 || 1;
  const minVal = 0;

  const points = trendData
    .map((d, i) => {
      if (d.value === null || d.value === undefined) return null;
      const x = padding.left + (i / (trendData.length - 1)) * chartW;
      const y = padding.top + chartH - ((d.value - minVal) / (maxVal - minVal)) * chartH;
      return { x, y, value: d.value, month: d.month };
    })
    .filter(Boolean);

  const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  // グラデーション塗りつぶし用パス
  const areaPath = pathData +
    ` L ${points[points.length - 1].x} ${padding.top + chartH}` +
    ` L ${points[0].x} ${padding.top + chartH} Z`;

  return `
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="display:block;margin:0 auto">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${color}" stop-opacity="0.2"/>
          <stop offset="100%" stop-color="${color}" stop-opacity="0.02"/>
        </linearGradient>
      </defs>
      <!-- Grid lines -->
      ${[0, 0.25, 0.5, 0.75, 1].map(ratio => {
        const y = padding.top + chartH * (1 - ratio);
        const val = Math.round(minVal + (maxVal - minVal) * ratio);
        return `
          <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#e2e8f0" stroke-width="1"/>
          <text x="${padding.left - 8}" y="${y + 4}" text-anchor="end" fill="#94a3b8" font-size="10">${formatNumber(val)}</text>
        `;
      }).join('')}
      <!-- Area fill -->
      <path d="${areaPath}" fill="url(#areaGrad)"/>
      <!-- Line -->
      <path d="${pathData}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>
      <!-- Points & labels -->
      ${points.map(p => `
        <circle cx="${p.x}" cy="${p.y}" r="4" fill="white" stroke="${color}" stroke-width="2"/>
        <text x="${p.x}" y="${padding.top + chartH + 20}" text-anchor="middle" fill="#64748b" font-size="11">${p.month}</text>
        <text x="${p.x}" y="${p.y - 10}" text-anchor="middle" fill="#1a1a2e" font-size="10" font-weight="600">${formatNumber(p.value)}</text>
      `).join('')}
    </svg>`;
}

/**
 * SVG棒グラフを生成（口コミ数用）
 */
function renderBarChart(trendData, color = '#f59e0b') {
  if (!trendData || trendData.length === 0) return '';

  const values = trendData.map(d => d.value).filter(v => v !== null && v !== undefined);
  if (values.length < 1) return '<div style="color:#94a3b8;font-size:12px;text-align:center;padding:20px">データなし</div>';

  const width = 680;
  const height = 140;
  const padding = { top: 20, right: 20, bottom: 35, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const maxVal = Math.max(...values) * 1.2 || 1;
  const barCount = trendData.length;
  const barWidth = Math.min(40, (chartW / barCount) * 0.6);
  const barGap = (chartW - barWidth * barCount) / (barCount + 1);

  return `
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="display:block;margin:0 auto">
      <!-- Grid lines -->
      ${[0, 0.5, 1].map(ratio => {
        const y = padding.top + chartH * (1 - ratio);
        const val = Math.round(maxVal * ratio);
        return `
          <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#e2e8f0" stroke-width="1"/>
          <text x="${padding.left - 8}" y="${y + 4}" text-anchor="end" fill="#94a3b8" font-size="10">${val}</text>
        `;
      }).join('')}
      <!-- Bars -->
      ${trendData.map((d, i) => {
        const x = padding.left + barGap * (i + 1) + barWidth * i;
        const val = d.value !== null && d.value !== undefined ? d.value : 0;
        const barH = (val / maxVal) * chartH;
        const y = padding.top + chartH - barH;
        return `
          <rect x="${x}" y="${y}" width="${barWidth}" height="${barH}" fill="${color}" rx="3"/>
          <text x="${x + barWidth / 2}" y="${y - 5}" text-anchor="middle" fill="#1a1a2e" font-size="10" font-weight="600">${val}</text>
          <text x="${x + barWidth / 2}" y="${padding.top + chartH + 18}" text-anchor="middle" fill="#64748b" font-size="11">${d.month}</text>
        `;
      }).join('')}
    </svg>`;
}

/**
 * メインHTMLテンプレートを生成する
 */
function renderHTML(reportData) {
  const { header, month, mainKPIs, reviews, posts, queries, competitors, actionLog, recommendations, trendViews, trendReviews, targetReviewCount, customMessage } = reportData;

  const monthNames = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];
  const monthLabel = monthNames[month - 1] || `${month}月`;
  const now = new Date();
  const dateStr = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 作成`;

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GBP月次レポート — ${header.clientName}（${monthLabel}）</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=Noto+Sans+JP:wght@400;500;700;900&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
      color: #1a1a2e;
      background: #f8f9fa;
      line-height: 1.7;
      font-size: 13px;
      -webkit-font-smoothing: antialiased;
    }

    .report { max-width: 800px; margin: 0 auto; background: white; }

    /* Header */
    .header {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      color: white;
      padding: 28px 40px;
      text-align: center;
    }
    .header h1 { font-size: 24px; font-weight: 900; letter-spacing: 2px; margin-bottom: 6px; }
    .header .client { font-size: 20px; font-weight: 700; color: #e2e8f0; }
    .header .meta { font-size: 12px; color: #94a3b8; margin-top: 8px; }

    /* Section */
    .section { padding: 20px 40px; border-bottom: 1px solid #e2e8f0; }
    .section:last-child { border-bottom: none; }
    .section-title {
      font-size: 16px; font-weight: 700; color: #1a1a2e;
      margin-bottom: 16px; padding-left: 12px;
      border-left: 4px solid #3b82f6;
    }

    /* KPI Cards */
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .kpi-card {
      background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
      padding: 16px; text-align: center;
    }
    .kpi-icon { font-size: 20px; margin-bottom: 4px; }
    .kpi-value { font-size: 28px; font-weight: 900; color: #1a1a2e; line-height: 1.2; }
    .kpi-label { font-size: 11px; color: #64748b; margin-top: 2px; }
    .kpi-delta { margin-top: 4px; }

    /* Tables */
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { background: #1a1a2e; color: white; padding: 8px 12px; text-align: left; font-weight: 500; }
    td { padding: 8px 12px; border-bottom: 1px solid #e2e8f0; }
    tr.highlight { background: #eff6ff; font-weight: 600; }

    /* Review summary */
    .review-bar {
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
      background: #f8fafc; border-radius: 12px; padding: 16px;
      border: 1px solid #e2e8f0;
    }
    .review-item { text-align: center; }
    .review-value { font-size: 22px; font-weight: 900; }
    .review-label { font-size: 11px; color: #64748b; }
    .review-target { font-size: 11px; color: #3b82f6; margin-top: 2px; }

    /* Recommendations */
    .rec-item {
      display: grid; grid-template-columns: 50px 1fr;
      gap: 8px; padding: 12px 0; border-bottom: 1px solid #f1f5f9;
    }
    .rec-priority { font-size: 14px; text-align: center; line-height: 1.8; }
    .rec-action { font-weight: 600; font-size: 13px; }
    .rec-detail { font-size: 12px; color: #64748b; margin-top: 2px; }

    /* Action Log */
    .action-log {
      background: #f8fafc; border-radius: 12px; padding: 16px 20px;
      border: 1px solid #e2e8f0; font-size: 13px; line-height: 1.8;
    }
    .action-log dt { font-weight: 600; margin-top: 8px; }
    .action-log dd { color: #475569; }

    /* Custom Message */
    .custom-message {
      background: #f0f9ff; border-radius: 12px; padding: 16px 20px;
      border: 1px solid #bae6fd; font-size: 13px; line-height: 1.8;
      color: #0c4a6e;
    }

    /* Footer */
    .footer {
      background: #1a1a2e; color: #e2e8f0; padding: 20px 40px;
      text-align: center; font-size: 11px; color: #94a3b8;
    }

    /* Print */
    @page { size: A4; margin: 12mm 0; }
    @media print {
      * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
      body { background: white; margin: 0; padding: 0; }
      .report { max-width: 100%; }
      .header, .section, .kpi-grid, .review-bar, table, .rec-item, .footer {
        break-inside: avoid; page-break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <div class="report">

    <!-- Header -->
    <div class="header">
      <h1>Googleビジネスプロフィール月次レポート</h1>
      <div class="client">${header.clientName} 様</div>
      <div class="meta">${monthLabel}度 ｜ ${header.industry || header.category || ''} ｜ ${dateStr}</div>
    </div>

    <!-- KPI Summary -->
    <div class="section">
      <div class="section-title">📊 主要KPIサマリー</div>
      <div class="kpi-grid">
        ${Object.values(mainKPIs).map(kpi => `
        <div class="kpi-card">
          <div class="kpi-icon">${kpi.icon}</div>
          <div class="kpi-value">${formatNumber(kpi.value)}</div>
          <div class="kpi-label">${kpi.label}</div>
          <div class="kpi-delta">${deltaHTML(kpi.delta)}</div>
        </div>`).join('')}
      </div>
    </div>

    <!-- 閲覧数の推移 -->
    <div class="section">
      <div class="section-title">📈 閲覧数の推移</div>
      ${renderSVGChart(trendViews)}
    </div>

    <!-- 口コミ数の推移 -->
    <div class="section">
      <div class="section-title">💬 口コミ数の推移</div>
      ${renderBarChart(trendReviews)}
    </div>

    <!-- 口コミ・投稿 -->
    <div class="section">
      <div class="section-title">⭐ 口コミ・投稿</div>
      <div class="review-bar">
        <div class="review-item">
          <div class="review-value">${formatNumber(reviews['口コミ総数（累計）'])}</div>
          <div class="review-label">口コミ総数</div>
          ${targetReviewCount ? `<div class="review-target">目標: ${targetReviewCount}件</div>` : ''}
        </div>
        <div class="review-item">
          <div class="review-value">${reviews['平均評価（★）'] !== null ? '★' + reviews['平均評価（★）'] : '—'}</div>
          <div class="review-label">平均評価</div>
        </div>
        <div class="review-item">
          <div class="review-value">${formatNumber(posts['当月投稿数'])}</div>
          <div class="review-label">当月投稿数</div>
        </div>
      </div>
    </div>

    <!-- Search Queries -->
    ${queries.length > 0 ? `
    <div class="section">
      <div class="section-title">🔍 検索クエリ TOP5</div>
      <table>
        <thead><tr><th>#</th><th>キーワード</th><th>表示回数</th></tr></thead>
        <tbody>
          ${queries.slice(0, 5).map(q => `
          <tr>
            <td>${q.rank}</td>
            <td>${q.keyword}</td>
            <td>${formatNumber(q.count)}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>` : ''}

    <!-- ベンチマーク参考（上位3社＋自社） -->
    ${competitors.length > 0 ? (() => {
      const self = competitors.filter(c => c.isSelf);
      const others = competitors.filter(c => !c.isSelf)
        .sort((a, b) => (b.reviewCount || 0) - (a.reviewCount || 0))
        .slice(0, 3);
      const display = [...others, ...self];
      return `
    <div class="section">
      <div class="section-title">📊 ベンチマーク参考</div>
      <table>
        <thead><tr><th>店舗名</th><th>口コミ数</th><th>評価</th></tr></thead>
        <tbody>
          ${display.map(c => `
          <tr${c.isSelf ? ' class="highlight"' : ''}>
            <td>${c.isSelf ? '★ ' : ''}${c.name}</td>
            <td>${c.reviewCount !== null ? c.reviewCount + '件' : '—'}</td>
            <td>${c.rating !== null ? c.rating : '—'}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
    })() : ''}

    <!-- Action Log -->
    ${actionLog.actions ? `
    <div class="section">
      <div class="section-title">📋 当月の施策と成果</div>
      <div class="action-log">
        <dt>実施した施策</dt>
        <dd>${actionLog.actions}</dd>
        ${actionLog.results ? `<dt>成果・気づき</dt><dd>${actionLog.results}</dd>` : ''}
      </div>
    </div>` : ''}

    <!-- Recommendations -->
    ${recommendations.length > 0 ? `
    <div class="section">
      <div class="section-title">💡 翌月の推奨アクション</div>
      ${recommendations.map(r => `
      <div class="rec-item">
        <div class="rec-priority">${r.priority}</div>
        <div>
          <div class="rec-action">${r.action}</div>
          <div class="rec-detail">${r.detail}</div>
        </div>
      </div>`).join('')}
    </div>` : ''}

    <!-- 個別メッセージ -->
    <div class="section" id="custom-message-section">
      <div class="section-title">✉️ 担当者より</div>
      <div class="custom-message">${customMessage || '※ここにHTMLファイル上で個別メッセージを追記できます'}</div>
    </div>

    <!-- Footer -->
    <div class="footer">
      本レポートはGoogleビジネスプロフィールの管理画面データに基づいて作成されています。<br>
      データの正確性はGoogleの提供する情報に依存します。
    </div>

  </div>
</body>
</html>`;
}

module.exports = { renderHTML, renderSVGChart, formatNumber };
