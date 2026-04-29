const fs = require('fs');
const file = 'C:\\Users\\hangy\\.gemini\\antigravity\\scratch\\company_search\\crawler.js';
let content = fs.readFileSync(file, 'utf8');

// 1. NG_INDUSTRY_KEYWORDSの追加
const targetNG = `    // 医療・介護の「実務・システム・検査」系
    '臨床検査', '血液検査', '電子カルテ', 'レセコン', 'PHC', 'ウィーメックス', 'エスアールエル', 'SRL', '介護', '福祉', '訪問看護', 'デイサービス', '老人ホーム', '医療事業開発', 'ケアマックス', 'ドクターソリューション', '医療サポート', 'メディカルフロント', 'メディカルガレージ', 'オクスアイ',
];`;

const newNG = `    // 医療・介護の「実務・システム・検査」系
    '臨床検査', '血液検査', '電子カルテ', 'レセコン', 'PHC', 'ウィーメックス', 'エスアールエル', 'SRL', '介護', '福祉', '訪問看護', 'デイサービス', '老人ホーム', '医療事業開発', 'ケアマックス', 'ドクターソリューション', '医療サポート', 'メディカルフロント', 'メディカルガレージ', 'オクスアイ',

    // ★ v2.8.0 ユーザー指摘による追加（大企業・コンビニ・信販）
    'ジャックス', 'ファミリーマート', 'セブンイレブン', 'ローソン', 'ミニストップ', 'コンビニエンス',
    'クレジットカード', 'カード株式会社', 'JACCS', '信販株式会社',
];`;

if (content.includes(targetNG)) {
    content = content.replace(targetNG, newNG);
    console.log("Applied NG keywords");
}

// 2. 問い合わせフォームURL検出（メインページ）
const targetForm1 = `        // 問い合わせフォームURLを検出
        for (const link of links) {
            if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                result.contactFormUrl = link.href;
                break;
            }
        }`;

const newForm1 = `        // 問い合わせフォームURLを検出
        for (const link of links) {
            if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                if (link.href && link.href.startsWith('http') && !link.href.match(/\\.(pdf|doc|docx|zip)$/i)) {
                    result.contactFormUrl = link.href;
                    break;
                }
            }
        }`;

if (content.includes(targetForm1)) {
    content = content.replace(targetForm1, newForm1);
    console.log("Applied Form1");
}

// 3. 問い合わせフォームURL検出（会社概要ページ）
const targetForm2 = `                // もしメインページでフォームが見つかっていなければ、会社概要ページでも探す
                if (!result.contactFormUrl) {
                    const aboutLinks = await page.evaluate(() => Array.from(document.querySelectorAll('a[href]')).map(a => ({ href: a.href, text: (a.textContent || '').trim().substring(0, 100) })));
                    for (const link of aboutLinks) {
                        if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                            result.contactFormUrl = link.href;
                            console.log(\`  [フォームURL再検出] \${result.contactFormUrl}\`);
                            break;
                        }
                    }
                }`;

const newForm2 = `                // もしメインページでフォームが見つかっていなければ、会社概要ページでも探す
                if (!result.contactFormUrl) {
                    const aboutLinks = await page.evaluate(() => Array.from(document.querySelectorAll('a[href]')).map(a => ({ href: a.href, text: (a.textContent || '').trim().substring(0, 100) })));
                    for (const link of aboutLinks) {
                        if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                            if (link.href && link.href.startsWith('http') && !link.href.match(/\\.(pdf|doc|docx|zip)$/i)) {
                                result.contactFormUrl = link.href;
                                console.log(\`  [フォームURL再検出] \${result.contactFormUrl}\`);
                                break;
                            }
                        }
                    }
                }`;

if (content.includes(targetForm2)) {
    content = content.replace(targetForm2, newForm2);
    console.log("Applied Form2");
}

fs.writeFileSync(file, content, 'utf8');
console.log("All patches applied.");
