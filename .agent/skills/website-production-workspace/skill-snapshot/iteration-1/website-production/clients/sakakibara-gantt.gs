// ================================================
//  榊原案件ガントチャート 自動更新スクリプト
//  使い方: シートの「予測日数」「開始日」「終了日」を変更した瞬間に
//          他の日付とガントチャートが自動で再計算・描画されます。
// ================================================

// 祝日リスト（2026年）
const HOLIDAYS = new Set([
  '2026/01/01','2026/01/12','2026/02/11','2026/02/23','2026/03/20','2026/04/29',
  '2026/05/03','2026/05/04','2026/05/05','2026/05/06','2026/07/20','2026/08/11',
  '2026/09/21','2026/09/23','2026/10/12','2026/11/03','2026/11/23'
]);

const PHASE_COLORS = {
  'P1':'#4a90d9', 'P2':'#e91e8c', 'P3':'#ff8c42', 'P4':'#e91e8c',
  'P5':'#20b2aa', 'P6a':'#2ecc71','P6b':'#2ecc71',
  'P7a':'#f39c12','P7b':'#f39c12','P8':'#e74c3c',
  'P9':'#9b59b6', 'P11':'#1abc9c','P12':'#27ae60'
};

// 休日判定（土日・祝日）
function isNonWorking(d) {
  const dow = d.getDay();
  const s = Utilities.formatDate(d, 'Asia/Tokyo', 'yyyy/MM/dd');
  return dow === 0 || dow === 6 || HOLIDAYS.has(s);
}

// 編集時に自動発火するトリガー関数
function onEdit(e) {
  if (!e) return;
  const sheet = e.source.getActiveSheet();
  
  if (sheet.getName() !== 'スケジュール') return;
  
  const row = e.range.getRow();
  const col = e.range.getColumn();
  
  // データ行(6行目以降) かつ 予測日数(4)〜終了日(6) の編集時
  if (row >= 6 && col >= 4 && col <= 6) {
    // balanceDates が計算した日付を直接受け取り、シートの再読み込みを避ける
    const computed = balanceDates(sheet, row, col);
    updateGanttRow(sheet, row, computed.start, computed.end);
    
    sheet.getRange('A4').setValue(
      '最終更新：' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy/MM/dd HH:mm')
    );
  }
}

// 日付の整合性を取る処理
// 戻り値: { start: Date|null, end: Date|null } — 計算後の確定値
function balanceDates(sheet, row, changedCol) {
  const range = sheet.getRange(row, 4, 1, 3);
  const data = range.getValues()[0];
  
  let days  = Number(data[0]); // D列: 予測日数（数値）
  let start = data[1];         // E列: 開始日
  let end   = data[2];         // F列: 終了日

  let computedStart = start ? (() => { const s = new Date(start); s.setHours(0,0,0,0); return s; })() : null;
  let computedEnd   = end   ? (() => { const e = new Date(end);   e.setHours(0,0,0,0); return e; })() : null;
  
  // 開始日(E列) または 予測日数(D列) が変更された場合 -> 終了日(F列) を計算
  if (changedCol === 4 || changedCol === 5) {
    if (start && days > 0) {
      let d = new Date(start);
      d.setHours(0,0,0,0);
      let bizCount = 0;
      
      // 1日目は開始日自身。days日分の営業日が経過するまで進める
      while (true) {
        if (!isNonWorking(d)) {
          bizCount++;
          if (bizCount >= days) break;
        }
        d.setDate(d.getDate() + 1);
      }
      sheet.getRange(row, 6).setValue(d);
      computedEnd = new Date(d); // ← 計算済みの終了日を保持
    }
  } 
  // 終了日(F列) が変更された場合 -> 予測日数(D列) を逆算
  else if (changedCol === 6) {
    if (start && end) {
      let pStart = new Date(start); pStart.setHours(0,0,0,0);
      let pEnd   = new Date(end);   pEnd.setHours(0,0,0,0);
      let biz = 0;
      for (let d = new Date(pStart); d <= pEnd; d.setDate(d.getDate()+1)) {
        if (!isNonWorking(d)) biz++;
      }
      sheet.getRange(row, 4).setValue(biz);
      computedEnd = pEnd; // ← 入力済みの終了日をそのまま保持
    }
  }

  return { start: computedStart, end: computedEnd };
}

// 特定の行のガントチャートだけを再描画する処理
// computedStart / computedEnd を受け取ることで、setValue直後のキャッシュ問題を回避する
function updateGanttRow(sheet, row, computedStart, computedEnd) {
  const PROJECT_START = new Date('2026-04-14');
  PROJECT_START.setHours(0,0,0,0); // UTC→JST補正（9時→0時に統一）
  const PROJECT_END   = new Date('2026-08-31');
  PROJECT_END.setHours(0,0,0,0);   // UTC→JST補正（9時→0時に統一）
  const GANTT_COL  = 8; // H列から
  
  // フェーズID・担当列はシートから読む（変更されていないため問題なし）
  const rowData = sheet.getRange(row, 1, 1, 6).getValues()[0];
  const phaseId  = String(rowData[0]); // A列
  const owner    = String(rowData[2]); // C列

  // 日付は balanceDates が返した計算済みの値を優先して使う
  // （fallback: シート上の値）
  const startRaw = computedStart || rowData[4];
  const endRaw   = computedEnd   || rowData[5];
  
  if (!startRaw || !endRaw) return;

  // computedStart/computedEnd はすでに setHours(0,0,0,0) 済みなので
  // fallback用に new Date でコピーして時刻を正規化する
  const pStart = new Date(startRaw); pStart.setHours(0,0,0,0);
  const pEnd   = new Date(endRaw);   pEnd.setHours(0,0,0,0);

  // 色の組み立て
  const dates = [];
  for (let d = new Date(PROJECT_START); d <= PROJECT_END; d.setDate(d.getDate()+1)) {
    dates.push(new Date(d));
  }
  
  const barColor = PHASE_COLORS[phaseId] || '#95a5a6';
  const isCustomer = owner.includes('お客様');
  const activeColor = isCustomer ? '#ff8c42' : barColor;

  const bgRow = dates.map(date => {
    const inRange = date >= pStart && date <= pEnd;
    const nonWork = isNonWorking(date);
    if (inRange  && !nonWork) return activeColor; // 平日の期間内
    if (inRange  &&  nonWork) return '#c0c0c0';   // 休日の期間内（濃いグレー）
    if (!inRange &&  nonWork) return '#eaecee';   // 休日の期間外（薄いグレー）
    return '#ffffff';                             // 平日の期間外（白）
  });

  // ガントバーの配色を一気に反映
  sheet.getRange(row, GANTT_COL, 1, dates.length).setBackgrounds([bgRow]);
}
