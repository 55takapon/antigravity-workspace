/**
 * sakakibara_gantt_writer.js
 * Google Sheets API でガントチャートを直接書き込む
 * 使い方: node sakakibara_gantt_writer.js
 */

const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

const SPREADSHEET_ID = '1WHq7_pmFKa5ZZu2NmiUx_d90JqRGlfRRFkj494Fb3yc';
const SHEET_NAME = 'スケジュール';

// 認証（form_automation の credentials を流用）
const credPath = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');
const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
const auth = new google.auth.GoogleAuth({
  credentials,
  scopes: ['https://www.googleapis.com/auth/spreadsheets'],
});

// ===== カラー定義（RGB 0-1） =====
function hex(h) {
  const r = parseInt(h.slice(1,3),16)/255;
  const g = parseInt(h.slice(3,5),16)/255;
  const b = parseInt(h.slice(5,7),16)/255;
  return { red:r, green:g, blue:b };
}
const COLORS = {
  '企画・PM':       '#4A90D9',
  'デザイン':       '#E91E8C',
  'コンテンツ収集': '#FF8C42',
  '環境構築':       '#20B2AA',
  'SWELL構築':      '#2ECC71',
  '確認・修正':     '#F39C12',
  'SEO・公開':      '#E74C3C',
  'ツール・納品':   '#9B59B6',
  '相続LP':         '#1ABC9C',
  'LINE連携':       '#27AE60',
};
const HEADER_BG   = '#1B2631';
const TITLE_BG    = '#2C3E50';
const TODAY_COLOR = '#FF4444';
const MONTH_BG    = '#34495E';

// ===== 工程データ（金額・工数なし） =====
const PHASES = [
  ['P1',  '企画・構成・PM（IA・WF・打ち合わせ含む）', '制作側',       '2026/04/14', '2026/04/25', '企画・PM'],
  ['P3',  'コンテンツ収集（テキスト・画像）',          'お客様',       '2026/04/21', '2026/05/09', 'コンテンツ収集'],
  ['P5',  'テスト環境（ステージング）構築',            '制作側',       '2026/04/21', '2026/04/25', '環境構築'],
  ['P2',  'デザイン（TOPページ）',                    '制作側',       '2026/04/25', '2026/05/16', 'デザイン'],
  ['P4',  'デザイン（下層ページ×5）',                 '制作側',       '2026/05/12', '2026/05/23', 'デザイン'],
  ['P6a', 'SWELL構築（TOPページ）',                   '制作側',       '2026/05/14', '2026/05/25', 'SWELL構築'],
  ['P7a', 'TOPページ確認・修正',                      'お客様＋制作', '2026/05/25', '2026/06/06', '確認・修正'],
  ['P6b', 'SWELL構築（下層ページ）',                  '制作側',       '2026/05/25', '2026/06/10', 'SWELL構築'],
  ['P7b', '下層ページ確認・修正',                     'お客様＋制作', '2026/06/06', '2026/06/17', '確認・修正'],
  ['P8',  '公開・SEO設定（GA4・GSC・構造化データ）',  '制作側',       '2026/06/15', '2026/06/27', 'SEO・公開'],
  ['P9',  'ツール導入・セキュリティ・納品',           '制作側',       '2026/06/22', '2026/06/30', 'ツール・納品'],
  ['P11', '相続専門LP制作（構成・デザイン・実装）',   '制作側',       '2026/07/21', '2026/08/14', '相続LP'],
  ['P12', 'LINE公式アカウント連携・リッチメニュー',   '制作側',       '2026/07/28', '2026/08/28', 'LINE連携'],
];

const PROJECT_START = new Date('2026-04-14');
const PROJECT_END   = new Date('2026-08-31');

// 日付配列生成
function getDates(start, end) {
  const dates = [];
  const d = new Date(start);
  while (d <= end) { dates.push(new Date(d)); d.setDate(d.getDate()+1); }
  return dates;
}

// col番号 → A1形式
function colLetter(n) {
  let s = '';
  while (n > 0) { const r = (n-1)%26; s = String.fromCharCode(65+r)+s; n=Math.floor((n-1)/26); }
  return s;
}

async function main() {
  const sheets = google.sheets({ version: 'v4', auth: await auth.getClient() });

  // ===== 既存シート削除 → 新規作成 =====
  const meta = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const existing = meta.data.sheets.find(s => s.properties.title === SHEET_NAME);

  const addRequest = { addSheet: { properties: { title: SHEET_NAME, index: 0, gridProperties: { rowCount: 200, columnCount: 300 } } } };
  const requests = [];

  if (existing) requests.push({ deleteSheet: { sheetId: existing.properties.sheetId } });
  requests.push(addRequest);

  const batchRes = await sheets.spreadsheets.batchUpdate({ spreadsheetId: SPREADSHEET_ID, requestBody: { requests } });
  const newSheetId = batchRes.data.replies[requests.length - 1].addSheet.properties.sheetId;
  console.log('シート作成完了 sheetId:', newSheetId);

  const dates = getDates(PROJECT_START, PROJECT_END);
  const GANTT_START_COL = 7; // G列（1-indexed）
  const HEADER_ROW = 5;      // 5行目（0-indexed: 4）
  const DATA_START_ROW = 6;  // 6行目（0-indexed: 5）
  const today = new Date(); today.setHours(0,0,0,0);

  // ===== VALUES 書き込み =====
  const valueData = [];

  // 行1: タイトル
  valueData.push({ range: `${SHEET_NAME}!A1`, values: [['📅  ホームページ制作ガントチャート　｜　榊原税理士事務所様']] });
  // 行2
  valueData.push({ range: `${SHEET_NAME}!A2`, values: [['公開目標：2026年6月末']] });
  // 行3
  valueData.push({ range: `${SHEET_NAME}!A3`, values: [['●オレンジ行 = お客様対応フェーズ　●赤縦線 = 今日　●土日はグレーアウト']] });
  // 行4
  const now = new Date().toLocaleString('ja-JP',{timeZone:'Asia/Tokyo'});
  valueData.push({ range: `${SHEET_NAME}!A4`, values: [[`最終更新：${now}`]] });

  // 行5: ヘッダー
  valueData.push({ range: `${SHEET_NAME}!A5:F5`, values: [['Phase','工程名','担当','開始日','終了日','進捗']] });

  // 行6〜: データ
  PHASES.forEach(([id, name, owner, start, end], i) => {
    const row = DATA_START_ROW + i;
    valueData.push({ range: `${SHEET_NAME}!A${row}:F${row}`, values: [[id, name, owner, start, end, '未着手']] });
  });

  // 合計行
  const totalRow = DATA_START_ROW + PHASES.length;
  valueData.push({ range: `${SHEET_NAME}!A${totalRow}:F${totalRow}`, values: [['','公開予定：2026年6月末','','','','']] });

  // 日付ヘッダー（5行目 G列以降）
  const dateHeaderRow5 = dates.map(d => [d.getDate()]);
  valueData.push({ range: `${SHEET_NAME}!${colLetter(GANTT_START_COL)}5`, values: [dateHeaderRow5.flat().map(v => v)] });
  // 実際には横一行なので
  valueData.push({
    range: `${SHEET_NAME}!${colLetter(GANTT_START_COL)}${HEADER_ROW}:${colLetter(GANTT_START_COL + dates.length - 1)}${HEADER_ROW}`,
    values: [dates.map(d => d.getDate())]
  });

  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId: SPREADSHEET_ID,
    requestBody: { valueInputOption: 'USER_ENTERED', data: valueData }
  });
  console.log('値の書き込み完了');

  // ===== FORMATTING =====
  const fmtRequests = [];

  // 列幅
  const colWidths = [55, 300, 100, 95, 95, 70];
  colWidths.forEach((w, i) => {
    fmtRequests.push({ updateDimensionProperties: {
      range: { sheetId: newSheetId, dimension: 'COLUMNS', startIndex: i, endIndex: i+1 },
      properties: { pixelSize: w }, fields: 'pixelSize'
    }});
  });
  // ガント列幅（16px）
  fmtRequests.push({ updateDimensionProperties: {
    range: { sheetId: newSheetId, dimension: 'COLUMNS', startIndex: GANTT_START_COL-1, endIndex: GANTT_START_COL-1+dates.length },
    properties: { pixelSize: 16 }, fields: 'pixelSize'
  }});

  // 行高
  fmtRequests.push({ updateDimensionProperties: {
    range: { sheetId: newSheetId, dimension: 'ROWS', startIndex: 0, endIndex: 1 },
    properties: { pixelSize: 40 }, fields: 'pixelSize'
  }});
  fmtRequests.push({ updateDimensionProperties: {
    range: { sheetId: newSheetId, dimension: 'ROWS', startIndex: HEADER_ROW-1, endIndex: HEADER_ROW },
    properties: { pixelSize: 32 }, fields: 'pixelSize'
  }});
  for (let i=0; i<PHASES.length; i++) {
    fmtRequests.push({ updateDimensionProperties: {
      range: { sheetId: newSheetId, dimension: 'ROWS', startIndex: DATA_START_ROW-1+i, endIndex: DATA_START_ROW+i },
      properties: { pixelSize: 27 }, fields: 'pixelSize'
    }});
  }

  // タイトル行1 マージ & 書式
  fmtRequests.push({ mergeCells: { range: { sheetId: newSheetId, startRowIndex:0, endRowIndex:1, startColumnIndex:0, endColumnIndex:6 }, mergeType:'MERGE_ALL' }});
  fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:0, endRowIndex:1, startColumnIndex:0, endColumnIndex:6 },
    cell: { userEnteredFormat: { backgroundColor: hex(TITLE_BG), textFormat: { foregroundColor: hex('#FFFFFF'), fontSize:14, bold:true },
      verticalAlignment:'MIDDLE', wrapStrategy:'CLIP' } }, fields:'userEnteredFormat' }});

  // 行2〜4 書式
  fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:1, endRowIndex:2, startColumnIndex:0, endColumnIndex:6 },
    cell: { userEnteredFormat: { textFormat: { foregroundColor: hex('#7F8C8D'), fontSize:10 } } }, fields:'userEnteredFormat.textFormat' }});
  fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:2, endRowIndex:3, startColumnIndex:0, endColumnIndex:6 },
    cell: { userEnteredFormat: { textFormat: { foregroundColor: hex('#E67E22'), fontSize:9 } } }, fields:'userEnteredFormat.textFormat' }});
  fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:3, endRowIndex:4, startColumnIndex:0, endColumnIndex:6 },
    cell: { userEnteredFormat: { textFormat: { foregroundColor: hex('#BDC3C7'), fontSize:9 } } }, fields:'userEnteredFormat.textFormat' }});

  // ヘッダー行5（A〜F）
  fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex: HEADER_ROW-1, endRowIndex: HEADER_ROW, startColumnIndex:0, endColumnIndex:6 },
    cell: { userEnteredFormat: { backgroundColor: hex(HEADER_BG), textFormat: { foregroundColor: hex('#FFFFFF'), bold:true, fontSize:10 },
      horizontalAlignment:'CENTER', verticalAlignment:'MIDDLE' } }, fields:'userEnteredFormat' }});

  // データ行の交互色 & お客様行
  PHASES.forEach(([id, name, owner,,, category], i) => {
    const rowIdx = DATA_START_ROW - 1 + i;
    const isCustomer = owner.includes('お客様');
    const bg = isCustomer ? '#FFF3E0' : (i%2===0 ? '#F8F9FA' : '#FFFFFF');
    fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:rowIdx, endRowIndex:rowIdx+1, startColumnIndex:0, endColumnIndex:6 },
      cell: { userEnteredFormat: { backgroundColor: hex(bg) } }, fields:'userEnteredFormat.backgroundColor' }});
    // 担当列: センタリング
    fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:rowIdx, endRowIndex:rowIdx+1, startColumnIndex:2, endColumnIndex:3 },
      cell: { userEnteredFormat: { horizontalAlignment:'CENTER',
        textFormat: isCustomer ? { foregroundColor: hex('#D35400'), bold:true } : { foregroundColor: hex('#000000'), bold:false } } },
      fields:'userEnteredFormat.horizontalAlignment,userEnteredFormat.textFormat' }});
    // 進捗列
    fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:rowIdx, endRowIndex:rowIdx+1, startColumnIndex:5, endColumnIndex:6 },
      cell: { userEnteredFormat: { horizontalAlignment:'CENTER' } }, fields:'userEnteredFormat.horizontalAlignment' }});
  });

  // 合計行
  fmtRequests.push({ repeatCell: { range: { sheetId: newSheetId, startRowIndex:totalRow-1, endRowIndex:totalRow, startColumnIndex:0, endColumnIndex:6 },
    cell: { userEnteredFormat: { backgroundColor: hex(TITLE_BG), textFormat: { foregroundColor: hex('#FFFFFF'), bold:true } } }, fields:'userEnteredFormat' }});

  // フリーズ
  fmtRequests.push({ updateSheetProperties: { properties: { sheetId: newSheetId,
    gridProperties: { frozenRowCount: HEADER_ROW, frozenColumnCount: 6 } }, fields:'gridProperties.frozenRowCount,gridProperties.frozenColumnCount' }});

  // ===== 月ヘッダー（4行目） マージ & 着色 =====
  let prevMonth = -1, monthStartIdx = 0;
  dates.forEach((date, idx) => {
    const m = date.getMonth();
    if (m !== prevMonth) {
      if (prevMonth !== -1) {
        const startCol = GANTT_START_COL - 1 + monthStartIdx;
        const endCol   = GANTT_START_COL - 1 + idx;
        fmtRequests.push({ mergeCells: { range: { sheetId:newSheetId, startRowIndex:3, endRowIndex:4, startColumnIndex:startCol, endColumnIndex:endCol }, mergeType:'MERGE_ALL' }});
        fmtRequests.push({ repeatCell: { range: { sheetId:newSheetId, startRowIndex:3, endRowIndex:4, startColumnIndex:startCol, endColumnIndex:endCol },
          cell: { userEnteredFormat: { backgroundColor:hex(MONTH_BG), textFormat:{foregroundColor:hex('#FFFFFF'),bold:true,fontSize:9}, horizontalAlignment:'CENTER' } }, fields:'userEnteredFormat' }});
      }
      prevMonth = m; monthStartIdx = idx;
    }
  });
  // 最終月
  {
    const startCol = GANTT_START_COL - 1 + monthStartIdx;
    const endCol   = GANTT_START_COL - 1 + dates.length;
    fmtRequests.push({ mergeCells: { range: { sheetId:newSheetId, startRowIndex:3, endRowIndex:4, startColumnIndex:startCol, endColumnIndex:endCol }, mergeType:'MERGE_ALL' }});
    fmtRequests.push({ repeatCell: { range: { sheetId:newSheetId, startRowIndex:3, endRowIndex:4, startColumnIndex:startCol, endColumnIndex:endCol },
      cell: { userEnteredFormat: { backgroundColor:hex(MONTH_BG), textFormat:{foregroundColor:hex('#FFFFFF'),bold:true,fontSize:9}, horizontalAlignment:'CENTER' } }, fields:'userEnteredFormat' }});
  }

  // 月ヘッダー値（4行目）をvalueDataには書いていないので別途
  const monthValueData = [];
  prevMonth = -1; monthStartIdx = 0;
  dates.forEach((date, idx) => {
    const m = date.getMonth();
    if (m !== prevMonth) {
      if (prevMonth !== -1) {
        const startCol = GANTT_START_COL + monthStartIdx;
        monthValueData.push({ range: `${SHEET_NAME}!${colLetter(startCol)}4`, values: [[`2026年${prevMonth+1}月`]] });
      }
      prevMonth = m; monthStartIdx = idx;
    }
  });
  monthValueData.push({ range: `${SHEET_NAME}!${colLetter(GANTT_START_COL+monthStartIdx)}4`, values: [[`2026年${prevMonth+1}月`]] });

  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId: SPREADSHEET_ID,
    requestBody: { valueInputOption: 'USER_ENTERED', data: monthValueData }
  });

  // ===== 日付ヘッダー（5行目）着色 =====
  dates.forEach((date, idx) => {
    const col = GANTT_START_COL - 1 + idx;
    const dow = date.getDay();
    const isWeekend = dow===0 || dow===6;
    fmtRequests.push({ repeatCell: { range: { sheetId:newSheetId, startRowIndex:HEADER_ROW-1, endRowIndex:HEADER_ROW, startColumnIndex:col, endColumnIndex:col+1 },
      cell: { userEnteredFormat: {
        backgroundColor: isWeekend ? hex('#D5E0F0') : hex(HEADER_BG),
        textFormat: { foregroundColor: isWeekend ? hex('#2471A3') : hex('#FFFFFF'), fontSize:7 },
        horizontalAlignment: 'CENTER'
      }}, fields:'userEnteredFormat' }});
  });

  // ===== ガントバー着色 =====
  PHASES.forEach(([,, owner, startStr, endStr, category], pi) => {
    const rowIdx = DATA_START_ROW - 1 + pi;
    const phaseStart = new Date(startStr); phaseStart.setHours(0,0,0,0);
    const phaseEnd   = new Date(endStr);   phaseEnd.setHours(0,0,0,0);
    const isCustomer = owner.includes('お客様');
    const barColor   = isCustomer ? COLORS['コンテンツ収集'] : (COLORS[category] || '#95A5A6');

    dates.forEach((date, idx) => {
      const col = GANTT_START_COL - 1 + idx;
      const dow = date.getDay();
      const inRange = date >= phaseStart && date <= phaseEnd;

      let bg;
      if (inRange) {
        bg = barColor;
      } else {
        bg = (dow===0||dow===6) ? '#EAECEE' : '#FFFFFF';
      }
      fmtRequests.push({ repeatCell: { range: { sheetId:newSheetId, startRowIndex:rowIdx, endRowIndex:rowIdx+1, startColumnIndex:col, endColumnIndex:col+1 },
        cell: { userEnteredFormat: { backgroundColor: hex(bg) } }, fields:'userEnteredFormat.backgroundColor' }});
    });
  });

  // ガント合計行（濃い背景）
  fmtRequests.push({ repeatCell: { range: { sheetId:newSheetId, startRowIndex:totalRow-1, endRowIndex:totalRow, startColumnIndex:GANTT_START_COL-1, endColumnIndex:GANTT_START_COL-1+dates.length },
    cell: { userEnteredFormat: { backgroundColor: hex(TITLE_BG) } }, fields:'userEnteredFormat.backgroundColor' }});

  // ===== 今日の列 =====
  if (today >= PROJECT_START && today <= PROJECT_END) {
    const diffDays = Math.floor((today - PROJECT_START) / 86400000);
    const todayColIdx = GANTT_START_COL - 1 + diffDays;
    // ヘッダーを赤に
    fmtRequests.push({ repeatCell: { range: { sheetId:newSheetId, startRowIndex:HEADER_ROW-1, endRowIndex:HEADER_ROW, startColumnIndex:todayColIdx, endColumnIndex:todayColIdx+1 },
      cell: { userEnteredFormat: { backgroundColor:hex(TODAY_COLOR), textFormat:{foregroundColor:hex('#FFFFFF'),bold:true,fontSize:7} } }, fields:'userEnteredFormat' }});
  }

  // ===== バッチ実行（500件ずつ） =====
  const CHUNK = 500;
  for (let i=0; i<fmtRequests.length; i+=CHUNK) {
    const chunk = fmtRequests.slice(i, i+CHUNK);
    await sheets.spreadsheets.batchUpdate({ spreadsheetId: SPREADSHEET_ID, requestBody: { requests: chunk } });
    console.log(`書式適用: ${i+chunk.length}/${fmtRequests.length}`);
  }

  console.log('\n✅ 完了！ スプレッドシートを確認してください。');
  console.log(`https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit`);
}

main().catch(e => { console.error('エラー:', e.message); process.exit(1); });
