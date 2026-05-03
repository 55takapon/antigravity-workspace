/**
 * CSVパーサー — GBP月次レポートテンプレートを読み取る
 * 
 * テンプレートCSVのセクション構造:
 *   行1-4: ヘッダー（顧客名・業種・カテゴリ・開始月）
 *   ■ パフォーマンス指標
 *   ■ アクション率
 *   ■ 口コミ
 *   ■ 投稿
 *   ■ 写真
 *   ■ 検索クエリTOP10
 *   ■ 競合ベンチマーク
 *   ■ MEO順位
 *   ■ 月次アクションログ
 */
const fs = require('fs');
const path = require('path');

/**
 * CSVテキストを行×列の2D配列にパースする
 */
function parseCSVText(text) {
  return text.split('\n')
    .map(line => line.replace(/\r$/, ''))
    .map(line => line.split(',').map(cell => cell.trim()));
}

/**
 * セクションの開始行を検出する（■で始まる行のみ対象）
 */
function findSectionStart(rows, sectionName) {
  for (let i = 0; i < rows.length; i++) {
    if (rows[i][0] && rows[i][0].startsWith('■') && rows[i][0].includes(sectionName)) {
      return i;
    }
  }
  return -1;
}

/**
 * 月のインデックスを取得（1月=1, 12月=12）
 * CSVヘッダー行から列番号を特定
 */
function getMonthColumn(month) {
  // CSVテンプレートの構造: 指標名, 1月, 2月, ... 12月, 備考
  return month; // 1月=列1, 2月=列2, ...
}

/**
 * セクションからデータを抽出する
 * @param {Array} rows - CSV全行
 * @param {string} sectionName - セクション名（■で始まる文字列の部分一致）
 * @param {number} month - 対象月（1-12）
 * @returns {Object} 指標名をキー、値をバリューとしたオブジェクト
 */
function extractSectionData(rows, sectionName, month) {
  const startIdx = findSectionStart(rows, sectionName);
  if (startIdx === -1) return {};

  const data = {};
  const col = getMonthColumn(month);

  // セクション開始の次の行（ヘッダー行）をスキップし、データ行を読む
  for (let i = startIdx + 2; i < rows.length; i++) {
    const row = rows[i];
    // 空行または次のセクション（■）に到達したら終了
    if (!row[0] || row[0].startsWith('■')) break;

    const label = row[0].replace(/^[├└┣┗│\s]+/, '').trim();
    if (!label) continue;

    const value = row[col] !== undefined ? row[col] : '';
    data[label] = value === '' ? null : isNaN(value) ? value : parseFloat(value);
  }

  return data;
}

/**
 * CSVファイルを読み込んでレポートデータを構造化する
 * @param {string} csvPath - CSVファイルパス
 * @param {number} month - 対象月（1-12）
 * @returns {Object} 構造化されたレポートデータ
 */
function parseReportCSV(csvPath, month) {
  const text = fs.readFileSync(csvPath, 'utf-8');
  const rows = parseCSVText(text);

  // ヘッダー情報
  const header = {
    clientName: rows[0] ? rows[0][1] || rows[0][0].replace('顧客名', '').replace(',', '').trim() : '未設定',
    industry: rows[1] ? rows[1][1] || '' : '',
    category: rows[2] ? rows[2][1] || '' : '',
    startMonth: rows[3] ? rows[3][1] || '' : '',
  };

  // 目標口コミ数（ヘッダー直下に「目標口コミ数」行があれば読み取る）
  let targetReviewCount = null;
  // 除外ルール（ヘッダー直下に「除外ルール」行があれば読み取る）
  let skipRules = [];
  for (let i = 0; i < Math.min(rows.length, 10); i++) {
    if (rows[i][0] && rows[i][0].includes('目標口コミ数')) {
      targetReviewCount = rows[i][1] ? parseInt(rows[i][1]) : null;
    }
    if (rows[i][0] && rows[i][0].includes('除外ルール')) {
      // カンマ区切りの値を配列化（例: "posts,calls" → ["posts","calls"]）
      skipRules = rows[i].slice(1).filter(v => v && v.trim()).map(v => v.trim());
    }
  }

  // 各セクションのデータ抽出
  const performance = extractSectionData(rows, 'パフォーマンス指標', month);
  const actionRates = extractSectionData(rows, 'アクション率', month);
  const reviews = extractSectionData(rows, '口コミ', month);
  const posts = extractSectionData(rows, '投稿', month);
  const photos = extractSectionData(rows, '写真', month);

  // 前月データも取得（前月比計算用）
  const prevMonth = month > 1 ? month - 1 : null;
  const prevPerformance = prevMonth ? extractSectionData(rows, 'パフォーマンス指標', prevMonth) : {};
  const prevReviews = prevMonth ? extractSectionData(rows, '口コミ', prevMonth) : {};

  // 検索クエリTOP10（構造が異なるため個別処理）
  const queries = extractSearchQueries(rows, month);

  // 競合ベンチマーク
  const competitors = extractCompetitors(rows, month);

  // MEO順位
  const meoRanking = extractSectionData(rows, 'MEO順位', month);

  // アクションログ
  const actionLog = extractActionLog(rows, month);

  return {
    header,
    month,
    targetReviewCount,
    skipRules,
    performance,
    prevPerformance,
    actionRates,
    reviews,
    prevReviews,
    posts,
    photos,
    queries,
    competitors,
    meoRanking,
    actionLog,
  };
}

/**
 * 検索クエリTOP10を抽出
 */
function extractSearchQueries(rows, month) {
  const startIdx = findSectionStart(rows, '検索クエリ');
  if (startIdx === -1) return [];

  const queries = [];
  // 月ごとに2列ずつ（KW, 表示回数）: 1月=列1,2 / 2月=列3,4 / ...
  const kwCol = (month - 1) * 2 + 1;
  const countCol = kwCol + 1;

  for (let i = startIdx + 2; i < rows.length; i++) {
    const row = rows[i];
    if (!row[0] || row[0].startsWith('■')) break;

    const keyword = row[kwCol] || '';
    const count = row[countCol] ? parseFloat(row[countCol]) : 0;

    if (keyword) {
      queries.push({ rank: parseInt(row[0]) || queries.length + 1, keyword, count });
    }
  }

  return queries;
}

/**
 * 競合ベンチマークを抽出
 */
function extractCompetitors(rows, month) {
  const startIdx = findSectionStart(rows, '競合ベンチマーク');
  if (startIdx === -1) return [];

  const competitors = [];
  // 四半期列: Q1=列1,2 / Q2=列3,4 / Q3=列5,6 / Q4=列7,8
  const quarter = Math.ceil(month / 3);
  const countCol = (quarter - 1) * 2 + 1;
  const ratingCol = countCol + 1;

  for (let i = startIdx + 2; i < rows.length; i++) {
    const row = rows[i];
    if (!row[0] || row[0].startsWith('■')) break;

    const name = row[0].replace(/^(競合\d+:|自社:)/, '').trim();
    const reviewCount = row[countCol] ? parseFloat(row[countCol]) : null;
    const rating = row[ratingCol] ? parseFloat(row[ratingCol]) : null;
    const isSelf = row[0].includes('自社');

    if (name) {
      competitors.push({ name, reviewCount, rating, isSelf });
    }
  }

  return competitors;
}

/**
 * アクションログを抽出
 */
function extractActionLog(rows, month) {
  const startIdx = findSectionStart(rows, 'アクションログ');
  if (startIdx === -1) return { actions: '', results: '' };

  for (let i = startIdx + 2; i < rows.length; i++) {
    const row = rows[i];
    if (!row[0]) continue;

    const monthLabel = `${month}月`;
    if (row[0].trim() === monthLabel || row[0].trim() === String(month)) {
      return {
        actions: row[1] || '',
        results: row[2] || '',
      };
    }
  }

  return { actions: '', results: '' };
}

module.exports = { parseReportCSV, parseCSVText, findSectionStart };
