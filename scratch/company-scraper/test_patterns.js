// 修正後のパターンでマッチするかテスト
const testTexts = [
  '資本金 300万円',
  '資本金 1,000万円',
  '資本金 1,000,000円',
  '資本金：1,000万円',
  '資本金: 5億円',
  '従業員数 100名',
  '従業員数：250名',
  '従業員数 50名（パート含む）',
  '社員数 30名',
  '従業員 15人',
];

const EMPLOYEE_PATTERNS = [
  /従業員数?\s*[：:\s]\s*([\d,，０-９]+\s*(?:名|人)(?:\s*[（\(][^）\)]+[）\)])?)/,
  /従業員数?\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
  /社員数\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
  /スタッフ数\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
  /職員数\s*[：:\s]\s*(?:約\s*)?([\d,，０-９]+\s*(?:名|人)?)/,
];

const CAPITAL_PATTERNS = [
  /資本金\s*[：:\s]\s*([０-９\d][０-９\d億万千百,，\s]*円)/,
  /資本金\s*[：:\s]\s*([０-９\d,，]+\s*(?:億|万)?円)/,
];

function test(text) {
  for (const p of EMPLOYEE_PATTERNS) {
    const m = text.match(p);
    if (m) return '[EMP] ' + text + ' → ' + m[1].trim();
  }
  for (const p of CAPITAL_PATTERNS) {
    const m = text.match(p);
    if (m) return '[CAP] ' + text + ' → ' + m[1].trim();
  }
  return '[MISS] ' + text;
}

testTexts.forEach(t => console.log(test(t)));
