const fs = require('fs');
const path = require('path');

const REPORT_DIR = path.join(__dirname, '../../gbp-meo-core/reports');

function verifyReport(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const slug = path.basename(filePath).replace(/_monthly_.*$/, '');
  const errors = [];

  // Check 1: 閲覧数 (View count)
  // Search for: <div class="kpi-value">XXX</div>\n<div class="kpi-label">閲覧数</div>
  const viewCountMatch = content.match(/<div class="kpi-value">([\d,]+)<\/div>\s*<div class="kpi-label">閲覧数<\/div>/);
  if (viewCountMatch) {
    const views = parseInt(viewCountMatch[1].replace(/,/g, ''), 10);
    if (views < 10) {
      errors.push(`異常な閲覧数: ${views} (1桁です。データ列のパースズレが疑われます)`);
    }
  } else {
    errors.push('閲覧数のKPIが見つかりません');
  }

  // Check 2: ベンチマーク (Benchmarks)
  // Find the table body inside the benchmark section
  const benchmarkMatch = content.match(/<div class="section-title">📊 ベンチマーク参考<\/div>\s*<table>[\s\S]*?<tbody>([\s\S]*?)<\/tbody>/);
  if (benchmarkMatch) {
    const tbody = benchmarkMatch[1];
    // Count how many rows don't have '★' (competitors)
    const rows = tbody.match(/<tr[^>]*>[\s\S]*?<\/tr>/g) || [];
    const competitors = rows.filter(r => !r.includes('★'));
    if (competitors.length === 0) {
      // Pet sitter has no competitors by definition, but for a general check, warn if 0.
      if (slug !== 'pet-sitter' && slug !== 'meat-shika') { // Actually meat-shika now has them if extracted
        errors.push(`ベンチマーク（競合）が設定されていません`);
      }
    }
  } else {
    errors.push('ベンチマーク参考セクションが見つかりません');
  }

  // Check 3: 担当者より (Custom Message)
  const msgMatch = content.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
  if (msgMatch) {
    const msg = msgMatch[1].trim();
    if (msg.startsWith('※') || msg === '') {
      errors.push(`担当者よりのコメントが空欄またはプレースホルダーです`);
    }
  } else {
    errors.push('担当者よりセクションが見つかりません');
  }

  return errors;
}

function main() {
  if (!fs.existsSync(REPORT_DIR)) {
    console.error('Report directory not found:', REPORT_DIR);
    process.exit(1);
  }

  const files = fs.readdirSync(REPORT_DIR).filter(f => f.endsWith('.html'));
  let hasError = false;

  console.log('🔍 GBPレポート品質チェックを開始します...');
  
  for (const file of files) {
    const filePath = path.join(REPORT_DIR, file);
    const errors = verifyReport(filePath);
    if (errors.length > 0) {
      console.log(`❌ [NG] ${file}`);
      errors.forEach(e => console.log(`   - ${e}`));
      hasError = true;
    } else {
      console.log(`✅ [OK] ${file}`);
    }
  }

  if (hasError) {
    console.log('\n⚠️ 品質チェックに失敗したレポートがあります。修正してください。');
    process.exit(1);
  } else {
    console.log('\n🎉 全レポートの品質チェックを通過しました。');
  }
}

main();
