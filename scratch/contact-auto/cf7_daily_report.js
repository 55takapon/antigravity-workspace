#!/usr/bin/env node
/**
 * cf7_daily_report.js — CF7エビデンスログ日次集計レポート
 * 
 * 使い方:
 *   node cf7_daily_report.js                    # 本日分を集計
 *   node cf7_daily_report.js 2026-04-30         # 指定日を集計
 *   node cf7_daily_report.js --all              # 全期間を集計
 * 
 * 出力:
 *   - コンソールにサマリーを表示
 *   - reports/cf7_report_YYYY-MM-DD.md にレポート保存
 */

const fs = require('fs');
const path = require('path');

// ── 設定 ──
const LOGS_DIR = path.join(__dirname, 'logs');
const REPORTS_DIR = path.join(__dirname, 'reports');

// テスト用ドメイン（集計から除外）
const EXCLUDE_DOMAINS = [
  'localhost',
  'jet-produce.com',
  '127.0.0.1',
];

// ── 引数処理 ──
const arg = process.argv[2];
const targetDate = arg === '--all' ? null : (arg || new Date().toISOString().slice(0, 10));

// ── ログファイル収集 ──
function collectJsonFiles(dir) {
  let files = [];
  if (!fs.existsSync(dir)) return files;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files = files.concat(collectJsonFiles(full));
    } else if (entry.name.endsWith('.json') && !entry.name.startsWith('unknown_fields') && !entry.name.startsWith('unmatched_')) {
      files.push(full);
    }
  }
  return files;
}

function collectUnknownFieldFiles(dir) {
  let files = [];
  if (!fs.existsSync(dir)) return files;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files = files.concat(collectUnknownFieldFiles(full));
    } else if (entry.name.startsWith('unknown_fields') && entry.name.endsWith('.json')) {
      files.push(full);
    }
  }
  return files;
}

// ── メイン処理 ──
function run() {
  const allEvidenceFiles = collectJsonFiles(LOGS_DIR);
  const allUnknownFiles = collectUnknownFieldFiles(LOGS_DIR);

  // 日付フィルタ
  const evidenceFiles = targetDate
    ? allEvidenceFiles.filter(f => path.basename(f).startsWith(targetDate))
    : allEvidenceFiles;

  const unknownFiles = targetDate
    ? allUnknownFiles.filter(f => path.basename(f).includes(targetDate))
    : allUnknownFiles;

  if (evidenceFiles.length === 0 && unknownFiles.length === 0) {
    console.log(`📭 ${targetDate || '全期間'} のログファイルが見つかりません。`);
    return;
  }

  // ── エビデンス解析 ──
  let totalSent = 0;
  let success = 0;
  let fail = 0;
  const statusMap = {};      // mail_sent, mail_failed, etc.
  const evidenceMap = {};     // S, A, B, error
  const domainResults = {};   // domain -> { success, fail }
  const errors = [];

  for (const file of evidenceFiles) {
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf8'));

      // ドメイン判定（先にやってテスト用を除外）
      let domain = 'unknown';
      try {
        domain = new URL(data.pageUrl).hostname;
      } catch (e) {
        const m = path.basename(file).match(/_([^_]+\.\w+)\.json$/);
        if (m) domain = m[1].replace(/_/g, '.');
      }

      // テスト用ドメインは除外
      if (EXCLUDE_DOMAINS.some(ex => domain.includes(ex))) continue;

      totalSent++;

      // 結果
      const isSuccess = data.result?.success === true;
      if (isSuccess) success++;
      else fail++;

      // ステータス
      const apiStatus = data.apiResponse?.status || 'unknown';
      statusMap[apiStatus] = (statusMap[apiStatus] || 0) + 1;

      // エビデンスランク
      const ev = data.result?.evidence || 'unknown';
      evidenceMap[ev] = (evidenceMap[ev] || 0) + 1;

      if (!domainResults[domain]) domainResults[domain] = { success: 0, fail: 0 };
      if (isSuccess) domainResults[domain].success++;
      else domainResults[domain].fail++;

      // エラー詳細
      if (!isSuccess) {
        errors.push({
          domain,
          rowId: data.rowId,
          reason: data.result?.reason || apiStatus,
          file: path.basename(file),
        });
      }
    } catch (e) {
      // JSONパースエラー → スキップ
    }
  }

  // ── 未知フィールド解析 ──
  let unknownFieldCount = 0;
  const unknownFieldNames = {};
  for (const file of unknownFiles) {
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf8'));
      const arr = Array.isArray(data) ? data : [data];
      for (const item of arr) {
        unknownFieldCount++;
        const name = item.name || 'unnamed';
        unknownFieldNames[name] = (unknownFieldNames[name] || 0) + (item.count || 1);
      }
    } catch (e) {}
  }

  // ── レポート生成 ──
  const successRate = totalSent > 0 ? ((success / totalSent) * 100).toFixed(1) : '0.0';
  const dateLabel = targetDate || '全期間';
  const now = new Date().toISOString().replace('T', ' ').slice(0, 19);

  let report = `# 📊 CF7 日次集計レポート — ${dateLabel}\n\n`;
  report += `> **生成時刻**: ${now} JST\n\n`;
  report += `---\n\n`;

  // サマリー
  report += `## 📈 送信サマリー\n\n`;
  report += `| 指標 | 値 |\n|---|---|\n`;
  report += `| 総送信試行数 | ${totalSent} |\n`;
  report += `| ✅ 成功 | ${success} |\n`;
  report += `| ❌ 失敗 | ${fail} |\n`;
  report += `| 成功率 | **${successRate}%** |\n\n`;

  // APIステータス分布
  report += `## 🏷️ APIステータス分布\n\n`;
  report += `| ステータス | 件数 |\n|---|---|\n`;
  for (const [status, count] of Object.entries(statusMap).sort((a, b) => b[1] - a[1])) {
    const icon = status === 'mail_sent' ? '✅' : '❌';
    report += `| ${icon} ${status} | ${count} |\n`;
  }
  report += `\n`;

  // エビデンスランク分布
  report += `## 🎯 エビデンスランク分布\n\n`;
  report += `| ランク | 件数 | 説明 |\n|---|---|---|\n`;
  const rankDesc = { S: '完全一致（API確認）', A: 'DOM変化確認', B: '推定成功', error: 'エラー', unknown: '不明' };
  for (const [rank, count] of Object.entries(evidenceMap).sort()) {
    report += `| **${rank}** | ${count} | ${rankDesc[rank] || ''} |\n`;
  }
  report += `\n`;

  // ドメイン別成績
  report += `## 🌐 ドメイン別送信結果\n\n`;
  report += `| ドメイン | 成功 | 失敗 | 成功率 |\n|---|---|---|---|\n`;
  const sortedDomains = Object.entries(domainResults).sort((a, b) => (b[1].success + b[1].fail) - (a[1].success + a[1].fail));
  for (const [domain, r] of sortedDomains) {
    const total = r.success + r.fail;
    const rate = ((r.success / total) * 100).toFixed(0);
    report += `| ${domain} | ${r.success} | ${r.fail} | ${rate}% |\n`;
  }
  report += `\n`;

  // エラー詳細
  if (errors.length > 0) {
    report += `## ⚠️ エラー詳細（上位10件）\n\n`;
    report += `| ドメイン | rowId | 理由 |\n|---|---|---|\n`;
    for (const err of errors.slice(0, 10)) {
      report += `| ${err.domain} | ${err.rowId} | ${err.reason} |\n`;
    }
    report += `\n`;
  }

  // 未知フィールド
  report += `## 🔍 未知フィールド（未マッチ）\n\n`;
  if (unknownFieldCount === 0) {
    report += `> 本日は未知フィールドの発生なし\n\n`;
  } else {
    report += `| フィールド名 | 出現回数 |\n|---|---|\n`;
    const sortedFields = Object.entries(unknownFieldNames).sort((a, b) => b[1] - a[1]);
    for (const [name, count] of sortedFields.slice(0, 15)) {
      report += `| \`${name}\` | ${count} |\n`;
    }
    report += `\n> 合計 ${unknownFieldCount} 件の未知フィールドを検出\n\n`;
  }

  report += `---\n\n`;
  report += `*cf7_daily_report.js による自動生成*\n`;

  // ── コンソール出力 ──
  console.log(`\n${'═'.repeat(50)}`);
  console.log(`  📊 CF7 日次集計レポート — ${dateLabel}`);
  console.log(`${'═'.repeat(50)}`);
  console.log(`  総送信: ${totalSent} | ✅ 成功: ${success} | ❌ 失敗: ${fail}`);
  console.log(`  成功率: ${successRate}%`);
  console.log(`  未知フィールド: ${unknownFieldCount} 件`);
  console.log(`${'═'.repeat(50)}\n`);

  // ── ファイル保存 ──
  if (!fs.existsSync(REPORTS_DIR)) fs.mkdirSync(REPORTS_DIR, { recursive: true });
  const reportFile = path.join(REPORTS_DIR, `cf7_report_${dateLabel}.md`);
  fs.writeFileSync(reportFile, report, 'utf8');
  console.log(`📄 レポート保存: ${reportFile}\n`);
}

run();
