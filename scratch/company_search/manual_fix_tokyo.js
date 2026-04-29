/**
 * manual_fix_tokyo.js - 東京追加分の目視修正
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const SHEET_NAME = 'Webマーケティング';

// 大手企業リスト（追加）
const LARGE_CORPS = [
    'サイバーエージェント', 'レバレジーズ', 'セプテーニ・ホールディングス',
    'デジタルガレージ', 'DACホールディングス', 'イード', 'ドワンゴ',
    'Speee', 'フルスピード', // 重複
];

// 不正企業名パターン
function isInvalidName(name) {
    if (/^株式会社導入事例$/.test(name)) return true;
    if (/^株式会社インタビュー動画$/.test(name)) return true;
    if (/^ACCOUNTHAKUHODO/.test(name)) return true;
    if (name === '株式会社100') return true;
    return false;
}

async function main() {
    const sheets = await getGoogleSheetsClient();
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });
    const allRows = response.data.values || [];
    const dataRows = allRows.slice(1);

    console.log(`全${dataRows.length}件をチェック\n`);

    const deleteIndices = [];
    const seenDomains = new Map(); // ドメイン重複チェック

    for (let i = 0; i < dataRows.length; i++) {
        const name = (dataRows[i][2] || '').trim();
        const url = (dataRows[i][4] || '').trim();
        let domain = '';
        try { domain = new URL(url).hostname.toLowerCase().replace(/^www\./, ''); } catch {}

        // === 大手企業 ===
        if (LARGE_CORPS.some(corp => name.includes(corp))) {
            console.log(`  🗑 #${i+1} [大手企業] "${name}"`);
            deleteIndices.push(i);
            continue;
        }

        // === 不正な企業名 ===
        if (isInvalidName(name)) {
            console.log(`  🗑 #${i+1} [企業名NG] "${name}"`);
            deleteIndices.push(i);
            continue;
        }

        // === URL不一致: ドメインと企業名の乖離が明白 ===
        // レバレジーズ → freelance-hub.jp
        if (name.includes('レバレジーズ') && domain.includes('freelance-hub')) {
            console.log(`  🗑 #${i+1} [URL不一致] "${name}" -> ${domain}`);
            deleteIndices.push(i);
            continue;
        }
        // 富士商事 → aily-lab.co.jp
        if (name.includes('富士商事') && domain.includes('aily-lab')) {
            console.log(`  🗑 #${i+1} [URL不一致] "${name}" -> ${domain}`);
            deleteIndices.push(i);
            continue;
        }
        // クウカン → kukanhokkaido.co.jp (北海道なのに東京エリア)
        if (name.includes('クウカン') && domain.includes('hokkaido')) {
            console.log(`  🗑 #${i+1} [エリア不一致] "${name}" -> ${domain}`);
            deleteIndices.push(i);
            continue;
        }
        // growthseed.jpはフルスピードのメディアだが、別エリアで本体がある
        if (domain.includes('growthseed')) {
            console.log(`  🗑 #${i+1} [重複メディア] "${name}" -> ${domain}`);
            deleteIndices.push(i);
            continue;
        }
        // Faber → fabercompany.co.jp は大手
        if (name.includes('Faber') && domain.includes('fabercompany')) {
            console.log(`  🗑 #${i+1} [大手企業] "${name}"`);
            deleteIndices.push(i);
            continue;
        }
        // 株式会社ブリジア → bridge-a.co.jp (ブリジア ≠ bridge-a? Playwrightでは一致)
        // → 保留（OK）

        // === ドメイン重複チェック ===
        if (domain && seenDomains.has(domain)) {
            console.log(`  🗑 #${i+1} [ドメイン重複] "${name}" (${domain}) 行#${seenDomains.get(domain)}と重複`);
            deleteIndices.push(i);
            continue;
        }
        if (domain) seenDomains.set(domain, i + 1);
    }

    console.log(`\n削除: ${deleteIndices.length}件\n`);

    if (deleteIndices.length > 0) {
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
        const sheet = spreadsheet.data.sheets.find(s => s.properties.title === SHEET_NAME);
        const sheetId = sheet.properties.sheetId;

        const sorted = [...deleteIndices].sort((a, b) => b - a);
        await sheets.spreadsheets.batchUpdate({
            spreadsheetId: SPREADSHEET_ID,
            requestBody: {
                requests: sorted.map(idx => ({
                    deleteDimension: {
                        range: { sheetId, dimension: 'ROWS', startIndex: idx + 1, endIndex: idx + 2 }
                    }
                })),
            },
        });
        console.log(`✅ ${deleteIndices.length}行を削除完了`);
    }

    // 最終件数
    const final = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!B:C`,
    });
    const finalRows = (final.data.values || []).filter(r => r[0] && r[0] !== 'エリア');
    const areas = {};
    finalRows.forEach(r => { areas[r[0]] = (areas[r[0]] || 0) + 1; });
    console.log(`\n=== 最終件数 ===`);
    console.log(`合計: ${finalRows.length}件`);
    Object.entries(areas).forEach(([a, c]) => console.log(`  ${a}: ${c}社`));
}

main().catch(err => { console.error(err.message); process.exit(1); });
