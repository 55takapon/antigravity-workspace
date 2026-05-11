const axios = require('axios');
const cheerio = require('cheerio');

const COMPANIES = [
  { name: 'ワンページ', base: 'https://onepage.co.jp' },
  { name: 'デンコウスタジオ', base: 'https://denkou-studio.com' },
  { name: 'makotoba', base: 'https://makotoba.co.jp' },
  { name: 'コレオ', base: 'https://www.choreo.co.jp' },
  { name: 'WWG', base: 'https://web-wwc.com' },
  { name: 'NextDoor', base: 'http://nextdoorltd.jp' },
  { name: 'エー・シー・プラネット', base: 'https://www.acplanet.co.jp' },
  { name: 'NeviQo', base: 'https://neviqo.co.jp' },
];

const LINK_PATTERNS = [/会社概要/, /企業概要/, /企業情報/, /会社情報/, /about/i, /company/i, /corporate/i];
const HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0' };

async function fetchHtml(url) {
  try {
    const res = await axios.get(url, { timeout: 12000, headers: HEADERS, maxRedirects: 5 });
    return res.data;
  } catch { return null; }
}

async function debugCompany(name, base) {
  console.log('\n========== ' + name + ' ==========');
  const html = await fetchHtml(base + '/');
  if (!html) { console.log('トップページ取得失敗'); return; }

  // 会社概要リンクを探す
  const $ = cheerio.load(html);
  const links = [];
  $('a[href]').each((_, el) => {
    const text = $(el).text().trim();
    const href = $(el).attr('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:')) return;
    if (LINK_PATTERNS.some(p => p.test(text) || p.test(href))) {
      try { links.push({ text, url: new URL(href, base).href }); } catch {}
    }
  });
  const unique = [...new Map(links.map(l => [l.url, l])).values()].slice(0, 3);
  console.log('発見リンク: ' + (unique.length ? unique.map(l => l.text + ' -> ' + l.url).join(' / ') : 'なし'));

  // 各リンクをfetchしてテキスト確認
  for (const link of unique) {
    const h = await fetchHtml(link.url);
    if (!h) { console.log('  [' + link.text + '] fetch失敗'); continue; }
    const $2 = cheerio.load(h);
    $2('script, style, noscript').remove();
    const text = $2('body').text().replace(/\s+/g, ' ');

    for (const kw of ['従業員', '社員数', '資本金', '設立']) {
      const idx = text.indexOf(kw);
      if (idx >= 0) {
        console.log('  [' + kw + '] ' + text.slice(Math.max(0, idx - 10), idx + 80));
      }
    }
  }
}

(async () => {
  for (const c of COMPANIES) {
    await debugCompany(c.name, c.base);
  }
})();
