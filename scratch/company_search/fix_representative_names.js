/**
 * fix_representative_names.js - D列（代表者名）の全件クリーニング
 *
 * 既存シートのD列に残存しているゴミ（役職切れ端・経歴・人名以外）を
 * cleanRepresentativeName → isJapanesePersonName で判定し、
 * NG のものを「ご担当者」に置換する。
 *
 * 使い方:
 *   node fix_representative_names.js                    # Webマーケティング（デフォルト）
 *   node fix_representative_names.js --sheet クリニック専門支援
 *   node fix_representative_names.js --dry-run          # 確認のみ
 */

const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';

// 全シートを対象にする（--sheet 指定があればそのシートのみ）
const ALL_SHEETS = [
    'Webマーケティング',
    'Webマーケティング_名古屋',
    'クリニック専門支援',
];

const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
let targetSheets = ALL_SHEETS;
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--sheet' && args[i + 1]) { targetSheets = [args[i + 1]]; i++; }
}

// crawler.js の関数を再利用
const { cleanRepresentativeName, isJapanesePersonName } = require('./crawler');

/**
 * 代表者名として絶対にNGな文字列を独立チェック
 * （cleanRepresentativeName後でもすり抜けるもの用）
 */
function isInvalidRepresentativeName(name) {
    if (!name || name.trim() === '') return true;
    const n = name.trim();

    // 「ご担当者」はすでにデフォルト値なので OK
    if (n === 'ご担当者') return false;

    // 完全一致でNG確定のラベル語
    const LABEL_WORDS = [
        '経歴', 'プロフィール', '代表取締役', '社長', '会長', '理事長',
        '代表者', '担当者', '代表', '氏名', '氏', '役職',
        '企業名', '会社名', '会社情報', '企業情報',
    ];
    if (LABEL_WORDS.includes(n)) return true;

    // 先頭が「長」+スペース（役職の切れ端: 「長 林順之亮」等）
    if (/^長[\s　]/.test(n)) return true;

    // 先頭が「氏」「様」等の敬称
    if (/^[氏様さん御]/.test(n)) return true;

    // 文章片（助詞が含まれる）
    if (/[はがをでにとものへ]/.test(n) && n.length > 4) return true;

    // カタカナ2文字以上連続（=役職・サービス名の可能性）
    if (/[ァ-ヶー]{2,}/.test(n)) return true;

    // 英数字が含まれる（=URL・コード混入）
    if (/[a-zA-Z0-9]/.test(n)) return true;

    // 10文字超（=文章片の可能性大）
    if (n.length > 10) return true;

    // 人名判定（正判定）
    const cleaned = cleanRepresentativeName(n);
    if (!cleaned) return true;
    if (!isJapanesePersonName(cleaned)) return true;

    return false;
}

async function processSheet(sheets, sheetName) {
    console.log(`\n=== シート: ${sheetName} ===`);
    // crawler.jsのキャッシュを毎回クリアして最新版を使用
    delete require.cache[require.resolve('./crawler')];
    const { cleanRepresentativeName, isJapanesePersonName } = require('./crawler');

    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });

    const allRows = res.data.values || [];
    if (allRows.length <= 1) { console.log('  データなし'); return 0; }

    const header = allRows[0];
    const nameCol = header.indexOf('代表者名');
    const compCol = header.indexOf('企業名');

    if (nameCol < 0) { console.log('  「代表者名」列が見つかりません。スキップ。'); return 0; }

    const fixes = [];

    for (let i = 1; i < allRows.length; i++) {
        const row    = allRows[i];
        const raw    = (row[nameCol] || '').trim();
        const comp   = (row[compCol] || '').trim();
        const rowNum = i + 1;

        if (!raw || raw === 'ご担当者') continue;

        // cleanRepresentativeName でノイズ除去後に再判定
        const cleaned = cleanRepresentativeName(raw);
        if (isInvalidRepresentativeName(raw) || !cleaned) {
            console.log(`  🔧 行${rowNum}: [${comp}] 「${raw}」→「ご担当者」`);
            fixes.push({ rowNum, nameCol });
        } else if (cleaned !== raw) {
            // ノイズが除去されてクリーンな名前になった場合は修正値を書き込む
            console.log(`  ✂️  行${rowNum}: [${comp}] 「${raw}」→「${cleaned}」`);
            fixes.push({ rowNum, nameCol, value: cleaned });
        }
    }

    console.log(`  修正対象: ${fixes.length}件`);
    if (fixes.length === 0) { console.log('  ✅ 問題なし'); return 0; }
    if (isDryRun) { console.log('  [ドライラン] 書き込みスキップ'); return fixes.length; }

    const colLetter = String.fromCharCode(65 + nameCol);
    for (const fix of fixes) {
        await sheets.spreadsheets.values.update({
            spreadsheetId: SPREADSHEET_ID,
            range: `${sheetName}!${colLetter}${fix.rowNum}`,
            valueInputOption: 'RAW',
            requestBody: { values: [[fix.value ?? 'ご担当者']] },
        });
    }
    console.log(`  ✅ ${fixes.length}件を修正しました。`);
    return fixes.length;
}

async function main() {
    console.log('========================================');
    console.log('  D列（代表者名）全件クリーニング');
    console.log(`  モード: ${isDryRun ? 'ドライラン' : '本番'}`);
    console.log(`  対象: ${targetSheets.join(', ')}`);
    console.log('========================================');

    const sheets = await getGoogleSheetsClient();
    let total = 0;
    for (const sheetName of targetSheets) {
        total += await processSheet(sheets, sheetName);
    }

    console.log(`\n========================================`);
    console.log(`  合計修正: ${total}件`);
    console.log(`========================================`);
}

main().catch(e => { console.error(e); process.exit(1); });
