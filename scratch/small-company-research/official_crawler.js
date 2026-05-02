/**
 * official_crawler.js
 * 企業の公式サイトをクロールし、品質ゲートに必要な情報を収集する。
 */

const { chromium } = require('playwright-extra');

const CONTACT_PATTERNS = [/contact/i, /inquiry/i, /form/i, /お問い?合わせ/, /お問合せ/, /ご相談/, /ご依頼/, /見積/, /資料請求/, /entry/i, /無料相談/];
const COMPANY_PATTERNS = [/company/i, /about/i, /corporate/i, /profile/i, /outline/i, /会社概要/, /会社案内/, /会社情報/, /企業情報/, /企業概要/, /プロフィール/];
const SERVICE_PATTERNS = [/service/i, /solution/i, /business/i, /事業内容/, /サービス/, /事業紹介/, /ソリューション/];

const EXCLUDE_PATHS = [
    '/case', '/cases', '/works', '/results', '/portfolio', '/achievements', '/voice',
    '/blog', '/column', '/article', '/media', '/magazine',
    '/news', '/topics', '/info', '/press',
    '/recruit', '/careers', '/jobs',
    '/archives', '/entry', '/guide'
];

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function isExcludedPath(urlStr) {
    try {
        const url = new URL(urlStr);
        const path = url.pathname.toLowerCase();
        
        // 年月形式（/2024/03/等）
        if (/\/\d{4}\/\d{2}\//.test(path)) return true;
        
        for (const ex of EXCLUDE_PATHS) {
            if (path.startsWith(ex) || path.includes(ex + '/')) return true;
        }
        return false;
    } catch { return true; }
}

async function extractTextFromPage(page) {
    return await page.evaluate(() => {
        // 除外要素を一時的に削除（クローンに対して行うのが理想だが簡易的に）
        const clone = document.body.cloneNode(true);
        const excludes = clone.querySelectorAll('nav, header, footer, aside, .sidebar, .widget, .ad, .sns, .share, .pagination');
        excludes.forEach(el => el.remove());
        return clone.innerText || '';
    });
}

/**
 * 公式サイトをクロールする
 * @param {import('playwright').Page} page 
 * @param {string} url 
 */
async function crawlOfficialSite(page, url) {
    const result = {
        mainText: '',
        contactUrl: '',
        capitalText: '',
        representative: '', // 必要に応じて上書き
    };

    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await delay(2000);

        // トップページのテキスト抽出
        let text = await extractTextFromPage(page);
        result.mainText += text + '\n';

        // リンク収集
        const links = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: (a.textContent || '').trim().substring(0, 100)
            }));
        });

        let companyUrl = '';
        let serviceUrl = '';

        for (const link of links) {
            if (!link.href.startsWith('http') || link.href.match(/\.(pdf|jpg|png|zip)$/i)) continue;
            
            // 問い合わせURL
            if (!result.contactUrl && CONTACT_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                result.contactUrl = link.href;
            }
            // 会社概要URL
            if (!companyUrl && COMPANY_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                companyUrl = link.href;
            }
            // サービスURL
            if (!serviceUrl && SERVICE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                serviceUrl = link.href;
            }
        }

        // サービスページクロール
        if (serviceUrl && serviceUrl !== url && !isExcludedPath(serviceUrl)) {
            try {
                await page.goto(serviceUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
                await delay(1500);
                const sText = await extractTextFromPage(page);
                result.mainText += sText + '\n';
            } catch (e) { /* ignore */ }
        }

        // 会社概要ページクロール
        if (companyUrl && companyUrl !== url && companyUrl !== serviceUrl && !isExcludedPath(companyUrl)) {
            try {
                await page.goto(companyUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
                await delay(1500);
                const cText = await extractTextFromPage(page);
                result.mainText += cText + '\n';

                // 資本金と代表者を簡易抽出（テーブルから）
                const tableData = await page.evaluate(() => {
                    const res = {};
                    document.querySelectorAll('table tr').forEach(tr => {
                        const th = tr.querySelector('th');
                        const td = tr.querySelector('td');
                        if (th && td) {
                            const key = th.textContent.trim().replace(/\s+/g, '');
                            const val = td.textContent.trim();
                            res[key] = val;
                        }
                    });
                    return res;
                });

                if (tableData['資本金']) result.capitalText = tableData['資本金'];
                if (tableData['代表者'] || tableData['代表取締役']) {
                    result.representative = tableData['代表者'] || tableData['代表取締役'];
                }
            } catch (e) { /* ignore */ }
        }

    } catch (e) {
        console.log(`[Crawler Error] ${url} - ${e.message.substring(0, 50)}`);
    }

    return result;
}

module.exports = { crawlOfficialSite };
