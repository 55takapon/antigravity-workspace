/**
 * get_stats_0505_v2.js — 2026-05-05 送信統計（詳細版）
 * ○/×/△/未 はすべて「送信日が5/5」または「statusが入っている行」で判定
 * 送信日なしでも × や 未 が記録されている可能性あり
 */
const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

const CRED_PATH = path.join(__dirname, 'google_credentials.json');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_DATE = '2026/05/05';
const EXCLUDE_DOMAINS = ['jet-produce.com', 'localhost', '127.0.0.1'];
const SHEETS = ['260325test', '251127'];

async function main() {
  const credentials = JSON.parse(fs.readFileSync(CRED_PATH, 'utf-8'));
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  });
  const sheets = google.sheets({ version: 'v4', auth });

  for (const sheetName of SHEETS) {
    console.log(`\n${'═'.repeat(60)}`);
    console.log(`📋 シート: ${sheetName}`);
    console.log('═'.repeat(60));

    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: `'${sheetName}'`,
    });
    const values = res.data.values || [];
    if (values.length < 2) { console.log('  データなし'); continue; }

    const headers = values[0];
    const rows = values.slice(1);
    console.log(`  ヘッダー: ${JSON.stringify(headers.slice(0, 10))}`);

    const col = (name) => headers.indexOf(name);
    const urlCol    = col('問い合わせフォームURL');
    const dateCol   = col('送信日');
    const statusCol = col('送信○×');
    const reasonCol = col('送信不可理由');
    const companyCol = col('企業名');

    console.log(`  総行数: ${rows.length}`);

    // 5/5に何らかの処理があった行をすべて抽出
    const processed = [];
    let excludeCount = 0, noUrlCount = 0, preexistCount = 0, ngCount = 0;

    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const rowNum = i + 2;
      const url     = (row[urlCol]    || '').trim();
      const date    = (row[dateCol]   || '').trim();
      const status  = (row[statusCol] || '').trim();
      const reason  = (row[reasonCol] || '').trim();
      const company = (row[companyCol]|| '').trim();

      // URLなし
      if (!url || !url.startsWith('http')) { noUrlCount++; continue; }

      // jet-produce除外
      let hostname = '';
      try { hostname = new URL(url).hostname; } catch(e) {}
      if (EXCLUDE_DOMAINS.some(d => hostname.includes(d))) { excludeCount++; continue; }

      // 前日以前の送信済み
      if (date && date !== TARGET_DATE) { preexistCount++; continue; }

      // 5/5送信済み or status入り or reason入り → 記録
      if (date === TARGET_DATE || status || reason) {
        processed.push({ rowNum, company, url: hostname, date, status, reason });
      }
    }

    // 集計
    const maru   = processed.filter(r => r.status === '〇').length;
    const delta  = processed.filter(r => r.status === '△').length;
    const batsu  = processed.filter(r => r.status === '×').length;
    const mi     = processed.filter(r => r.status === '未').length;
    const ng_reason = processed.filter(r => !r.date && r.reason && !r.status).length;
    const total_tried = maru + delta + batsu + mi;

    console.log(`
  ── 5/5 送信アクション ────────────────────
  総試行数（jet-produce除外）: ${total_tried} 件
    ✅ 成功（〇）:     ${maru} 件
    ⚠️  要確認（△）:  ${delta} 件
    ❌ 失敗（×）:     ${batsu} 件
    ❓ 判定不能（未）: ${mi} 件

  ── スキップ内訳 ─────────────────────────
    📅 送信済み（前日以前）:   ${preexistCount} 件
    🚫 送信不可理由NG:          ${ng_reason} 件
    🔗 URLなし:                  ${noUrlCount} 件
    🧪 jet-produce除外:          ${excludeCount} 件
    `);

    if (processed.length > 0) {
      console.log('  ── 処理行詳細 ──────────────────────────────────');
      for (const d of processed) {
        const icon = d.status === '〇' ? '✅' : d.status === '△' ? '⚠️ ' : d.status === '×' ? '❌' : d.status === '未' ? '❓' : '  ';
        const r = d.reason ? ` [${d.reason.slice(0, 25)}]` : '';
        console.log(`  行${String(d.rowNum).padEnd(3)} ${icon} ${d.status || '(statusなし)'} | ${d.company.slice(0,18).padEnd(20)} | ${d.url}${r}`);
      }
    }
  }
}

main().catch(e => { console.error('Error:', e.message); process.exit(1); });
