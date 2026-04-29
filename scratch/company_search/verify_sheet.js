/**
 * verify_sheet.js - 全データダンプ & 1件ずつ目視レベル検証
 */
const { getGoogleSheetsClient } = require('./sheets_writer');
const { isValidCompanyName } = require('./crawler');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング';

function normalizeDomain(url) {
    if (!url) return '';
    try {
        const u = new URL(url);
        return u.hostname.replace(/^(www|corp|en|ja|jp|info)\./i, '').toLowerCase();
    } catch { return ''; }
}

function normalizeCoreName(name) {
    if (!name) return '';
    return name
        .replace(/株式会社|合同会社|有限会社/g, '')
        .replace(/[Ａ-Ｚａ-ｚ０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
        .toLowerCase()
        .replace(/[\s・\-_.&＆　]/g, '')
        .trim();
}

async function main() {
    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const dataRows = allRows.slice(1);

    console.log(`全${dataRows.length}件を1件ずつ検証\n`);

    const domainSet = new Map();
    const nameSet = new Map();
    const issues = [];

    for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i];
        const no = i + 1;
        const name = (row[2] || '').trim();
        const rep = (row[3] || '').trim();
        const url = (row[4] || '').trim();
        const emp = (row[9] || '').trim();
        const domain = normalizeDomain(url);
        const normName = normalizeCoreName(name);
        const rowIssues = [];

        // A: 企業名チェック
        if (!name) rowIssues.push('企業名空');
        else if (!isValidCompanyName(name)) rowIssues.push('企業名無効');
        // 追加: 企業名に怪しいパターンがないか手動チェック
        if (name && (
            /[。、！？!?]/.test(name) ||         // 句読点
            name.length > 30 ||                 // 長すぎ
            /https?:/.test(name) ||             // URL混入
            /\d{4}年/.test(name) ||             // 年号
            /\d{4}$/.test(name) ||              // 末尾4桁数字
            /サービス$/.test(name) ||           // サービス名
            /サイト$/.test(name) ||             // サイト名
            /ページ$/.test(name) ||             // ページ名
            /センター$/.test(name) && !/株式会社|合同会社|有限会社/.test(name) || // センター（法人格なし）
            /[（(].+[)）]/.test(name) ||        // 括弧付き
            /\s{2,}/.test(name)                 // 連続スペース
        )) {
            rowIssues.push('要注意パターン検出');
        }

        // B: 重複チェック
        if (domain) {
            if (domainSet.has(domain)) rowIssues.push(`ドメイン重複(#${domainSet.get(domain)})`);
            else domainSet.set(domain, no);
        }
        if (normName && normName.length >= 2) {
            if (nameSet.has(normName)) rowIssues.push(`名前重複(#${nameSet.get(normName)})`);
            else {
                // 部分一致
                for (const [existing, existNo] of nameSet) {
                    if (existing.length >= 3 && normName.length >= 3 &&
                        (normName.includes(existing) || existing.includes(normName))) {
                        rowIssues.push(`部分一致(#${existNo}:${existing})`);
                        break;
                    }
                }
                nameSet.set(normName, no);
            }
        }

        // C: 代表者名チェック
        if (rep && rep !== 'ご担当者') {
            if (/[はがをでにの].{3,}|しました|します|https?:|www\.|\.com|\.jp|会社|ホームページ/.test(rep)) {
                rowIssues.push(`代表者名異常:"${rep}"`);
            }
        }

        const status = rowIssues.length > 0 ? '⚠️ ' + rowIssues.join(', ') : '✅';
        const empStr = emp || '不明';
        console.log(`#${String(no).padStart(3)}: ${status}`);
        console.log(`      企業名: ${name}`);
        console.log(`      代表者: ${rep || 'ご担当者'}`);
        console.log(`      URL:    ${url}`);
        console.log(`      従業員: ${empStr}`);
        if (rowIssues.length > 0) issues.push({ no, name, issues: rowIssues });
        console.log('');
    }

    console.log('════════════════════════════════════════');
    console.log('  最終検証結果');
    console.log('════════════════════════════════════════');
    console.log(`  全件数: ${dataRows.length}`);
    console.log(`  問題あり: ${issues.length}件`);
    if (issues.length > 0) {
        console.log('\n  [問題のある行]');
        for (const i of issues) {
            console.log(`    #${i.no}: "${i.name}" - ${i.issues.join(', ')}`);
        }
    } else {
        console.log('\n  ✅ 全件問題なし');
    }
}

main().catch(err => { console.error(err); process.exit(1); });
