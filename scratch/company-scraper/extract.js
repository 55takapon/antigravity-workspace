/**
 * 企業情報抽出スクリプト（サービスアカウント認証版）
 *
 * 使い方:
 *   node extract.js --start 183 --end 200
 *
 * サービスアカウントJSONを使用するため、ブラウザ認証不要。
 */

'use strict';

const { google } = require('googleapis');
const axios = require('axios');
const cheerio = require('cheerio');
const path = require('path');

// ─── 設定 ──────────────────────────────────────────────
const SPREADSHEET_ID = '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY';
const SHEET_NAME = 'シート1';
const SCOPES = ['https://www.googleapis.com/auth/spreadsheets'];
const CREDENTIALS_PATH = path.join(__dirname, 'google_credentials.json');
const REQUEST_DELAY_MS = 1500;
const REQUEST_TIMEOUT_MS = 12000;

// 会社概要ページのリンクテキスト or hrefパターン
const COMPANY_PAGE_TEXT_PATTERNS = [
  /会社概要/,
  /企業概要/,
  /企業情報/,
  /会社情報/,
  /会社案内/,
  /について$/,
  /about\s*us/i,
  /about$/i,
  /company\s*profile/i,
  /corporate\s*profile/i,
  /アウトライン/,
];
const COMPANY_PAGE_HREF_PATTERNS = [
  /\/about/i,
  /\/company/i,
  /\/corporate/i,
  /\/profile/i,
  /\/outline/i,
];

// URLパスのフォールバック候補（よく使われる順）
const FALLBACK_PATHS = [
  '/about',
  '/about/',
  '/company',
  '/company/',
  '/about/profile',
  '/company/profile',
  '/company/profile/',
  '/company/about',
  '/profile',
  '/profile/',
  '/corporate',
  '/corporate/',
  '/corporate/profile',
  '/outline',
  '/aboutus',
  '/company-profile',
  '/company_profile',
  '/about-us',
];

// ─── 抽出パターン（コロンあり・なし両対応） ─────────────────
const EMPLOYEE_PATTERNS = [
  /従業員数?\s*[：:\s]\s*([\d,，０-９]+\s*(?:名|人)(?:\s*[（\(][^）\)]+[）\)])?)/,
  /従業員数?\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
  /社員数\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
  /スタッフ数\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
  /職員数\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
  /グループ従業員数?\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
];

const CAPITAL_PATTERNS = [
  // 億・万・千・百を含む表記（例: 1億2,000万円、3,000万円）
  /資本金\s*[：:\s]\s*([０-９\d]{1,4}[,，]?[０-９\d]{0,4}億[０-９\d,，]{0,10}万?円)/,
  /資本金\s*[：:\s]\s*([０-９\d]{1,5}[,，]?[０-９\d]{0,4}万円)/,
  // 数字+カンマのみ（例: 1,000,000円、10000000円）
  /資本金\s*[：:\s]\s*([０-９\d,，]{1,15}円)/,
];

// ─── ユーティリティ ─────────────────────────────────────
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { start: 183, end: 200 };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--start' && args[i + 1]) opts.start = parseInt(args[i + 1], 10);
    if (args[i] === '--end'   && args[i + 1]) opts.end   = parseInt(args[i + 1], 10);
  }
  return opts;
}

function normalizeUrl(raw) {
  let url = (raw || '').trim().replace(/\/$/, '');
  if (!url) return null;
  if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
  return url;
}

function extractFirst(text, patterns) {
  for (const pat of patterns) {
    const m = text.match(pat);
    if (m) return m[1].trim();
  }
  return null;
}

// ─── スクレイピング ─────────────────────────────────────
async function fetchHtml(url) {
  try {
    const res = await axios.get(url, {
      timeout: REQUEST_TIMEOUT_MS,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0',
        'Accept-Language': 'ja,en-US;q=0.9',
        'Accept': 'text/html,application/xhtml+xml',
      },
      maxRedirects: 5,
    });
    return res.data;
  } catch {
    return null;
  }
}

function parseInfo(html) {
  const $ = cheerio.load(html);
  $('script, style, noscript').remove();
  const text = $('body').text().replace(/[ \t]+/g, ' ');
  return {
    employees: extractFirst(text, EMPLOYEE_PATTERNS),
    capital:   extractFirst(text, CAPITAL_PATTERNS),
  };
}

function findCompanyPageLinks(html, baseUrl) {
  const $ = cheerio.load(html);
  const found = [];
  $('a[href]').each((_, el) => {
    const text = $(el).text().trim();
    const href = $(el).attr('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
    const textMatch = COMPANY_PAGE_TEXT_PATTERNS.some((p) => p.test(text));
    const hrefMatch = COMPANY_PAGE_HREF_PATTERNS.some((p) => p.test(href));
    if (textMatch || hrefMatch) {
      try {
        found.push(new URL(href, baseUrl).href);
      } catch { /* 無効なURL */ }
    }
  });
  return [...new Set(found)].slice(0, 8);
}

// E列のURLからトップページのオリジンを導出
function getOrigin(rawUrl) {
  try {
    const u = new URL(rawUrl);
    return u.origin;
  } catch {
    return null;
  }
}

async function scrapeCompany(rawUrl) {
  const baseUrl = normalizeUrl(rawUrl);
  if (!baseUrl) return { employees: null, capital: null };

  // E列URLがサブページの場合もあるので、トップページも試す
  const origin = getOrigin(baseUrl);
  const urlsToTry = [baseUrl];
  if (origin && origin !== baseUrl && origin + '/' !== baseUrl) {
    urlsToTry.push(origin);
  }

  let bestInfo = { employees: null, capital: null };

  for (const tryUrl of urlsToTry) {
    const rootHtml = await fetchHtml(tryUrl);
    if (!rootHtml) continue;

    const info = parseInfo(rootHtml);
    bestInfo.employees = bestInfo.employees || info.employees;
    bestInfo.capital = bestInfo.capital || info.capital;
    if (bestInfo.employees && bestInfo.capital) return bestInfo;

    // ページ内リンクから会社概要ページを自動発見
    const links = findCompanyPageLinks(rootHtml, tryUrl);
    for (const link of links) {
      if (link === tryUrl || link === baseUrl) continue;
      const html = await fetchHtml(link);
      if (!html) continue;
      const info2 = parseInfo(html);
      bestInfo.employees = bestInfo.employees || info2.employees;
      bestInfo.capital = bestInfo.capital || info2.capital;
      if (bestInfo.employees && bestInfo.capital) return bestInfo;
    }
  }

  if (bestInfo.employees || bestInfo.capital) return bestInfo;

  // フォールバックパスを順次試行（オリジンに対して）
  const fallbackBase = origin || baseUrl;
  for (const subpath of FALLBACK_PATHS) {
    const url = fallbackBase + subpath;
    const html = await fetchHtml(url);
    if (!html) continue;
    const info = parseInfo(html);
    bestInfo.employees = bestInfo.employees || info.employees;
    bestInfo.capital = bestInfo.capital || info.capital;
    if (bestInfo.employees || bestInfo.capital) return bestInfo;
  }

  return bestInfo;
}

// ─── Google Sheets 認証（サービスアカウント） ──────────────
async function authorize() {
  const auth = new google.auth.GoogleAuth({
    keyFile: CREDENTIALS_PATH,
    scopes: SCOPES,
  });
  return auth.getClient();
}

// ─── メイン ─────────────────────────────────────────────
async function main() {
  const { start, end } = parseArgs();
  const totalRows = end - start + 1;
  console.log(`\n==============================`);
  console.log(` 企業情報抽出  行 ${start} 〜 ${end}（${totalRows}社）`);
  console.log(`==============================\n`);

  const auth = await authorize();
  const sheets = google.sheets({ version: 'v4', auth });

  const readRange = `${SHEET_NAME}!C${start}:K${end}`;
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: readRange,
  });

  const rows = res.data.values || [];
  const writeBuffer = Array.from({ length: totalRows }, () => ['', '']);

  let successCount = 0;
  let skipCount = 0;

  for (let i = 0; i < totalRows; i++) {
    const row        = rows[i] || [];
    const rowNum     = start + i;
    const company    = row[0]  || '';  // C列
    const url        = row[2]  || '';  // E列（C=0, D=1, E=2）
    const existingJ  = row[7]  || '';  // J列
    const existingK  = row[8]  || '';  // K列

    if (existingJ && existingK) {
      console.log(`[SKIP] 行${rowNum} ${company} — 既存データあり`);
      writeBuffer[i] = [existingJ, existingK];
      skipCount++;
      continue;
    }

    if (!url) {
      console.log(`[SKIP] 行${rowNum} ${company} — URLなし`);
      writeBuffer[i] = [existingJ, existingK];
      skipCount++;
      continue;
    }

    process.stdout.write(`[処理中] 行${rowNum} ${company} ...`);
    const { employees, capital } = await scrapeCompany(url);

    const empVal = employees || existingJ || '';
    const capVal = capital   || existingK || '';

    writeBuffer[i] = [empVal, capVal];

    if (empVal || capVal) {
      successCount++;
      console.log(` ✓ 従業員: ${empVal || '−'} / 資本金: ${capVal || '−'}`);
    } else {
      console.log(` × 未取得`);
    }

    await sleep(REQUEST_DELAY_MS);
  }

  // J列・K列に一括書き込み
  const writeRange = `${SHEET_NAME}!J${start}:K${end}`;
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: writeRange,
    valueInputOption: 'RAW',
    requestBody: { values: writeBuffer },
  });

  console.log(`\n==============================`);
  console.log(` 完了`);
  console.log(` 取得: ${successCount}件 / スキップ: ${skipCount}件 / 未取得: ${totalRows - successCount - skipCount}件`);
  console.log(` 書き込み先: ${writeRange}`);
  console.log(`==============================\n`);
}

main().catch((err) => {
  console.error('\nエラー:', err.message);
  process.exit(1);
});
