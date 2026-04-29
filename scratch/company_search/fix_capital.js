/**
 * fix_capital.js - 資本金列の不正データ修正
 * 
 * 資本金の正しいパターン: 数字 + 万円/億円/円 のみ
 * それ以外（文章片、JSON、メールアドレス混入等）は空に
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング_大阪';

/**
 * 資本金の値が有効かを正で判定する
 * 有効パターン: 数字(カンマ区切りOK) + 万円/億円/円/万/億
 */
function isValidCapital(value) {
    if (!value) return false;
    const v = value.trim();
    // 正のパターン: 数字(カンマ区切り) + 万円/億円/円/万/億 のいずれか
    if (/^[\d,]+\s*(万円|億円|円|万|億)$/.test(v)) return true;
    // 数字のみ（円単位の金額）: 6桁以上の数字
    if (/^[\d,]+$/.test(v) && v.replace(/,/g, '').length >= 6) return true;
    // 「非公開」「非開示」は許容
    if (/^非(公開|開示)$/.test(v)) return true;
    
    return false;
}

/**
 * 資本金の値をクリーニングする
 * 余分なテキストを除去して数字+単位のみにする
 */
function cleanCapital(raw) {
    if (!raw) return '';
    let v = raw.trim();
    
    // 既に有効ならそのまま
    if (isValidCapital(v)) return v;
    
    // 先頭の数字+単位部分だけ抽出
    const match = v.match(/^([\d,]+\s*(?:万円|億円|円|万|億))/);
    if (match && isValidCapital(match[1])) return match[1].trim();
    
    // 先頭の純数字（6桁以上）を抽出
    const numMatch = v.match(/^([\d,]+)/);
    if (numMatch) {
        const num = numMatch[1].replace(/,/g, '');
        if (num.length >= 6) return numMatch[1] + '円';
    }
    
    // どれにも合致しない → 不正データ
    return '';
}

async function main() {
    console.log('========================================');
    console.log('  資本金データ品質修正');
    console.log('========================================\n');

    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);
    
    const capitalIdx = header.indexOf('資本金');
    if (capitalIdx < 0) { console.log('資本金列なし'); return; }
    const colLetter = String.fromCharCode(65 + capitalIdx);
    
    console.log(`対象: ${dataRows.length}社 / 資本金列: ${colLetter}列\n`);
    
    let fixed = 0, valid = 0, empty = 0;
    
    for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i];
        const raw = (row[capitalIdx] || '').trim();
        const name = (row[2] || '').trim();
        const sheetRow = i + 2;
        
        if (!raw) { empty++; continue; }
        
        if (isValidCapital(raw)) {
            valid++;
            continue;
        }
        
        // 不正データを修正
        const cleaned = cleanCapital(raw);
        console.log(`[修正] 行${sheetRow} ${name}`);
        console.log(`  修正前: "${raw}"`);
        console.log(`  修正後: "${cleaned || '(空に)'}"` );
        
        await sheets.spreadsheets.values.update({
            spreadsheetId: SPREADSHEET_ID,
            range: `${SHEET_NAME}!${colLetter}${sheetRow}`,
            valueInputOption: 'USER_ENTERED',
            requestBody: { values: [[cleaned]] },
        });
        fixed++;
    }
    
    // 最終確認
    console.log('\n========================================');
    console.log(`  結果: 有効 ${valid}件 / 修正 ${fixed}件 / 空 ${empty}件`);
    console.log('========================================\n');
    
    // 修正後の全件出力
    const finalResp = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const finalData = finalResp.data.values.slice(1);
    console.log('=== 資本金 最終一覧 ===');
    for (let i = 0; i < finalData.length; i++) {
        const nm = (finalData[i][2] || '').trim();
        const cap = (finalData[i][capitalIdx] || '').trim();
        if (cap) {
            const ok = isValidCapital(cap) ? '✅' : '⚠️';
            console.log(`  ${ok} #${i+1} ${nm}: ${cap}`);
        }
    }
}

main().catch(err => { console.error(err); process.exit(1); });
