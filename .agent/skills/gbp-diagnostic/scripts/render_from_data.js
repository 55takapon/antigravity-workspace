/**
 * GBP診断レポート生成（目視確認済みデータJSONから）
 *
 * スクレイプ済み・目視確認済みのデータJSONを入力として、
 * スコアリング → HTML / NotebookLM用テキスト / 営業訴求トークを一括生成する。
 * （旧 test_{client}.js 14本のコピペ増殖を置き換えるパラメータ化スクリプト）
 *
 * 使い方:
 *   node scripts/render_from_data.js --data <データJSON> --client <クライアント名> [--outdir <出力先>]
 *
 * 引数:
 *   --data    入力データJSONのパス（basic/reviews/photos/posts/competitors 構造）
 *   --client  クライアント名（半角英数・アンダースコア推奨。ファイル名に使用）
 *   --outdir  出力先ディレクトリ（省略時: ~/gbp-clients/{client}）
 *
 * 出力（既存の命名規則を踏襲）:
 *   diagnostic_report_{client}_{YYYYMMDD}.html
 *   diagnostic_report_{client}_{YYYYMMDD}_notebook.txt
 *   diagnostic_sales_pitch_{client}_{YYYYMMDD}.txt
 *   diagnostic_data_{client}_{YYYYMMDD}.json  （入力データのコピー）
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const { analyzeGBP } = require('./analyze_gbp');
const { generateHTML, generateNotebookText, generateSalesPitchText } = require('./generate_report');

function printUsage() {
  console.error('使い方: node scripts/render_from_data.js --data <データJSON> --client <クライアント名> [--outdir <出力先>]');
  console.error('例:     node scripts/render_from_data.js --data ~/gbp-clients/meet_dental/diagnostic_input_meet_dental.json --client meet_dental');
}

// ── 引数パース ──
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--data') args.data = argv[++i];
    else if (argv[i] === '--client') args.client = argv[++i];
    else if (argv[i] === '--outdir') args.outdir = argv[++i];
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.data || !args.client) {
    printUsage();
    process.exit(1);
  }

  const dataPath = path.resolve(args.data);
  if (!fs.existsSync(dataPath)) {
    console.error(`❌ データJSONが見つかりません: ${dataPath}`);
    process.exit(1);
  }

  const client = args.client;
  const outDir = args.outdir ? path.resolve(args.outdir) : path.join(os.homedir(), 'gbp-clients', client);
  fs.mkdirSync(outDir, { recursive: true });

  // BOM付きでも読めるように除去してからパース
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8').replace(/^﻿/, ''));

  // ── スコアリング ──
  const result = analyzeGBP(data);

  console.log('=== スコアリング結果 ===');
  console.log(`ビジネス名: ${result.businessName}`);
  console.log(`業種判定: ${result.industry.label}`);
  console.log(`総合スコア: ${result.totalRank.rank} (${result.totalScore}/100)`);
  console.log('');
  console.log('5軸スコア:');
  for (const axis of result.axes) {
    console.log(`  ${axis.rank.rank} ${axis.label}: ${axis.score}点`);
    if (axis.details && axis.details.length > 0) {
      for (const d of axis.details) {
        console.log(`     → ${d}`);
      }
    }
  }

  // ── ファイル出力（日付はJST固定 / UTC+9） ──
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  const dateStr = jst.toISOString().slice(0, 10).replace(/-/g, '');

  const html = generateHTML(result, data);
  const htmlPath = path.join(outDir, `diagnostic_report_${client}_${dateStr}.html`);
  fs.writeFileSync(htmlPath, html, 'utf-8');
  console.log(`\n✅ HTML: ${htmlPath}`);

  const text = generateNotebookText(result, data);
  const textPath = path.join(outDir, `diagnostic_report_${client}_${dateStr}_notebook.txt`);
  fs.writeFileSync(textPath, text, 'utf-8');
  console.log(`✅ NotebookLM: ${textPath}`);

  const pitch = generateSalesPitchText(result, data);
  const pitchPath = path.join(outDir, `diagnostic_sales_pitch_${client}_${dateStr}.txt`);
  fs.writeFileSync(pitchPath, pitch, 'utf-8');
  console.log(`✅ 営業訴求トーク: ${pitchPath}`);

  const jsonPath = path.join(outDir, `diagnostic_data_${client}_${dateStr}.json`);
  fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2), 'utf-8');
  console.log(`✅ データ: ${jsonPath}`);
}

if (require.main === module) {
  main();
}
