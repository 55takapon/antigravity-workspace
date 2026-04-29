const EMPLOYEE_PATTERNS = [
    /従業員[数]?[：:\s]*[約]?([\d,]+)[名人]/,
    /社員[数]?[：:\s]*[約]?([\d,]+)[名人]/,
    /スタッフ[数]?[：:\s]*[約]?([\d,]+)[名人]/,
    /メンバー[：:\s]*[約]?([\d,]+)[名人]/,
    /([\d,]+)[名人]\s*[（(].*?[正社員|パート|アルバイト]/,
    /人[員数]?[：:\s]*[約]?([\d,]+)/,
    /([\d,]+)\s*(?:名|人)\s*(?:在籍|所属)/,
];

const CAPITAL_PATTERNS = [
    /資本金[：:\s]*([\d,.]+[万億]?円?[^<{\n]*)/,
    /([\d,.]+[万億]円)\s*（.*?資本準備金/,
];

function testEmployee(text) {
    for (const pattern of EMPLOYEE_PATTERNS) {
        const match = text.match(pattern);
        if (match) {
            return parseInt(match[1].replace(/,/g, ''), 10);
        }
    }
    return null;
}

function testCapital(text) {
    for (const pattern of CAPITAL_PATTERNS) {
        const match = text.match(pattern);
        if (match) {
            return match[1].trim();
        }
    }
    return null;
}

const lines = [
    "従業員数 3,172名（2023年3月期）",
    "社員数：約1,000人",
    "メンバー 約50名",
    "資本金：3,000万円",
    "資本金 1億5,000万円",
    "10,000,000円", // パターンに合致しないダミー
];

for (const line of lines) {
    console.log(`[Input] ${line}`);
    console.log(`  Emp: ${testEmployee(line)}`);
    console.log(`  Cap: ${testCapital(line)}`);
}
