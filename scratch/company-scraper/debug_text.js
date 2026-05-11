const axios = require('axios');
const cheerio = require('cheerio');

const TEST_URLS = [
  { name: 'ワンページ', url: 'https://onepage.co.jp/' },
  { name: 'ワンページ(概要)', url: 'https://onepage.co.jp/company-profile/' },
  { name: 'デンコウスタジオ', url: 'https://denkou-studio.com/' },
  { name: 'makotoba', url: 'https://makotoba.co.jp/' },
  { name: 'コレオ', url: 'https://www.choreo.co.jp/' },
  { name: 'WWG', url: 'https://web-wwc.com/' },
];

async function debug(name, url) {
  console.log('\n=== ' + name + ' (' + url + ') ===');
  try {
    const res = await axios.get(url, {
      timeout: 12000,
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0' },
    });
    const $ = cheerio.load(res.data);
    $('script, style, noscript').remove();
    const text = $('body').text().replace(/\s+/g, ' ');

    // 従業員の周辺テキスト
    const idx1 = text.indexOf('従業員');
    if (idx1 >= 0) {
      console.log('[従業員] ' + text.slice(Math.max(0, idx1 - 20), idx1 + 60));
    } else {
      console.log('[従業員] 見つからず');
    }

    // 資本金の周辺テキスト
    const idx2 = text.indexOf('資本金');
    if (idx2 >= 0) {
      console.log('[資本金] ' + text.slice(Math.max(0, idx2 - 20), idx2 + 60));
    } else {
      console.log('[資本金] 見つからず');
    }

    // 社員数の周辺テキスト
    const idx3 = text.indexOf('社員数');
    if (idx3 >= 0) {
      console.log('[社員数] ' + text.slice(Math.max(0, idx3 - 20), idx3 + 60));
    }

    // スタッフの周辺テキスト
    const idx4 = text.indexOf('スタッフ');
    if (idx4 >= 0) {
      console.log('[スタッフ] ' + text.slice(Math.max(0, idx4 - 10), idx4 + 60));
    }
  } catch (e) {
    console.log('FETCH FAILED: ' + e.message);
  }
}

(async () => {
  for (const t of TEST_URLS) {
    await debug(t.name, t.url);
  }
})();
