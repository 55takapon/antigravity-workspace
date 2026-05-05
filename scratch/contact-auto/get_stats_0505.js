/**
 * get_stats_0505.js — 2026-05-05 送信統計集計
 * jet-produce.com ドメインへのテスト送信は除外
 */
const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const CRED_PATH = path.join(__dirname, 'google_credentials.json');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_DATE = '2026/05/05';
const EXCLUDE_DOMAINS = ['jet-produce.com', 'localhost', '127.0.0.1'];

// 対象シート: 260325test と 251127
const SHEETS = ['260325test', '251127'];

async function main() {
  const credentials = JSON.parse(fs.readFileSync(CRED_PATH, 'utf-8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  const allStats = {
    total_tried: 0,       // 送信試みた件数（スキップ除く）
    success_maru: 0,      // 〇 送信成功
    success_delta: 0,     // △ 要確認（成功寄り）
    fail_batsu: 0,        // × 送信失敗
    unknown_mi: 0,        // 未 判定不能
    skipped_preexist: 0,  // 送信済みスキップ（日付あり）
    skipped_reason: 0,    // 送信不可理由あり（NG）
    skipped_no_url: 0,    // URL なし
    skipped_exclude: 0,   // jet-produce等テスト除外
    details: [],
  };

  for (const sheetName of SHEETS) {
    console.log(`\n📋 シート: ${sheetName}`);
    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `'${sheetName}'`,
    });
    const values = res.data.values || [];
    if (values.length < 2) { console.log('  データなし'); continue; }

    const headers = values[0];
    const rows = values.slice(1);

    const col = (name) => headers.indexOf(name);
    const urlCol    = col('問い合わせフォームURL');
    const dateCol   = col('送信日');
    const statusCol = col('送信○×');
    const reasonCol = col('送信不可理由');
    const companyCol = col('企業名');

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const rowNum = i + 2;
      const url     = (row[urlCol]    || '').trim();
      const date    = (row[dateCol]   || '').trim();
      const status  = (row[statusCol] || '').trim();
      const reason  = (row[reasonCol] || '').trim();
      const company = (row[companyCol]|| '').trim();

      // URLなし → スキップ
      if (!url || !url.startsWith('http')) {
        allStats.skipped_no_url++;
        continue;
      }

      // jet-produce等テストドメイン除外
      try {
        const hostname = new URL(url).hostname;
        if (EXCLUDE_DOMAINS.some(d => hostname.includes(d))) {
          allStats.skipped_exclude++;
          console.log(`  🚫 行${rowNum} ${company} (${hostname}) → テスト除外`);
          continue;
        }
      } catch(e) {}

      // 送信済みスキップ（日付が今日以前についてる）
      if (date && date !== TARGET_DATE) {
        allStats.skipped_preexist++;
        continue;
      }

      // 5/5に送信した行（送信日が5/5のもの）
      if (date === TARGET_DATE) {
        allStats.total_tried++;
        if (status === '〇') allStats.success_maru++;
        else if (status === '△') allStats.success_delta++;
        else if (status === '×') allStats.fail_batsu++;
        else allStats.unknown_mi++;

        allStats.details.push({
          sheet: sheetName, row: rowNum, company,
          status, reason: reason || '—',
          url: url.length > 50 ? url.slice(0, 50) + '…' : url
        });
      }
      // 送信不可理由あり（送信日なし）→ スキップカウント
      else if (reason && !date) {
        allStats.skipped_reason++;
      }
    }
  }

  // ── レポート出力 ──
  console.log('\n' + '═'.repeat(60));
  console.log('  📊 5/5 送信統計（jet-produce.comテスト除外済み）');
  console.log('═'.repeat(60));

  const total = allStats.total_tried;
  const succeeded = allStats.success_maru + allStats.success_delta;
  const rate = total > 0 ? ((succeeded / total) * 100).toFixed(1) : '0.0';

  console.log(`
  【送信試行】
  　総試行数:       ${total} 件
  　✅ 成功（〇）:  ${allStats.success_maru} 件
  　⚠️ 要確認（△）: ${allStats.success_delta} 件（成功扱い）
  　❌ 失敗（×）:  ${allStats.fail_batsu} 件
  　❓ 判定不能（未）: ${allStats.unknown_mi} 件

  　送信率（〇+△/試行）: ${rate}%

  【スキップ内訳】
  　📅 送信済みスキップ（前日以前）: ${allStats.skipped_preexist} 件
  　🚫 送信不可理由あり（NG）:       ${allStats.skipped_reason} 件
  　🔗 URLなし:                       ${allStats.skipped_no_url} 件
  　🧪 テスト除外（jet-produce）:     ${allStats.skipped_exclude} 件
  `);

  console.log('  【ドメイン別詳細】');
  console.log('  ' + '-'.repeat(58));
  console.log(`  ${'シート'.padEnd(14)} ${'行'.padEnd(4)} ${'企業名'.padEnd(18)} ${'結果'.padEnd(4)} 理由`);
  console.log('  ' + '-'.repeat(58));
  for (const d of allStats.details) {
    const icon = d.status === '〇' ? '✅' : d.status === '△' ? '⚠️' : d.status === '×' ? '❌' : '❓';
    console.log(`  ${d.sheet.padEnd(14)} ${String(d.row).padEnd(4)} ${d.company.slice(0,16).padEnd(18)} ${icon} ${d.status}  ${d.reason.slice(0, 30)}`);
  }

  console.log('\n' + '═'.repeat(60));
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
