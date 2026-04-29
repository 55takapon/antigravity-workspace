/**
 * GBP診断レポート生成
 * 分析結果からHTML（PDF化用）とNotebookLM用テキストを生成
 */

/**
 * プログレスバーを生成（テキスト）
 */
function progressBar(score, width = 10) {
  const filled = Math.round(score / 100 * width);
  return '█'.repeat(filled) + '░'.repeat(width - filled);
}

/**
 * ① HTML レポート生成（PDF化用）
 */
function generateHTML(result, data) {
  const { businessName, category, totalScore, totalRank, axes, top3, opportunityMessage, competitors: allCompetitors, industry } = result;
  // レポート表示は上位3社（口コミ数順）
  const competitors = [...allCompetitors].sort((a, b) => (b.reviewCount || 0) - (a.reviewCount || 0)).slice(0, 3);
  const date = new Date().toLocaleDateString('ja-JP', { year: 'numeric', month: 'long', day: 'numeric' });

  const medalEmojis = ['🥇', '🥈', '🥉'];
  const rankColors = { S: '#22c55e', A: '#3b82f6', B: '#eab308', C: '#f97316', D: '#ef4444' };

  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Googleビジネスプロフィール診断レポート — ${businessName}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=Noto+Sans+JP:wght@400;500;700;900&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
      color: #1a1a2e;
      background: #f8f9fa;
      line-height: 1.7;
      font-size: 14px;
      -webkit-font-smoothing: antialiased;
    }

    .report {
      max-width: 800px;
      margin: 0 auto;
      background: white;
    }

    /* Header */
    .header {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      color: white;
      padding: 28px 40px;
      text-align: center;
    }
    .header h1 {
      font-size: 28px;
      font-weight: 900;
      letter-spacing: 2px;
      margin-bottom: 8px;
    }
    .header .subtitle {
      font-size: 20px;
      font-weight: 700;
      color: #e2e8f0;
      margin-bottom: 16px;
    }
    .header .date {
      font-size: 13px;
      color: #94a3b8;
    }
    .header .disclaimer {
      font-size: 11px;
      color: #64748b;
      margin-top: 12px;
    }

    /* Sections */
    .section {
      padding: 20px 40px;
      border-bottom: 1px solid #e2e8f0;
    }
    .section:last-child { border-bottom: none; }
    .section-title {
      font-size: 18px;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 20px;
      padding-left: 12px;
      border-left: 4px solid #3b82f6;
    }

    /* Total Score */
    .total-score {
      text-align: center;
      padding: 24px 40px;
      background: #f1f5f9;
    }
    .total-rank {
      font-size: 72px;
      font-weight: 900;
      color: ${rankColors[totalRank.rank]};
      line-height: 1;
    }
    .total-label {
      font-size: 16px;
      color: #64748b;
      margin-top: 8px;
    }
    .total-desc {
      font-size: 14px;
      color: #475569;
      margin-top: 12px;
    }

    /* Axis Scores */
    .axis-grid {
      display: grid;
      gap: 12px;
    }
    .axis-row {
      display: grid;
      grid-template-columns: 160px 40px 1fr 40px;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
    }
    .axis-label { font-weight: 500; font-size: 13px; }
    .axis-rank {
      font-weight: 900;
      font-size: 18px;
      text-align: center;
    }
    .axis-bar-container {
      background: #e2e8f0;
      border-radius: 8px;
      height: 24px;
      overflow: hidden;
    }
    .axis-bar {
      height: 100%;
      border-radius: 8px;
      transition: width 0.3s;
    }
    .axis-score { font-size: 13px; color: #64748b; text-align: right; }

    /* Opportunity */
    .opportunity {
      background: #fef2f2;
      border-left: 4px solid #ef4444;
      padding: 20px 24px;
      border-radius: 0 8px 8px 0;
      line-height: 1.8;
    }
    .opportunity.good {
      background: #f0fdf4;
      border-left-color: #22c55e;
    }

    /* Top 3 */
    .top3-item {
      background: #f8fafc;
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 16px;
      border: 1px solid #e2e8f0;
    }
    .top3-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .top3-medal { font-size: 28px; }
    .top3-title { font-size: 16px; font-weight: 700; }
    .top3-body { font-size: 13px; color: #475569; }
    .top3-body dt {
      font-weight: 600;
      color: #1a1a2e;
      margin-top: 8px;
    }
    .top3-body dd { margin-left: 0; margin-top: 2px; }

    /* Competitor Table */
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th {
      background: #1a1a2e;
      color: white;
      padding: 10px 12px;
      text-align: left;
      font-weight: 500;
    }
    td {
      padding: 10px 12px;
      border-bottom: 1px solid #e2e8f0;
    }
    tr.highlight {
      background: #eff6ff;
      font-weight: 600;
    }

    /* Action List */
    .action-item {
      display: grid;
      grid-template-columns: 1fr 80px 120px;
      gap: 8px;
      padding: 10px 0;
      border-bottom: 1px solid #f1f5f9;
      font-size: 13px;
    }
    .action-difficulty { text-align: center; }
    .action-effort { text-align: right; color: #64748b; font-size: 12px; }

    /* Footer */
    .footer {
      background: #1a1a2e;
      color: #e2e8f0;
      padding: 32px 40px;
      text-align: center;
    }
    .footer .cta {
      font-size: 15px;
      line-height: 2;
      margin-bottom: 20px;
    }
    .footer .contact {
      font-size: 12px;
      color: #94a3b8;
    }

    /* Print / PDF */
    @page {
      size: A4;
      margin: 12mm 0 12mm 0;
    }
    @media print {
      * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
      body { background: white; margin: 0; padding: 0; font-size: 13px; }
      .report { max-width: 100%; box-shadow: none; }

      /* ページ切れ防止 */
      .header { break-inside: avoid; page-break-inside: avoid; }
      .total-score { break-inside: avoid; page-break-inside: avoid; }
      .section { break-inside: avoid; page-break-inside: avoid; }
      .top3-item { break-inside: avoid; page-break-inside: avoid; }
      .axis-grid { break-inside: avoid; page-break-inside: avoid; }
      table { break-inside: avoid; page-break-inside: avoid; }
      .opportunity { break-inside: avoid; page-break-inside: avoid; }
      .footer { break-inside: avoid; page-break-inside: avoid; }

      /* 主要セクション前で改ページ許可 */
      .section { page-break-before: auto; }
    }
  </style>
</head>
<body>
  <div class="report">
    <!-- Header -->
    <div class="header">
      <h1>Googleビジネスプロフィール診断レポート</h1>
      <div class="subtitle">${businessName} 様</div>
      <div class="date">${date} ｜ 業種: ${category}</div>
      <div class="disclaimer">※本レポートはGoogleマップ上の公開情報に基づく簡易診断です</div>
    </div>

    <!-- Total Score -->
    <div class="total-score">
      <div style="font-size:14px;color:#64748b;margin-bottom:8px;">総合評価</div>
      <div class="total-rank">${totalRank.rank}</div>
      <div class="total-label">${totalRank.label}（スコア: ${totalScore}/100）</div>
    </div>

    <!-- 5 Axis Scores -->
    <div class="section">
      <div class="section-title">5軸スコア</div>
      <div class="axis-grid">
${axes.map(a => `        <div class="axis-row">
          <div class="axis-label">${a.label}</div>
          <div class="axis-rank" style="color:${rankColors[a.rank.rank]}">${a.rank.rank}</div>
          <div class="axis-bar-container">
            <div class="axis-bar" style="width:${a.score}%;background:${rankColors[a.rank.rank]}"></div>
          </div>
          <div class="axis-score">${a.score}点</div>
        </div>`).join('\n')}
      </div>
    </div>

    <!-- Opportunity -->
    <div class="section">
      <div class="section-title">推定される状況</div>
      <div class="opportunity${totalScore >= 70 ? ' good' : ''}">
        ${opportunityMessage}
      </div>
    </div>

    <!-- Top 3 -->
    <div class="section">
      <div class="section-title">伸びしろ TOP3</div>
${top3.map((item, i) => `      <div class="top3-item">
        <div class="top3-header">
          <span class="top3-medal">${medalEmojis[i]}</span>
          <span class="top3-title">${item.improvement.summary}</span>
          <span style="color:${rankColors[item.currentRank]};font-weight:900;margin-left:auto">${item.currentRank}</span>
        </div>
        <dl class="top3-body">
          <dt>現状の課題</dt>
          <dd>${item.details.slice(0, 2).join(' / ') || '—'}</dd>
          <dt>改善の方向性</dt>
          <dd>${item.improvement.action}</dd>
          <dt>想定される工数</dt>
          <dd>${item.improvement.effort}</dd>
        </dl>
      </div>`).join('\n')}
    </div>

    <!-- Axis Detail -->
    <div class="section">
      <div class="section-title">各軸の詳細</div>
${axes.map(a => `      <div style="margin-bottom:20px">
        <div style="font-weight:700;font-size:14px;margin-bottom:4px">
          <span style="color:${rankColors[a.rank.rank]};font-weight:900">${a.rank.rank}</span>
          ${a.label}（${a.score}点）
        </div>
        <ul style="font-size:13px;color:#475569;padding-left:20px">
${a.details.length > 0 ? a.details.map(d => `          <li>${d}</li>`).join('\n') : '          <li>良好な状態です</li>'}
${a.replyRateNote ? `          <li style="color:#94a3b8;font-size:11px">※返信率は${a.replyRateNote}</li>` : ''}
        </ul>
      </div>`).join('\n')}
    </div>

${competitors.length > 0 ? `    <!-- Competitors -->
    <div class="section">
      <div class="section-title">競合との比較</div>
      <table>
        <thead>
          <tr><th>店舗名</th><th>平均評価</th><th>口コミ件数</th></tr>
        </thead>
        <tbody>
          <tr class="highlight">
            <td>★ ${businessName}（御社）</td>
            <td>${data.reviews.averageRating || '—'}</td>
            <td>${data.reviews.totalCount || 0}件</td>
          </tr>
${competitors.map(c => `          <tr>
            <td>${c.name}</td>
            <td>${c.rating || '—'}</td>
            <td>${c.reviewCount || 0}件</td>
          </tr>`).join('\n')}
        </tbody>
      </table>
    </div>` : ''}

    <!-- Footer -->
    <div class="footer">
      <div class="cta">
        上記の改善を実施することで、GBPの集客力向上が期待できます。<br>
        継続的な運用には、写真撮影・投稿企画・口コミ対応など<br>
        専門的なノウハウと定期的な工数が必要です。<br>
        <strong>運用代行にご興味がございましたら、お気軽にご相談ください。</strong>
      </div>
      <div class="contact">
        ※本レポートの評価基準は一般的な業種ベンチマークに基づくものであり、<br>
        個別の状況により最適な施策は異なる場合があります。
      </div>
    </div>
  </div>
</body>
</html>`;
}

/**
 * ② NotebookLM用テキスト生成
 */
function generateNotebookText(result, data) {
  const { businessName, category, totalScore, totalRank, axes, top3, opportunityMessage, competitors: allCompetitors, industry } = result;
  // レポート表示は上位3社（口コミ数順）
  const competitors = [...allCompetitors].sort((a, b) => (b.reviewCount || 0) - (a.reviewCount || 0)).slice(0, 3);
  const date = new Date().toLocaleDateString('ja-JP');
  const medalEmojis = ['🥇', '🥈', '🥉'];

  let text = '';

  text += `# ${businessName} 様 GBP MEO診断結果\n\n`;

  text += `## スライド1: 表紙\n`;
  text += `タイトル: Googleビジネスプロフィール診断レポート\n`;
  text += `サブタイトル: ${businessName} 様\n`;
  text += `日付: ${date}\n`;
  text += `業種: ${data.basic.category}\n`;
  text += `※Googleマップ上の公開情報に基づく簡易診断です\n\n`;

  text += `## スライド2: 総合スコア\n`;
  text += `総合評価: ${totalRank.rank}（${totalRank.label}）\n`;
  text += `スコア: ${totalScore}/100点\n\n`;
  text += `5軸の評価:\n`;
  for (const a of axes) {
    text += `  ${a.rank.rank} ${a.label}: ${a.score}点\n`;
  }
  text += '\n';

  text += `## スライド3: 推定される状況\n`;
  text += `${opportunityMessage}\n\n`;

  for (let i = 0; i < top3.length; i++) {
    const item = top3[i];
    text += `## スライド${4 + i}: 伸びしろ ${medalEmojis[i]} 第${i + 1}位\n`;
    text += `テーマ: ${item.improvement.summary}\n`;
    text += `現在のランク: ${item.currentRank}\n`;
    if (item.details.length > 0) {
      text += `現状の課題:\n`;
      for (const d of item.details.slice(0, 3)) {
        text += `  - ${d}\n`;
      }
    }
    text += `改善の方向性: ${item.improvement.action}\n`;
    text += `想定工数: ${item.improvement.effort}\n\n`;
  }

  if (competitors.length > 0) {
    text += `## スライド7: 競合との比較\n`;
    text += `| 店舗名 | 平均評価 | 口コミ件数 |\n`;
    text += `|--------|---------|----------|\n`;
    text += `| ★${businessName}（御社） | ${data.reviews.averageRating || '—'} | ${data.reviews.totalCount || 0}件 |\n`;
    for (const c of competitors) {
      text += `| ${c.name} | ${c.rating || '—'} | ${c.reviewCount || 0}件 |\n`;
    }
    text += '\n';
  }

  text += `## スライド${competitors.length > 0 ? 8 : 7}: 改善アクション一覧\n`;
  for (const item of top3) {
    text += `${item.rank}. ${item.improvement.summary}\n`;
    text += `   工数: ${item.improvement.effort}\n`;
    text += `   効果: ${item.improvement.impact}\n\n`;
  }

  text += `## 最終スライド: まとめ\n`;
  text += `上記の改善を実施することで、GBPの集客力向上が期待できます。\n`;
  text += `継続的な運用には、写真撮影・投稿企画・口コミ対応など\n`;
  text += `専門的なノウハウと定期的な工数が必要です。\n`;
  text += `運用代行にご興味がございましたら、お気軽にご相談ください。\n`;

  return text;
}

/**
 * ③ 営業用訴求トークテキスト生成
 * ユーザー心理に寄り添い、客観的事実と資産化を軸にした提案テキストを生成
 */
function generateSalesPitchText(result, data) {
  const { businessName, category, top3 } = result;

  let text = '';
  text += `■ 現状と機会損失について\n`;
  text += `現在のGoogleマップの状況を確認すると、せっかく検討段階に入った見込み客を取りこぼしてしまっている（機会損失が起きている）客観的な事実があります。\n\n`;
  
  text += `店舗や学習塾を探すお客様は、Web広告やチラシ、または検索で興味を持った後、必ず最後にマップの『口コミの数と質』や『最新の更新状況』で確認を行います。\n`;
  text += `口コミが十分にあり、情報がアクティブに管理されている状態であれば、それが絶対的な安心感に繋がり、問い合わせや相談への『行動のハードル』が下がります。これが現在の集客における明確な事実です。\n\n`;
  
  if (top3 && top3.length > 0) {
    text += `■ 主なボトルネック（現状の課題点）\n`;
    for (const item of top3) {
      text += `・${item.improvement.summary}\n`;
      if (item.details && item.details.length > 0) {
        text += `  （${item.details.join(' / ')}）\n`;
      }
    }
    text += `\n`;
  }

  text += `■ MEOの資産化とご提案\n`;
  text += `これらを全て自社で管理・運用し続けるのは多大な労力がかかりますが、プロに運用を任せることで、アカウントを確実な『集客資産』として最短で育てていくことが可能です。\n\n`;
  
  text += `ただ、MEOの資産化は我々だけの力では達成できません。日々の『口コミ獲得』など、オーナー様側の能動的なご協力があって初めて成功します。\n`;
  text += `もし「前向きに取り組んで現状を改善していきたい」というお考えでしたら、私たちが運用パートナーとして伴走させていただくことが可能です。\n\n`;
  text += `まずはこの機会損失の事実を認識していただき、本業に専念しながら集客の近道を目指すかどうか、ご検討いただければと思います。\n`;

  return text;
}

module.exports = { generateHTML, generateNotebookText, generateSalesPitchText };
