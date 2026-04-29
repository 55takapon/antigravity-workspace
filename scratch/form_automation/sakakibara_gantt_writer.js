/**
 * sakakibara_gantt_writer.js  v2.0
 * - 月ヘッダー文字化け修正（repeatCellで値+書式を同時設定）
 * - 担当〜開始日の間に「予測日数（営業日）」列を追加
 * - 2026年祝日を反映（土日＋祝日は非稼働日扱い）
 */

const { google } = require('googleapis');
const fs   = require('fs');
const path = require('path');

const SPREADSHEET_ID = '1WHq7_pmFKa5ZZu2NmiUx_d90JqRGlfRRFkj494Fb3yc';
const SHEET_NAME     = 'スケジュール';

const credPath    = path.join(__dirname, 'google_credentials.json');
const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
const auth = new google.auth.GoogleAuth({
  credentials,
  scopes: ['https://www.googleapis.com/auth/spreadsheets'],
});

// ===== カラー =====
function hex(h) {
  return { red: parseInt(h.slice(1,3),16)/255, green: parseInt(h.slice(3,5),16)/255, blue: parseInt(h.slice(5,7),16)/255 };
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
const HOLIDAY_BG  = '#FFCDD2'; // 祝日背景（ヘッダー行）
const HOLIDAY_FG  = '#C0392B'; // 祝日文字色
const WEEKEND_BG  = '#D5E0F0';
const WEEKEND_FG  = '#2471A3';

// ===== 2026年 祝日リスト（YYYY/MM/DD） =====
const HOLIDAYS_2026 = new Set([
  '2026/01/01', // 元日
  '2026/01/12', // 成人の日
  '2026/02/11', // 建国記念の日
  '2026/02/23', // 天皇誕生日
  '2026/03/20', // 春分の日
  '2026/04/29', // 昭和の日
  '2026/05/03', // 憲法記念日
  '2026/05/04', // みどりの日
  '2026/05/05', // こどもの日
  '2026/05/06', // 振替休日（5/3日曜の振替）
  '2026/07/20', // 海の日（第3月曜）
  '2026/08/11', // 山の日
  '2026/09/21', // 敬老の日（第3月曜）
  '2026/09/23', // 秋分の日
  '2026/10/12', // スポーツの日（第2月曜）
  '2026/11/03', // 文化の日
  '2026/11/23', // 勤労感謝の日
]);

function isHoliday(date) {
  const s = `${date.getFullYear()}/${String(date.getMonth()+1).padStart(2,'0')}/${String(date.getDate()).padStart(2,'0')}`;
  return HOLIDAYS_2026.has(s);
}
function isWeekend(date) { const d = date.getDay(); return d===0||d===6; }
function isNonWorking(date) { return isWeekend(date) || isHoliday(date); }

// 営業日数カウント（開始〜終了を含む）
function countBusinessDays(startStr, endStr) {
  const start = new Date(startStr); start.setHours(0,0,0,0);
  const end   = new Date(endStr);   end.setHours(0,0,0,0);
  let count = 0;
  const d = new Date(start);
  while (d <= end) { if (!isNonWorking(d)) count++; d.setDate(d.getDate()+1); }
  return count;
}

// ===== 工程データ（金額・工数なし） =====
// [Phase, 工程名, 担当, 開始日, 終了日, カテゴリ]
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

const PROJECT_START = new Date('2026-04-14'); PROJECT_START.setHours(0,0,0,0);
const PROJECT_END   = new Date('2026-08-31'); PROJECT_END.setHours(0,0,0,0);

function getDates(start, end) {
  const dates = []; const d = new Date(start);
  while (d <= end) { dates.push(new Date(d)); d.setDate(d.getDate()+1); }
  return dates;
}
function colLetter(n) {
  let s=''; while(n>0){const r=(n-1)%26;s=String.fromCharCode(65+r)+s;n=Math.floor((n-1)/26);} return s;
}

// ===== レイアウト定数 =====
// 列構成（1-indexed）
// A=Phase B=工程名 C=担当 D=予測日数 E=開始日 F=終了日 G=進捗 H〜=ガント
const GANTT_START_COL = 8; // H列
const INFO_COLS       = 7; // A〜G
const HEADER_ROW      = 5;
const DATA_START_ROW  = 6;

async function main() {
  const sheets = google.sheets({ version: 'v4', auth: await auth.getClient() });

  // ===== シート再作成 =====
  const meta = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const existing = meta.data.sheets.find(s => s.properties.title === SHEET_NAME);
  const reqs = [];
  if (existing) reqs.push({ deleteSheet: { sheetId: existing.properties.sheetId } });
  reqs.push({ addSheet: { properties: { title: SHEET_NAME, index: 0, gridProperties: { rowCount: 200, columnCount: 400 } } } });
  const batchRes = await sheets.spreadsheets.batchUpdate({ spreadsheetId: SPREADSHEET_ID, requestBody: { requests: reqs } });
  const newSheetId = batchRes.data.replies[reqs.length-1].addSheet.properties.sheetId;
  console.log('シート作成 sheetId:', newSheetId);

  const dates = getDates(PROJECT_START, PROJECT_END);
  const today = new Date(); today.setHours(0,0,0,0);

  // ===== VALUES 書き込み =====
  const valueData = [];

  // タイトル行1
  valueData.push({ range: `${SHEET_NAME}!A1`, values: [['📅  ホームページ制作ガントチャート　｜　榊原税理士事務所様']] });
  valueData.push({ range: `${SHEET_NAME}!A2`, values: [['公開目標：2026年6月末']] });
  valueData.push({ range: `${SHEET_NAME}!A3`, values: [['●オレンジ行＝お客様対応フェーズ　●赤縦線＝今日　●土日・祝日はグレー（ガントは営業日のみ反映）']] });
  const now = new Date().toLocaleString('ja-JP',{timeZone:'Asia/Tokyo'});
  valueData.push({ range: `${SHEET_NAME}!A4`, values: [[`最終更新：${now}`]] });

  // ヘッダー行5（A〜G）
  valueData.push({ range: `${SHEET_NAME}!A5:G5`, values: [['Phase','工程名','担当','予測日数','開始日','終了日','進捗']] });

  // データ行（6行目〜）
  PHASES.forEach(([id, name, owner, start, end], i) => {
    const bizDays = countBusinessDays(start, end);
    const row = DATA_START_ROW + i;
    valueData.push({ range: `${SHEET_NAME}!A${row}:G${row}`,
      values: [[id, name, owner, `${bizDays}日`, start, end, '未着手']] });
  });

  // 合計行
  const totalRow = DATA_START_ROW + PHASES.length;
  valueData.push({ range: `${SHEET_NAME}!A${totalRow}:G${totalRow}`, values: [['','公開予定：2026年6月末','','','','','']] });

  // 日付ヘッダー（5行目 H列以降）
  valueData.push({
    range: `${SHEET_NAME}!${colLetter(GANTT_START_COL)}${HEADER_ROW}:${colLetter(GANTT_START_COL+dates.length-1)}${HEADER_ROW}`,
    values: [dates.map(d => d.getDate())]
  });

  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId: SPREADSHEET_ID,
    requestBody: { valueInputOption: 'RAW', data: valueData }
  });
  console.log('値の書き込み完了');

  // ===== FORMATTING REQUESTS =====
  const fmtReqs = [];

  // 列幅（情報列）
  const colWidths = [50, 280, 95, 68, 88, 88, 65];
  colWidths.forEach((w, i) => {
    fmtReqs.push({ updateDimensionProperties: {
      range: { sheetId: newSheetId, dimension: 'COLUMNS', startIndex: i, endIndex: i+1 },
      properties: { pixelSize: w }, fields: 'pixelSize'
    }});
  });
  // ガント列幅（16px）
  fmtReqs.push({ updateDimensionProperties: {
    range: { sheetId: newSheetId, dimension: 'COLUMNS', startIndex: GANTT_START_COL-1, endIndex: GANTT_START_COL-1+dates.length },
    properties: { pixelSize: 16 }, fields: 'pixelSize'
  }});

  // 行高
  fmtReqs.push({ updateDimensionProperties: { range:{sheetId:newSheetId,dimension:'ROWS',startIndex:0,endIndex:1}, properties:{pixelSize:40}, fields:'pixelSize' }});
  fmtReqs.push({ updateDimensionProperties: { range:{sheetId:newSheetId,dimension:'ROWS',startIndex:HEADER_ROW-1,endIndex:HEADER_ROW}, properties:{pixelSize:32}, fields:'pixelSize' }});
  for (let i=0;i<PHASES.length;i++) {
    fmtReqs.push({ updateDimensionProperties: { range:{sheetId:newSheetId,dimension:'ROWS',startIndex:DATA_START_ROW-1+i,endIndex:DATA_START_ROW+i}, properties:{pixelSize:27}, fields:'pixelSize' }});
  }

  // タイトル行1: マージ & 書式
  fmtReqs.push({ mergeCells: { range:{sheetId:newSheetId,startRowIndex:0,endRowIndex:1,startColumnIndex:0,endColumnIndex:INFO_COLS}, mergeType:'MERGE_ALL' }});
  fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:0,endRowIndex:1,startColumnIndex:0,endColumnIndex:INFO_COLS},
    cell:{userEnteredFormat:{backgroundColor:hex(TITLE_BG),textFormat:{foregroundColor:hex('#FFFFFF'),fontSize:14,bold:true},verticalAlignment:'MIDDLE'}},
    fields:'userEnteredFormat' }});

  // 行2〜4
  fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:1,endRowIndex:2,startColumnIndex:0,endColumnIndex:INFO_COLS},
    cell:{userEnteredFormat:{textFormat:{foregroundColor:hex('#7F8C8D'),fontSize:10}}}, fields:'userEnteredFormat.textFormat' }});
  fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:2,endRowIndex:3,startColumnIndex:0,endColumnIndex:INFO_COLS},
    cell:{userEnteredFormat:{textFormat:{foregroundColor:hex('#E67E22'),fontSize:9}}}, fields:'userEnteredFormat.textFormat' }});
  fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:3,endRowIndex:4,startColumnIndex:0,endColumnIndex:INFO_COLS},
    cell:{userEnteredFormat:{textFormat:{foregroundColor:hex('#BDC3C7'),fontSize:9}}}, fields:'userEnteredFormat.textFormat' }});

  // ヘッダー行5（A〜G）
  fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:HEADER_ROW-1,endRowIndex:HEADER_ROW,startColumnIndex:0,endColumnIndex:INFO_COLS},
    cell:{userEnteredFormat:{backgroundColor:hex(HEADER_BG),textFormat:{foregroundColor:hex('#FFFFFF'),bold:true,fontSize:10},horizontalAlignment:'CENTER',verticalAlignment:'MIDDLE'}},
    fields:'userEnteredFormat' }});

  // データ行 書式
  PHASES.forEach(([id, name, owner,,,category], i) => {
    const rowIdx = DATA_START_ROW-1+i;
    const isCustomer = owner.includes('お客様');
    const bg = isCustomer ? '#FFF3E0' : (i%2===0 ? '#F8F9FA' : '#FFFFFF');
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:rowIdx,endRowIndex:rowIdx+1,startColumnIndex:0,endColumnIndex:INFO_COLS},
      cell:{userEnteredFormat:{backgroundColor:hex(bg)}}, fields:'userEnteredFormat.backgroundColor' }});
    // 担当列（C=3）: センタリング
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:rowIdx,endRowIndex:rowIdx+1,startColumnIndex:2,endColumnIndex:3},
      cell:{userEnteredFormat:{horizontalAlignment:'CENTER',textFormat: isCustomer?{foregroundColor:hex('#D35400'),bold:true}:{foregroundColor:hex('#000000'),bold:false}}},
      fields:'userEnteredFormat.horizontalAlignment,userEnteredFormat.textFormat' }});
    // 予測日数列（D=4）: センタリング、太字
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:rowIdx,endRowIndex:rowIdx+1,startColumnIndex:3,endColumnIndex:4},
      cell:{userEnteredFormat:{horizontalAlignment:'CENTER',textFormat:{bold:true,foregroundColor:hex('#2C3E50')}}},
      fields:'userEnteredFormat.horizontalAlignment,userEnteredFormat.textFormat' }});
    // 開始日・終了日（E=5,F=6）: センタリング
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:rowIdx,endRowIndex:rowIdx+1,startColumnIndex:4,endColumnIndex:6},
      cell:{userEnteredFormat:{horizontalAlignment:'CENTER'}}, fields:'userEnteredFormat.horizontalAlignment' }});
    // 進捗列（G=7）
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:rowIdx,endRowIndex:rowIdx+1,startColumnIndex:6,endColumnIndex:7},
      cell:{userEnteredFormat:{horizontalAlignment:'CENTER'}}, fields:'userEnteredFormat.horizontalAlignment' }});
  });

  // 合計行
  fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:totalRow-1,endRowIndex:totalRow,startColumnIndex:0,endColumnIndex:INFO_COLS},
    cell:{userEnteredFormat:{backgroundColor:hex(TITLE_BG),textFormat:{foregroundColor:hex('#FFFFFF'),bold:true}}}, fields:'userEnteredFormat' }});

  // フリーズ
  fmtReqs.push({ updateSheetProperties: { properties:{sheetId:newSheetId,gridProperties:{frozenRowCount:HEADER_ROW,frozenColumnCount:INFO_COLS}}, fields:'gridProperties.frozenRowCount,gridProperties.frozenColumnCount' }});

  // 枠線（情報列）
  fmtReqs.push({ updateBorders: { range:{sheetId:newSheetId,startRowIndex:HEADER_ROW-1,endRowIndex:totalRow,startColumnIndex:0,endColumnIndex:INFO_COLS},
    innerHorizontal:{style:'SOLID',color:hex('#DEE2E6')}, innerVertical:{style:'SOLID',color:hex('#DEE2E6')},
    top:{style:'SOLID',color:hex('#DEE2E6')}, bottom:{style:'SOLID',color:hex('#DEE2E6')},
    left:{style:'SOLID',color:hex('#DEE2E6')}, right:{style:'SOLID',color:hex('#DEE2E6')} }});

  // ===== 月ヘッダー（4行目）: マージ + 値 + 書式を同時設定 =====
  // （値をrepeatCellで埋め込むことで数値化を防ぐ）
  let prevMonth=-1, monthStartIdx=0;
  function flushMonth(endIdx, month) {
    const startCol = GANTT_START_COL-1+monthStartIdx;
    const endCol   = GANTT_START_COL-1+endIdx;
    if (endCol <= startCol) return;
    fmtReqs.push({ mergeCells: { range:{sheetId:newSheetId,startRowIndex:3,endRowIndex:4,startColumnIndex:startCol,endColumnIndex:endCol}, mergeType:'MERGE_ALL' }});
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:3,endRowIndex:4,startColumnIndex:startCol,endColumnIndex:endCol},
      cell:{
        userEnteredValue: { stringValue: `2026年${month+1}月` },
        userEnteredFormat:{
          backgroundColor:hex(MONTH_BG),
          textFormat:{foregroundColor:hex('#FFFFFF'),bold:true,fontSize:9},
          horizontalAlignment:'CENTER',
          numberFormat:{type:'TEXT'}
        }
      },
      fields:'userEnteredValue,userEnteredFormat' }});
  }

  dates.forEach((date, idx) => {
    const m = date.getMonth();
    if (m !== prevMonth) {
      if (prevMonth !== -1) flushMonth(idx, prevMonth);
      prevMonth = m; monthStartIdx = idx;
    }
  });
  flushMonth(dates.length, prevMonth); // 最終月

  // ===== 日付ヘッダー（5行目）着色 =====
  dates.forEach((date, idx) => {
    const col = GANTT_START_COL-1+idx;
    const weekend  = isWeekend(date);
    const holiday  = isHoliday(date);
    let bg, fg;
    if      (holiday && !weekend) { bg=HOLIDAY_BG; fg=HOLIDAY_FG; }
    else if (weekend)             { bg=WEEKEND_BG; fg=WEEKEND_FG; }
    else                          { bg=HEADER_BG;  fg='#FFFFFF'; }
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:HEADER_ROW-1,endRowIndex:HEADER_ROW,startColumnIndex:col,endColumnIndex:col+1},
      cell:{userEnteredFormat:{backgroundColor:hex(bg),textFormat:{foregroundColor:hex(fg),fontSize:7},horizontalAlignment:'CENTER'}},
      fields:'userEnteredFormat' }});
  });

  // ===== ガントバー着色（営業日のみ色付け） =====
  PHASES.forEach(([,, owner, startStr, endStr, category], pi) => {
    const rowIdx    = DATA_START_ROW-1+pi;
    const phaseStart = new Date(startStr); phaseStart.setHours(0,0,0,0);
    const phaseEnd   = new Date(endStr);   phaseEnd.setHours(0,0,0,0);
    const isCustomer = owner.includes('お客様');
    const barColor   = isCustomer ? COLORS['コンテンツ収集'] : (COLORS[category] || '#95A5A6');

    dates.forEach((date, idx) => {
      const col     = GANTT_START_COL-1+idx;
      const inRange = date >= phaseStart && date <= phaseEnd;
      const nonWork = isNonWorking(date);

      let bg;
      if (inRange && !nonWork)      bg = barColor;   // 営業日かつ期間内 → フェーズカラー
      else if (inRange && nonWork)  bg = '#C0C0C0';  // 期間内だが非営業日 → グレー
      else if (!inRange && nonWork) bg = '#EAECEE';  // 期間外・非営業日 → 薄グレー
      else                          bg = '#FFFFFF';   // 期間外・営業日 → 白

      fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:rowIdx,endRowIndex:rowIdx+1,startColumnIndex:col,endColumnIndex:col+1},
        cell:{userEnteredFormat:{backgroundColor:hex(bg)}}, fields:'userEnteredFormat.backgroundColor' }});
    });
  });

  // ガント合計行（濃い背景）
  fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:totalRow-1,endRowIndex:totalRow,startColumnIndex:GANTT_START_COL-1,endColumnIndex:GANTT_START_COL-1+dates.length},
    cell:{userEnteredFormat:{backgroundColor:hex(TITLE_BG)}}, fields:'userEnteredFormat.backgroundColor' }});

  // ===== 今日の列ハイライト =====
  if (today >= PROJECT_START && today <= PROJECT_END) {
    const diffDays = Math.floor((today-PROJECT_START)/86400000);
    const todayCol = GANTT_START_COL-1+diffDays;
    fmtReqs.push({ repeatCell: { range:{sheetId:newSheetId,startRowIndex:HEADER_ROW-1,endRowIndex:HEADER_ROW,startColumnIndex:todayCol,endColumnIndex:todayCol+1},
      cell:{userEnteredFormat:{backgroundColor:hex(TODAY_COLOR),textFormat:{foregroundColor:hex('#FFFFFF'),bold:true,fontSize:7}}},
      fields:'userEnteredFormat' }});
    // 各データ行に赤縦枠
    for (let i=0;i<PHASES.length;i++) {
      fmtReqs.push({ updateBorders: { range:{sheetId:newSheetId,startRowIndex:DATA_START_ROW-1+i,endRowIndex:DATA_START_ROW+i,startColumnIndex:todayCol,endColumnIndex:todayCol+1},
        left:{style:'SOLID_MEDIUM',color:hex(TODAY_COLOR)}, right:{style:'SOLID_MEDIUM',color:hex(TODAY_COLOR)} }});
    }
  }

  // ===== バッチ実行（500件ずつ） =====
  const CHUNK = 500;
  for (let i=0; i<fmtReqs.length; i+=CHUNK) {
    await sheets.spreadsheets.batchUpdate({ spreadsheetId:SPREADSHEET_ID, requestBody:{ requests:fmtReqs.slice(i,i+CHUNK) } });
    console.log(`書式適用: ${Math.min(i+CHUNK,fmtReqs.length)}/${fmtReqs.length}`);
  }

  console.log('\n✅ 完了！');
  console.log(`https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}/edit`);
}

main().catch(e => { console.error('エラー:', e.message); process.exit(1); });
