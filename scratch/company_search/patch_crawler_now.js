const fs = require('fs');

const file = 'C:\\Users\\hangy\\.gemini\\antigravity\\scratch\\company_search\\crawler.js';
let content = fs.readFileSync(file, 'utf-8');

// 1. NG_INDUSTRY_KEYWORDS に追加
if (!content.includes('ジャックス')) {
    content = content.replace(/'オクスアイ',\s*\];/, "'オクスアイ',\n    'ジャックス', 'ファミリーマート', 'セブンイレブン', 'ローソン', 'ミニストップ', 'コンビニエンス',\n    'クレジットカード', 'カード株式会社', 'JACCS', '信販株式会社',\n];");
    console.log('NG keywords added.');
}

// 2. 誤った位置（636行目付近）の幻覚ブロックを削除
const hallucinatedStart = `// もしメインページでフォームが見つかっていなければ、会社概要ページでも探す
                if (!result.contactFormUrl) {`;
if (content.indexOf(hallucinatedStart) < content.indexOf('function extractCompanyName')) {
    // extractCompanyNameの定義より前にあるものは誤り
    // 正規表現で削除
    const reg = /\s*\/\/\s*もしメインページでフォームが見つかっていなければ、会社概要ページでも探す\s*if\s*\(!result\.contactFormUrl\)\s*\{\s*const aboutLinks[^]*?\}\s*\}\s*\}/;
    content = content.replace(reg, '');
    console.log('Removed hallucinated block.');
}

// 3. crawler.jsの2つ目のフォーム抽出ブロック（会社概要側）の修正
if (!content.includes('result.contactFormUrl = link.href;\n                                console.log')) {
    const targetReg = /if\s*\(!result\.contactFormUrl\)\s*\{\s*const aboutLinks[^]*?console\.log\(`\s*\[フォームURL再検出\]/g;
    content = content.replace(/if\s*\(\w+\.href\s*&&\s*\w+\.href\.startsWith\('http'\).*?\)/g, ''); // 既存のパッチがあれば削除
    
    // 手動で安全に文字列置換（正規表現）
    content = content.replace(
        /if\s*\(\s*CONTACT_PAGE_PATTERNS\.some\(p => p\.test\(link\.href\) \|\| p\.test\(link\.text\)\)\s*\)\s*\{\s*result\.contactFormUrl = link\.href;\s*console\.log\(/g,
        "if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {\n                            if (link.href && link.href.startsWith('http') && !link.href.match(/\\.(pdf|doc|docx|zip)$/i)) {\n                                result.contactFormUrl = link.href;\n                                console.log("
    );
    // 閉じカッコを1つ追加
    content = content.replace(
        /console\.log\(`\s*\[フォームURL再検出\]\s*\$\{result\.contactFormUrl\}`\);\s*break;\s*\}/g,
        "console.log(`  [フォームURL再検出] ${result.contactFormUrl}`);\n                                break;\n                            }\n                        }"
    );
    console.log('Fixed about page form extraction.');
}

fs.writeFileSync(file, content, 'utf-8');
console.log('Done.');
