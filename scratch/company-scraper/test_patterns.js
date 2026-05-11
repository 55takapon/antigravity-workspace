const CAPITAL_PATTERNS = [
  /資本金\s*[：:\s]\s*([０-９\d]{1,4}[,，]?[０-９\d]{0,4}億[０-９\d,，]{0,10}万?円)/,
  /資本金\s*[：:\s]\s*([０-９\d]{1,5}[,，]?[０-９\d]{0,4}万円)/,
  /資本金\s*[：:\s]\s*([０-９\d,，]{1,15}円)/,
];

const tests = [
  '資本金 300万円',
  '資本金 1,000万円',
  '資本金：1,000万円',
  '資本金: 5億円',
  '資本金 1億2,000万円',
  '資本金 1,000,000円',
  '資本金 10000000円',
  '資本金 1,0000,000円',    // NeviQoの非標準表記
  '資本金 100万円',
  '資本金 2,565万円',
  // 暴走テスト: 長いテキストの中で止まるか
  '資本金 300万円 代表取締役 山田太郎 事業内容 Web制作',
];

function testCap(text) {
  for (const p of CAPITAL_PATTERNS) {
    const m = text.match(p);
    if (m) return '[OK] ' + text + ' → ' + m[1].trim();
  }
  return '[MISS] ' + text;
}

tests.forEach(t => console.log(testCap(t)));
