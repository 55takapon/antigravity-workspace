// extractCorpName関数のユニットテスト v2
function isValidCompanyName(name) {
  if (!name || name.length < 2 || name.length > 40) return false;
  const INVALID_PATTERNS = [
    /^https?:\/\//, /^@/, /^[\w.-]+\.(com|jp|co\.jp|net|org)$/,
    /SIGN IN/i, /LOG ?IN/i, /SIGN UP/i,
    /Form Builder/i, /Online Form/i,
    /Cookie/i, /Privacy/i, /Terms/i,
    /お知らせ/, /ニュース/, /ブログ/,
    /とのパートナー/, /のお知ら/,
    /当社が/, /薬会社が/, /弊社は/,
    /は様々な/, /を運営/, /サービスを/,
    /なら【/, /導入の依頼/, /相談・比較/,
    /するなら/, /獲得するなら/,
    /企業名[^\u3000\s]/,
    /認知・来店/, /両軸で/,
    /ログインはこちら/, /formerly/i,
    /ブックマーク/, /Bookmark/i,
    /hatena/i, /はてな/,
  ];
  if (INVALID_PATTERNS.some(p => p.test(name))) return false;
  if (name.length > 15 && /[はがをでに].{3,}/.test(name)) return false;
  return true;
}

function extractCorpName(text) {
  if (!text) return '';
  const pre = text.match(/(株式会社|合同会社|有限会社)([A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龯ぁ-んァ-ヶー・＆&\-.]{1,20})/);
  const post = text.match(/([一-龯ぁ-んァ-ヶA-Za-zＡ-Ｚａ-ｚ0-9０-９ー・＆&\-.]{1,15})(株式会社|合同会社|有限会社)(?=[\s|｜／\/（(\n]|$)/);

  let candidates = [];
  if (pre) {
    let name = pre[1] + pre[2];
    name = name.replace(/[（(].*$/, '').trim();
    if (name.length >= 5 && name.length <= 30) candidates.push(name);
  }
  if (post) {
    let name = post[1] + post[2];
    name = name.replace(/^.*(?:なら|では|には|ては|から|する|した|って)/g, '').trim();
    if (!name.match(/^(株式会社|合同会社|有限会社)/)) {
      const reMatch = name.match(/([一-龯ぁ-んァ-ヶA-Za-zＡ-Ｚ0-9０-９ー・]{1,15})(株式会社|合同会社|有限会社)/);
      if (reMatch) name = reMatch[1] + reMatch[2];
    }
    if (name.length >= 5 && name.length <= 30) candidates.push(name);
  }
  candidates.sort((a, b) => a.length - b.length);
  for (const c of candidates) {
    if (isValidCompanyName(c)) return c;
  }
  return '';
}

function extractCorpFromLabel(labelText) {
  if (!labelText) return '';
  let corp = extractCorpName(labelText);
  if (!corp) return '';
  const defurigana = corp.replace(/([A-Za-zＡ-Ｚ0-9０-９])[ァ-ヶー]{4,}$/, '$1');
  if (defurigana.length >= 5 && isValidCompanyName(defurigana)) return defurigana;
  return corp;
}

const tests = [
  // three-dots.co.jp: about_title
  { fn: 'extractCorpName', input: '大阪府大阪市の経営コンサルティング会社ならスリードット株式会社スリードット株式会社', expected: 'スリードット株式会社' },
  // three-dots.co.jp: og:site_name
  { fn: 'extractCorpName', input: 'スリードット株式会社 | 戦略的WEBコンサルティングで圧倒的集客を実現するスリードット', expected: 'スリードット株式会社' },
  // three-dots.co.jp: title (問題の元凶)
  { fn: 'extractCorpName', input: 'デジタルマーケティングコンサルティングならスリードットスリードット株式会社', expected: 'スリードット株式会社' },
  // webgram.jp: about_title
  { fn: 'extractCorpName', input: '会社概要 | 株式会社WEBGRAM', expected: '株式会社WEBGRAM' },
  // webgram.jp: tableMatch (フリガナ対応)
  { fn: 'extractCorpFromLabel', input: '株式会社WEBGRAMウェブグラム', expected: '株式会社WEBGRAM' },
  // cog-web.com: about_title
  { fn: 'extractCorpName', input: '会社概要｜株式会社COGウェブサービス', expected: '株式会社COGウェブサービス' },
  // bankluck-japan.com: about_title
  { fn: 'extractCorpName', input: '会社概要 - 大阪のSEO対策なら株式会社BLJ(ビーエルジェイ)', expected: '株式会社BLJ' },
  // baroque-ad.co.jp: og:site_name
  { fn: 'extractCorpName', input: '株式会社バロック', expected: '株式会社バロック' },
  // baroque-ad.co.jp: about_title
  { fn: 'extractCorpName', input: '会社概要 | 株式会社バロック', expected: '株式会社バロック' },
  // mindfree.jp: tableMatch
  { fn: 'extractCorpFromLabel', input: 'マインドフリー株式会社／MindFree Inc.', expected: 'マインドフリー株式会社' },
  // mindfree.jp: og:site_name (英語のみ→空を期待)
  { fn: 'extractCorpName', input: 'MindFree', expected: '' },
  // 文章は除外すべき
  { fn: 'extractCorpName', input: '株式会社ウェイバックとのパートナーシップのお知ら', expected: '' },
];

let passed = 0, failed = 0;
for (const t of tests) {
  const fn = t.fn === 'extractCorpFromLabel' ? extractCorpFromLabel : extractCorpName;
  const result = fn(t.input);
  const ok = result === t.expected;
  if (ok) {
    passed++;
    console.log('OK  ' + t.fn + ': "' + t.input.substring(0, 50) + '..." => "' + result + '"');
  } else {
    failed++;
    console.log('NG  ' + t.fn + ': "' + t.input.substring(0, 50) + '..." => "' + result + '" (期待: "' + t.expected + '")');
  }
}
console.log('\n結果: ' + passed + '/' + (passed + failed) + ' テスト通過');
