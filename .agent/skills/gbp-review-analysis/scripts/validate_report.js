/**
 * validate_report.js
 * GBP口コミ分析レポートの品質保証（QA）スクリプト
 * 
 * Usage:
 *   node validate_report.js --input review_analysis_xxx.json
 */

const fs = require('fs');
const path = require('path');

function runQA(inputPath) {
  console.log(`\n🔍 品質チェックスキル（QA Validator）を実行します...`);
  console.log(`   対象: ${inputPath}\n`);

  if (!fs.existsSync(inputPath)) {
    console.error('❌ エラー: 分析結果ファイルが見つかりません。');
    process.exit(1);
  }

  const analysis = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
  const metadata = analysis.metadata || {};
  const rd = analysis.ratingDistribution;
  const oa = analysis.ownerReplyAnalysis;

  let errors = 0;
  let warnings = 0;

  // 1. 母数整合性チェック
  console.log('✅ チェック項目1: 母数整合性チェック');
  const officialTotal = metadata.totalReviews || 0;
  const extractedTotal = rd.total || 0;
  
  if (extractedTotal === 0) {
    console.error(`   ❌ FAIL: 口コミが1件も抽出されていません。抽出に失敗しています。`);
    errors++;
  } else if (officialTotal > 0 && Math.abs(officialTotal - extractedTotal) > 5) {
    console.warn(`   ⚠️ WARN: 公式件数（${officialTotal}件）と抽出件数（${extractedTotal}件）に大きな乖離があります。（Googleの表示遅延の可能性もありますが要確認）`);
    warnings++;
  } else {
    console.log(`   PASS: 抽出件数=${extractedTotal}件`);
  }

  // 2. 返信率チェック
  console.log('\n✅ チェック項目2: 返信率チェック');
  if (oa.replyRate === 0 && extractedTotal > 0) {
    console.error(`   ❌ FAIL: 返信率が0%になっています！実際に0%の可能性もありますが、スクレイピングの「セレクタバグ」の可能性が極めて高いため、Googleマップ上で目視確認してください！`);
    errors++;
  } else {
    console.log(`   PASS: 返信率=${oa.replyRate}%`);
  }

  // 3. インサイト多様性チェック
  console.log('\n✅ チェック項目3: インサイト（引用文）の重複チェック');
  const allQuotes = [];
  let duplicateQuotes = 0;

  for (const s of analysis.strengths || []) {
    for (const ex of s.examples || []) {
      const excerpt = ex.excerpt.substring(0, 15); // 最初の15文字で簡易チェック
      if (allQuotes.includes(excerpt)) {
        duplicateQuotes++;
      } else {
        allQuotes.push(excerpt);
      }
    }
  }

  if (duplicateQuotes > 0) {
    console.error(`   ❌ FAIL: 強み抽出の例文に ${duplicateQuotes} 件の重複が存在します！抽出ロジック（deduplicateExamples）が破綻しています。`);
    errors++;
  } else {
    console.log(`   PASS: 引用文の重複なし`);
  }

  // 4. 否定要素の抽出漏れチェック
  console.log('\n✅ チェック項目4: ネガティブ抽出の整合性チェック');
  const negativeThemeCount = (analysis.weaknesses || []).length;
  const lowRatedCount = (analysis.lowRatedReviews || []).length;

  if (negativeThemeCount === 0 && lowRatedCount > 0) {
    console.warn(`   ⚠️ WARN: 弱み（ネガティブテーマ）が0件ですが、星3以下の口コミが${lowRatedCount}件存在します。ネガティブ辞書が機能していない可能性があります。`);
    warnings++;
  } else {
    console.log(`   PASS: ネガティブ分析整合性OK`);
  }

  // 最終判定
  console.log('\n=======================================');
  if (errors > 0) {
    console.error(`❌ QA FAILED: ${errors}件の致命的なエラーがあります。`);
    console.error(`   このレポートをクライアントに提出することは『絶対』に許可されません！`);
    console.error(`   直ちにスクリプトを修正し、パイプラインを再実行してください。`);
    console.log('=======================================\n');
    process.exit(1);
  } else if (warnings > 0) {
    console.log(`⚠️ QA PASSED WITH WARNINGS: ${warnings}件の警告があります。`);
    console.log(`   念のため目視確認を推奨しますが、提出可能な状態です。`);
    console.log('=======================================\n');
  } else {
    console.log(`🎉 QA PASSED: 全ての品質基準を満たしました！`);
    console.log(`   クライアントに胸を張って提出できるプロフェッショナルなレポートです。`);
    console.log('=======================================\n');
  }
}

// === CLI実行 ===
if (require.main === module) {
  const args = process.argv.slice(2);
  const inputIdx = args.indexOf('--input');

  if (inputIdx === -1) {
    console.error('Usage: node validate_report.js --input <analysis.json>');
    process.exit(1);
  }

  runQA(args[inputIdx + 1]);
}

module.exports = { runQA };
