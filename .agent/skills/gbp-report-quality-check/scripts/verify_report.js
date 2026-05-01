const fs = require('fs');
const path = require('path');

const REPORT_DIR = path.join(__dirname, '../../gbp-meo-core/reports');
const { CLIENTS } = require('../../gbp-meo-core/monthly-report/client_registry');

// slug → client_registry の正しい情報をマッピング
const REGISTRY = Object.fromEntries(CLIENTS.map(c => [c.slug, {
  name:        c.name,
  campus:      c.campus || null,
  displayName: c.campus ? c.name + '(' + c.campus + ')' : c.name,
  industry:    c.industry,
  competitors: c.competitors || [],
  skipRules:   c.skipRules || [],
}]));

function verifyReport(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const slug = path.basename(filePath).replace(/_monthly_.*$/, '');
  const errors = [];
  const warnings = [];
  const registryClient = REGISTRY[slug];

  // ──────────────────────────────────────────────
  // Check 1: slug が client_registry に存在するか
  // ──────────────────────────────────────────────
  if (!registryClient) {
    errors.push(`slug "${slug}" が client_registry.js に存在しません`);
    return { errors, warnings }; // 以降のチェックは不可能
  }

  // ──────────────────────────────────────────────
  // Check 2: クライアント名がレポート内に正しく含まれているか
  // ──────────────────────────────────────────────
  const expectedName = registryClient.displayName;
  if (!content.includes(registryClient.name)) {
    errors.push(`クライアント名「${registryClient.name}」がレポート内に見つかりません（データ混在の疑い）`);
  }

  // ──────────────────────────────────────────────
  // Check 3: 閲覧数 (View count) — ゼロ・異常値チェック
  // ──────────────────────────────────────────────
  const viewCountMatch = content.match(/<div class="kpi-value">([\d,]+)<\/div>\s*<div class="kpi-label">閲覧数<\/div>/);
  if (viewCountMatch) {
    const views = parseInt(viewCountMatch[1].replace(/,/g, ''), 10);
    if (views < 10) {
      errors.push(`異常な閲覧数: ${views} (1桁です。データ列のパースズレが疑われます)`);
    }
    if (views === 0) {
      errors.push(`閲覧数が0です。データが取得できていない可能性があります`);
    }
  } else {
    errors.push('閲覧数のKPIが見つかりません');
  }

  // ──────────────────────────────────────────────
  // Check 4: ベンチマーク（競合データ）— 空欄チェック
  // ──────────────────────────────────────────────
  const benchmarkMatch = content.match(/<div class="section-title">📊 ベンチマーク参考<\/div>\s*<table>[\s\S]*?<tbody>([\s\S]*?)<\/tbody>/);
  if (benchmarkMatch) {
    const tbody = benchmarkMatch[1];
    const rows = tbody.match(/<tr[^>]*>[\s\S]*?<\/tr>/g) || [];
    // 自社行以外で競合が1件以上あるか
    const nonSelfRows = rows.filter(r => !r.includes('background'));
    if (nonSelfRows.length === 0 && registryClient.competitors.length > 0) {
      errors.push(`ベンチマーク（競合）が設定されていません（registry上は${registryClient.competitors.length}社定義済み）`);
    }
  } else {
    errors.push('ベンチマーク参考セクションが見つかりません');
  }

  // ──────────────────────────────────────────────
  // Check 5: 担当者よりコメント — 空欄・プレースホルダーチェック
  // ──────────────────────────────────────────────
  const msgMatch = content.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
  if (msgMatch) {
    const msg = msgMatch[1].replace(/<[^>]+>/g, '').trim();
    if (msg.startsWith('※') || msg === '') {
      warnings.push(`担当者よりのコメントが空欄またはプレースホルダーです`);
    }
  } else {
    warnings.push('担当者よりセクションが見つかりません');
  }

  // ──────────────────────────────────────────────
  // Check 6: 業種名が正しいか（industry チェック）
  // ──────────────────────────────────────────────
  // レポートHTMLに業種が含まれていないケースもあるため、warningとして
  if (registryClient.industry) {
    // HTMLのタイトルやヘッダーに業種が含まれているか（間接チェック）
    // → 業種自体がHTMLに明示されていない構造の場合は警告のみ
  }

  // ──────────────────────────────────────────────
  // Check 7: グラフデータの存在チェック
  // ──────────────────────────────────────────────
  const chartMatch = content.match(/chartData\s*=\s*(\[[\s\S]*?\])/);
  if (!chartMatch) {
    warnings.push('グラフ用データ（chartData）が見つかりません');
  }

  // ──────────────────────────────────────────────
  // Check 8: skipRulesの反映チェック
  // ──────────────────────────────────────────────
  if (registryClient.skipRules.includes('posts')) {
    // 投稿頻度の推奨が出力されていないことを確認
    if (content.includes('投稿が') && content.includes('件です（月')) {
      errors.push(`skipRules["posts"]が設定されているのに、投稿頻度の推奨が出力されています`);
    }
  }

  return { errors, warnings };
}

function main() {
  if (!fs.existsSync(REPORT_DIR)) {
    console.error('Report directory not found:', REPORT_DIR);
    process.exit(1);
  }

  // 最新月のHTMLのみ対象（古いレポートはスキップ）
  const files = fs.readdirSync(REPORT_DIR).filter(f => f.endsWith('.html'));
  
  // 月ごとにグルーピングして最新月を特定
  const months = [...new Set(files.map(f => {
    const m = f.match(/_monthly_(\d+)/);
    return m ? m[1] : null;
  }).filter(Boolean))].sort();
  const latestMonth = months[months.length - 1];
  
  const targetFiles = files.filter(f => f.includes(`_monthly_${latestMonth}`));
  
  let hasError = false;
  let totalErrors = 0;
  let totalWarnings = 0;

  console.log(`🔍 GBPレポート品質チェック — ${latestMonth}月分（${targetFiles.length}ファイル）`);
  console.log('');
  
  for (const file of targetFiles) {
    const filePath = path.join(REPORT_DIR, file);
    const { errors, warnings } = verifyReport(filePath);
    const slug = file.replace(/_monthly_.*$/, '');
    const client = REGISTRY[slug];
    const label = client ? client.displayName : slug;
    
    if (errors.length > 0) {
      console.log(`❌ [NG] ${label} (${file})`);
      errors.forEach(e => console.log(`   🔴 ${e}`));
      warnings.forEach(w => console.log(`   🟡 ${w}`));
      hasError = true;
      totalErrors += errors.length;
    } else if (warnings.length > 0) {
      console.log(`⚠️ [WARN] ${label} (${file})`);
      warnings.forEach(w => console.log(`   🟡 ${w}`));
      totalWarnings += warnings.length;
    } else {
      console.log(`✅ [OK] ${label}`);
    }
    totalWarnings += warnings.length;
  }

  // client_registry に定義があるのにレポートがないクライアントを検出
  console.log('');
  const reportSlugs = new Set(targetFiles.map(f => f.replace(/_monthly_.*$/, '')));
  const missingSlugs = Object.keys(REGISTRY).filter(s => !reportSlugs.has(s));
  if (missingSlugs.length > 0) {
    console.log(`⚠️ レポート未生成のクライアント:`);
    missingSlugs.forEach(s => {
      const c = REGISTRY[s];
      console.log(`   ⏭ ${c.displayName} (${s})`);
    });
  }

  console.log('');
  console.log(`━━━ サマリー ━━━`);
  console.log(`  チェック対象: ${targetFiles.length}ファイル`);
  console.log(`  エラー: ${totalErrors}件`);
  console.log(`  警告: ${totalWarnings}件`);
  
  if (hasError) {
    console.log('\n⚠️ 品質チェックに失敗したレポートがあります。修正してください。');
    process.exit(1);
  } else {
    console.log('\n🎉 全レポートの品質チェックを通過しました。');
  }
}

main();
