/**
 * fix_capital_final.js - 資本金列の最終修正
 * 全行を読み取り、不正データを即修正
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング_大阪';

function isValidCapital(v) {
    if (!v) return false;
    v = v.trim();
    if (/^[\d,]+\s*(万円|億円|円|万|億)$/.test(v)) return true;
    if (/^[\d,]+$/.test(v) && v.replace(/,/g, '').length >= 6) return true;
    if (/^非(公開|開示)$/.test(v)) return true;
    return false;
}

function cleanCapital(raw) {
    if (!raw) return '';
    let v = raw.trim();
    if (isValidCapital(v)) return v;
    // 先頭の数字+単位だけ抽出
    const m = v.match(/^([\d,]+\s*(?:万円|億円|円|万|億))/);
    if (m && isValidCapital(m[1].trim())) return m[1].trim();
    // 先頭の数字6桁以上
    const n = v.match(/^([\d,]+)/);
    if (n && n[1].replace(/,/g, '').length >= 6) return n[1] + '円';
    return '';
}

async function main() {
    const sheets = await getGoogleSheetsClient();
    const resp = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = resp.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);
    const capIdx = header.indexOf('資本金');
    const colLetter = String.fromCharCode(65 + capIdx);
    
    let fixed = 0;
    for (let i = 0; i < dataRows.length; i++) {
        const raw = (dataRows[i][capIdx] || '').trim();
        if (!raw) continue;
        if (isValidCapital(raw)) continue;
        
        const cleaned = cleanCapital(raw);
        const name = (dataRows[i][2] || '').trim();
        const row = i + 2;
        console.log(`[修正] #${i+1} ${name}: "${raw}" -> "${cleaned || '(空)'}"`);
        
        await sheets.spreadsheets.values.update({
            spreadsheetId: SPREADSHEET_ID,
            range: `${SHEET_NAME}!${colLetter}${row}`,
            valueInputOption: 'USER_ENTERED',
            requestBody: { values: [[cleaned]] },
        });
        fixed++;
    }
    
    if (fixed === 0) console.log('不正データなし');
    else console.log(`\n${fixed}件修正完了`);
    
    // 最終確認: 全件出力
    const f = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: SHEET_NAME });
    const fData = f.data.values.slice(1);
    console.log('\n=== 全資本金 最終確認 ===');
    let problems = 0;
    for (let i = 0; i < fData.length; i++) {
        const cap = (fData[i][capIdx] || '').trim();
        if (!cap) continue;
        if (!isValidCapital(cap)) {
            console.log(`⚠️ #${i+1} ${fData[i][2]}: "${cap}"`);
            problems++;
        } else {
            console.log(`✅ #${i+1} ${fData[i][2]}: ${cap}`);
        }
    }
    console.log(`\n残存問題: ${problems}件`);
}

main().catch(e => { console.error(e); process.exit(1); });
