const { getGoogleSheetsClient } = require('./sheets_writer');
const fs = require('fs');
const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

(async () => {
    const sheets = await getGoogleSheetsClient();
    const out = [];

    // Sheets list
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    out.push('=== シート一覧 ===');
    for (const s of spreadsheet.data.sheets) {
        out.push(`  - ${s.properties.title} (${s.properties.gridProperties.rowCount} rows)`);
    }

    // Nagoya sheet
    const res = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: 'Webマーケティング_名古屋' });
    const all = res.data.values || [];
    const data = all.slice(1);
    const filled = data.filter(r => (r[2] || '').trim());
    const empty = data.length - filled.length;
    out.push('');
    out.push('=== Webマーケティング_名古屋 ===');
    out.push(`ヘッダー: ${all[0].join(' | ')}`);
    out.push(`データ行: ${data.length}, 企業名あり: ${filled.length}, 空行: ${empty}`);

    let formYes = 0, formNo = 0, ngReason = 0, repName = 0, repDefault = 0, empK = 0, empU = 0;
    for (const r of filled) {
        if ((r[5] || '').trim()) formYes++; else formNo++;
        if ((r[8] || '').trim()) ngReason++;
        if ((r[3] || '').trim() && (r[3] || '').trim() !== 'ご担当者') repName++; else repDefault++;
        const e = (r[9] || '').trim();
        if (e && e !== '不明' && e !== 'null') empK++; else empU++;
    }
    out.push(`フォーム: あり=${formYes}, なし=${formNo}`);
    out.push(`送信不可理由: ${ngReason}件記入済み`);
    out.push(`代表者名: フルネーム=${repName}, ご担当者=${repDefault}`);
    out.push(`従業員数: 取得=${empK}, 不明=${empU}`);

    // 先頭5件
    out.push('');
    out.push('[先頭5件]');
    for (let i = 0; i < Math.min(5, filled.length); i++) {
        const r = filled[i]; 
        out.push(`  #${i + 1}: ${(r[2] || '')} | URL: ${(r[4] || '').substring(0, 50)}`);
    }

    // 末尾5件
    out.push('');
    out.push('[末尾5件 (企業名あり)]');
    for (let i = Math.max(0, filled.length - 5); i < filled.length; i++) {
        const r = filled[i];
        out.push(`  #${i + 1}: ${(r[2] || '')} | URL: ${(r[4] || '').substring(0, 50)}`);
    }

    // Webマーケティング sheet
    const res2 = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID, range: 'Webマーケティング' });
    const all2 = res2.data.values || [];
    const data2 = all2.slice(1);
    const filled2 = data2.filter(r => (r[2] || '').trim());
    out.push('');
    out.push('=== Webマーケティング ===');
    out.push(`データ行: ${data2.length}, 企業名あり: ${filled2.length}`);

    fs.writeFileSync('nagoya_status_clean.txt', out.join('\n'), 'utf-8');
    console.log('Done. nagoya_status_clean.txt に書き出しました');
})().catch(e => console.error(e.message));
