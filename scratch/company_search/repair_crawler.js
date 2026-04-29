const fs = require('fs');
const file = 'C:\\Users\\hangy\\.gemini\\antigravity\\scratch\\company_search\\crawler.js';
let content = fs.readFileSync(file, 'utf-8');

const brokenChunk = `        // リンク一覧を取得
        const links = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
            if (COMPANY_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                companyPageUrl = link.href;
                result.companyPageUrl = link.href;
                break;
            }
        }`;

const fixedChunk = `        // リンク一覧を取得
        const links = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: (a.textContent || '').trim().substring(0, 100),
            }));
        });

        // 問い合わせフォームURLを検出
        for (const link of links) {
            if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                if (link.href && link.href.startsWith('http') && !link.href.match(/\\.(pdf|doc|docx|zip)$/i)) {
                    result.contactFormUrl = link.href;
                    break;
                }
            }
        }

        // 会社概要ページURLを検出
        let companyPageUrl = '';
        for (const link of links) {
            if (COMPANY_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                companyPageUrl = link.href;
                result.companyPageUrl = link.href;
                break;
            }
        }`;

if (content.includes(brokenChunk)) {
    content = content.replace(brokenChunk, fixedChunk);
    fs.writeFileSync(file, content, 'utf-8');
    console.log("Repaired crawler.js logic.");
} else {
    console.log("Broken chunk not found!");
}
