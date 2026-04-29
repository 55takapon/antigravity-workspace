const { getGoogleSheetsClient } = require('./sheets_writer');
const fs = require('fs');

async function main() {
    const sheets = await getGoogleSheetsClient();
    const r = await sheets.spreadsheets.values.get({
        spreadsheetId: '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk',
        range: 'Webマーケティング!A:F',
    });
    const rows = (r.data.values || []).slice(1);
    const areas = {};
    rows.forEach(x => { const a = (x[1] || '').trim(); if (a) areas[a] = (areas[a] || 0) + 1; });

    let out = '=== 最終結果 ===\n合計: ' + rows.length + '件\n';
    Object.entries(areas).forEach(([a, c]) => { out += '  ' + a + ': ' + c + '社\n'; });
    out += '\n全件リスト:\n';
    rows.forEach((x, i) => {
        const name = (x[2] || '').trim();
        const url = (x[4] || '').trim();
        const form = (x[5] || '').trim();
        let d = '';
        try { d = new URL(url).hostname; } catch {}
        out += '#' + String(i + 1).padStart(3) + ' [' + ((x[1] || '').trim()) + '] ' + name + ' | ' + d + ' | form:' + (form ? 'あり' : 'なし') + '\n';
    });

    fs.writeFileSync('C:/tmp/final_audit.txt', out, 'utf-8');
    console.log(out);
}

main().catch(err => { console.error(err.message); process.exit(1); });
