/**
 * delete_ng_companies.js
 * 指定した会社名をシートから削除 + 除外リストに追記
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET   = 'Webマーケティング';
const EXCLUDE_SHEET  = '除外リスト';

// 削除対象（名前の部分一致でも検出）
const NG_TARGETS = [
    { match: '飯舘バイオパートナーズ',       reason: 'NG業種:バイオ・農業系' },
    { match: '東京レコードマネジメント',       reason: 'NG業種:文書管理' },
    { match: '東京電設サービス',              reason: 'NG業種:電設工事' },
    { match: 'コーポレートサイト',             reason: '企業名無効:Webサイト用語' },
    { match: 'ＧＤＢＬ',                     reason: 'NG:業種不明・対象外' },
    { match: 'アット東京',                    reason: 'NG業種:データセンター' },
    { match: 'タワーライン',                  reason: 'NG業種:通信インフラ' },
    { match: 'ファミリーネット・ジャパン',      reason: 'NG業種:ISP' },
    { match: 'ホームテック',                  reason: 'NG業種:住宅リフォーム' },
    { match: 'プライムソリューションズ',        reason: 'NG業種:対象外' },
    { match: 'ハウスプラス住宅保証',           reason: 'NG業種:住宅保証' },
    { match: 'Readyfor',                     reason: '企業名無効:クラウドファンディング' },
    { match: 'レディーフォー',                reason: '企業名無効:クラウドファンディング' },
    { match: 'クラウドファンディング',          reason: '企業名無効:プラットフォーム' },
    { match: '東京ドーム',                    reason: 'NG業種:レジャー施設' },
    { match: '京成バス',                      reason: 'NG業種:交通' },
    { match: '東京シティ青果',                reason: 'NG業種:青果卸売' },
    { match: 'URL Shortener',                reason: '企業名無効:ツール名' },
    { match: 'X.gd',                         reason: '企業名無効:ドメイン' },
    { match: '会社概要・アクセス',             reason: '企業名無効:ページタイトル混入' },
    { match: 'デンソー',                      reason: 'NG業種:自動車部品製造大手' },
    { match: '日本建築検査協会',               reason: 'NG業種:検査協会' },
    { match: '岩谷産業',                      reason: 'NG業種:ガス・エネルギー大手' },
    { match: 'プレサンスコーポレーション',      reason: 'NG業種:不動産デベロッパー' },
    { match: '東京センチュリー',               reason: 'NG業種:リース・金融' },
    { match: '双日',                          reason: 'NG業種:総合商社' },
    { match: '建築構造計算ソフトウェア',        reason: '企業名無効:ページタイトル混入' },
    { match: 'ユニオンシステム',               reason: 'NG業種:建築CADソフト' },
    { match: 'Kokusai',                       reason: 'NG業種:対象外(業種不明)' },
    { match: '株式会社日新',                   reason: 'NG:ページタイトル混入、業種不明' },
];

async function main() {
    const sheets = await getGoogleSheetsClient();

    // 1. シート全件取得
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET,
    });
    const allRows = res.data.values || [];
    const header  = allRows[0];
    const nameCol = header.indexOf('企業名');
    const urlCol  = header.indexOf('ホームページURL');

    // 2. 削除対象行を特定
    const toDelete = [];
    for (let i = 1; i < allRows.length; i++) {
        const row    = allRows[i];
        const name   = (row[nameCol] || '').trim();
        const url    = (row[urlCol]  || '').trim();
        const rowNum = i + 1;

        for (const target of NG_TARGETS) {
            if (name.includes(target.match) || url.includes(target.match)) {
                toDelete.push({ rowNum, name, url, reason: target.reason });
                break;
            }
        }
    }

    console.log(`\n削除対象: ${toDelete.length}件`);
    toDelete.forEach(r => console.log(`  行${r.rowNum}: 「${r.name}」→ ${r.reason}`));

    if (toDelete.length === 0) { console.log('削除対象なし'); return; }

    // 3. 除外リストに追記
    const exRes = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: EXCLUDE_SHEET,
    });
    const existingNames = new Set(
        (exRes.data.values || []).slice(1).map(r => (r[0] || '').trim())
    );
    const today = new Date().toLocaleDateString('ja-JP');
    const toAdd = toDelete
        .filter(r => r.name && !existingNames.has(r.name))
        .map(r => [r.name, '', r.url, r.reason, today]);

    if (toAdd.length > 0) {
        await sheets.spreadsheets.values.append({
            spreadsheetId: SPREADSHEET_ID,
            range: `${EXCLUDE_SHEET}!A:E`,
            valueInputOption: 'RAW',
            requestBody: { values: toAdd },
        });
        console.log(`\n除外リストに${toAdd.length}件追記完了`);
    }

    // 4. シートIDを取得して行削除
    const meta = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
    const sheet = meta.data.sheets.find(s => s.properties.title === TARGET_SHEET);
    const sheetId = sheet.properties.sheetId;

    const deleteRequests = [...toDelete]
        .sort((a, b) => b.rowNum - a.rowNum)  // 降順（後ろから削除）
        .map(r => ({
            deleteDimension: {
                range: {
                    sheetId,
                    dimension: 'ROWS',
                    startIndex: r.rowNum - 1,
                    endIndex: r.rowNum,
                },
            },
        }));

    await sheets.spreadsheets.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        requestBody: { requests: deleteRequests },
    });
    console.log(`\nシートから${toDelete.length}行を削除完了`);
}

main().catch(e => { console.error(e.message); process.exit(1); });
