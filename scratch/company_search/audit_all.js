/**
 * audit_all.js - 全データ精密監査スクリプト
 * 全件の企業名・URL・ドメインを出力し、問題を洗い出す
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング';

async function main() {
    const sheets = await getGoogleSheetsClient();

    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });

    const allRows = response.data.values || [];
    const dataRows = allRows.slice(1);

    console.log(`全${dataRows.length}件を監査\n`);

    // 問題パターン検出
    const GOVT_DOMAINS = ['go.jp', 'lg.jp', 'ed.jp', 'ac.jp'];
    const PORTAL_JUNK_DOMAINS = ['jimoty', 'jmty', 'dairitenkeisyu', 
        'coconala', 'lancers', 'crowdworks', 'hikoma',
        'note.com', 'hatena', 'qiita',
        'slideshare', 'speakerdeck', 'medium.com',
        'soumu.go.jp', 'meti.go.jp', 'kantei.go.jp', 'mhlw.go.jp',
        'impress.co.jp', 'itmedia.co.jp', 'nikkei.com',
        'yahoo.co.jp', 'livedoor.com', 'goo.ne.jp', 'biglobe.ne.jp'];
    
    const issues = [];

    for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i];
        const no = i + 1;
        const area = (row[1] || '').trim();
        const name = (row[2] || '').trim();
        const url = (row[4] || '').trim();
        
        let domain = '';
        try { domain = new URL(url).hostname.toLowerCase(); } catch {}

        const rowIssues = [];

        // 1. 中国語を含む（日本語の漢字として使わない文字）
        if (/[游戏柯伊索]/.test(name)) rowIssues.push('中国語混入');

        // 2. ページタイトル混入（|で区切り）
        if (/\|/.test(name)) rowIssues.push('パイプ文字混入(ページタイトル)');
        if (/の検索結果/.test(name)) rowIssues.push('検索結果タイトル');
        if (/ページ目/.test(name) || /ジモティー/.test(name)) rowIssues.push('掲示板タイトル');

        // 3. 政府・公的ドメイン
        if (GOVT_DOMAINS.some(d => domain.endsWith(d))) rowIssues.push(`公的ドメイン(${domain})`);

        // 4. ポータル/メディアドメイン
        if (PORTAL_JUNK_DOMAINS.some(d => domain.includes(d))) rowIssues.push(`ポータルサイト(${domain})`);

        // 5. 企業名に「所在地」等メタ情報混入
        if (/所在地|住所|電話番号|設立|事業内容/.test(name)) rowIssues.push('メタ情報混入');

        // 6. 法人格除去後の中核名が1文字以下
        const coreName = name.replace(/株式会社|合同会社|有限会社/g, '').trim();
        if (coreName.length <= 1) rowIssues.push(`中核名短すぎ(${coreName})`);

        // 7. 「C株式会社」的な1文字英語+法人格
        if (/^[A-Za-zＡ-Ｚａ-ｚ]株式会社$|^株式会社[A-Za-zＡ-Ｚａ-ｚ]$/.test(name)) rowIssues.push('1文字英字+法人格');

        // 8. 括弧やページ番号
        if (/\(\d+ページ|（\d+ページ/.test(name)) rowIssues.push('ページ番号混入');

        // 9. 記事タイトルパターン
        if (/検索結果|一覧$|ランキング$|おすすめ\d+選|比較\d+選/.test(name)) rowIssues.push('記事タイトル');

        // 10. 長すぎる企業名（30文字超）
        if (name.length > 30) rowIssues.push(`長すぎ(${name.length}文字)`);

        // 11. Web広告代理店・Web... のような記事タイトル風
        if (/^Web[^\s].{15,}/.test(name) && /代理店|おすすめ|会社|まとめ/.test(name)) rowIssues.push('記事タイトル風');

        // 出力
        const status = rowIssues.length > 0 ? `❌ ${rowIssues.join(', ')}` : '✅';
        console.log(`#${String(no).padStart(3)} [${area}]: ${status}`);
        console.log(`      企業名: ${name}`);
        console.log(`      URL:    ${url}`);
        if (rowIssues.length > 0) {
            issues.push({ no, name, url, domain, issues: rowIssues });
        }
        console.log('');
    }

    console.log('════════════════════════════════════════');
    console.log(`  全件数: ${dataRows.length}`);
    console.log(`  問題あり: ${issues.length}件`);
    console.log('════════════════════════════════════════');
    if (issues.length > 0) {
        console.log('\n[問題一覧]');
        for (const i of issues) {
            console.log(`  #${i.no}: "${i.name}" (${i.domain}) - ${i.issues.join(', ')}`);
        }
    }
}

main().catch(err => { console.error(err.message); process.exit(1); });
