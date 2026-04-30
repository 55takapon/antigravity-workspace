/**
 * check_name_url_match.js
 * 指定シートの対象行について、URLにアクセスし、企業名がサイト内に存在するかチェックする
 */
const { getGoogleSheetsClient } = require('./sheets_writer');
const https = require('https');
const http = require('http');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング_名古屋';

// URLからHTMLを取得するヘルパー関数
function fetchHtml(urlStr) {
    return new Promise((resolve) => {
        if (!urlStr || !urlStr.startsWith('http')) {
            return resolve('');
        }
        const client = urlStr.startsWith('https') ? https : http;
        const req = client.get(urlStr, {
            timeout: 5000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                // リダイレクトは1回だけ追う
                const redirectUrl = new URL(res.headers.location, urlStr).href;
                return resolve(fetchHtml(redirectUrl));
            }
            
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => resolve(data));
        });

        req.on('error', () => resolve(''));
        req.on('timeout', () => { req.destroy(); resolve(''); });
    });
}

// 法人格を削除したコアの社名を取得する
function getCoreName(companyName) {
    return companyName.replace(/(株式会社|合同会社|有限会社|一般社団法人|財団法人)/g, '').trim();
}

async function main() {
    console.log(`=== ${TARGET_SHEET} 行2-86の社名・URL一致チェック ===`);
    const sheets = await getGoogleSheetsClient();
    
    // 行2〜86（インデックスでいうとA2:I86）を取得
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${TARGET_SHEET}!A2:E86`,
    });

    const rows = res.data.values || [];
    console.log(`対象件数: ${rows.length}件`);

    const mismatches = [];

    // 順次処理（一気にやるとブロックされる可能性があるので直列で）
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const rowNum = i + 2; // A2から始まるのでインデックス+2
        const companyName = (row[2] || '').trim(); // C列
        const url = (row[4] || '').trim(); // E列

        if (!companyName || !url) continue;

        process.stdout.write(`行${rowNum}: ${companyName} (${url}) をチェック中... `);

        const html = await fetchHtml(url);
        if (!html) {
            console.log('❌ サイトアクセス不可');
            mismatches.push({ row: rowNum, name: companyName, url, reason: 'アクセス不可' });
            continue;
        }

        // HTMLタグを除去してテキスト化（簡易）
        const text = html.replace(/<[^>]*>?/gm, ' ');
        const coreName = getCoreName(companyName);

        // フルネームが含まれているか、またはコア社名が含まれているか
        if (text.includes(companyName) || text.includes(coreName)) {
            console.log('✅ 一致');
        } else {
            console.log('⚠️ 不一致疑い');
            mismatches.push({ row: rowNum, name: companyName, url, reason: 'サイト内に社名なし' });
        }
        
        // サーバー負荷軽減のためのウェイト
        await new Promise(r => setTimeout(r, 500));
    }

    console.log('\n=== 🚨 不一致疑い（またはアクセス不可）のリスト ===');
    if (mismatches.length === 0) {
        console.log('不一致疑いはありませんでした！🎉');
    } else {
        console.table(mismatches);
    }
}

main().catch(e => console.error('エラー:', e.message));
