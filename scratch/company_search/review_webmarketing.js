/**
 * review_webmarketing.js
 * 
 * Webマーケティングシートを全件精査し、
 * 不適切な会社を除外リストへ登録 + シートから削除する
 */

const { getGoogleSheetsClient } = require('./sheets_writer');
const { isNGIndustry, isValidCompanyName, isListedCorporation } = require('./crawler');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEET = 'Webマーケティング';
const EXCLUDE_SHEET = '除外リスト';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 追加の除外判定（NG業種に加えて業種別チェック）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// 業種・属性として明らかに対象外のキーワード
const MANUAL_NG_KEYWORDS = [
    // 大手・上場企業グループ名
    'トヨタ', '日産', 'ホンダ', 'ソニー', 'パナソニック', '富士通', '東芝', '日立',
    'NTT', 'docomo', 'ドコモ', 'ソフトバンク', 'KDDI', 'au',
    '電通', '博報堂', 'ADK', 'オグルヴィ',
    'マイナビ', 'リクルート', 'パーソル', 'テンプスタッフ', 'ランスタッド',
    '三菱', '三井', '住友', '野村', '大和証券',
    // 不動産仲介大手
    'エイブル', 'アパマン', 'ミニミニ', 'ピタットハウス', 'センチュリー21', 'スターツ',
    // スポーツ・球団
    '野球団', '球団', 'フットボールクラブ', 'バスケット', 'サッカークラブ',
    // 出版・メディア
    'ガイド社', '出版社', '新聞社', '放送局', '雑誌社', 'テレビ',
    // 製造業
    '製作所', '製造所', '合金', '製鋼', '鋳造', '鍛造',
    // ガス・エネルギー
    '原燃', '発電', '送電', '原子力', 'エネルギー株式会社',
    // 行政・公的
    '公社', '財団法人', '社団法人', '独立行政法人',
    // 求人・転職（会社自体がそれ）
    'ジョブ', 'キャリア採用', '人材センター',
    // EC・ショッピング
    'ジモティー', 'メルカリ', 'ヤフオク',
    // 水産・農業
    '水産', '漁業', '農協', '畜産',
    // 大学・学術
    '大学', '専門学校', '学校法人',
];

// URLで判定する大手ドメイン
const NG_DOMAINS = [
    'toyota.co.jp', 'honda.co.jp', 'sony.com', 'fujitsu.com',
    'ntt.com', 'ntt-west.co.jp', 'ntt-east.co.jp', 'docomo.ne.jp',
    'softbank.co.jp', 'panasonic.com', 'sharp.co.jp',
    'hitachi.co.jp', 'toshiba.co.jp', 'mitsubishi.co.jp',
    'dentsu.co.jp', 'hakuhodo.co.jp',
    'mynavi.jp', 'mynavi.co.jp', 'recruit.co.jp', 'rikunabi.com',
    'able.co.jp', 'apaman.jp', 'minimini.co.jp',
    'jmty.jp', 'mercari.com',
    'npb.or.jp', 'jleague.jp',
];

function isNGByName(name) {
    if (!name) return { ng: true, reason: '企業名なし' };
    if (!isValidCompanyName(name)) return { ng: true, reason: '企業名無効' };
    
    for (const kw of MANUAL_NG_KEYWORDS) {
        if (name.includes(kw)) return { ng: true, reason: `NGキーワード「${kw}」` };
    }
    
    const industryCheck = isNGIndustry(name);
    if (industryCheck.blocked) return { ng: true, reason: `NG業種: ${industryCheck.reason}` };
    
    if (isListedCorporation(name)) return { ng: true, reason: '上場企業' };
    
    return { ng: false };
}

function isNGByUrl(url) {
    if (!url) return { ng: false };
    try {
        const hostname = new URL(url).hostname.toLowerCase();
        for (const d of NG_DOMAINS) {
            if (hostname.includes(d)) return { ng: true, reason: `NGドメイン: ${d}` };
        }
    } catch {}
    return { ng: false };
}

async function main() {
    const sheetsClient = await getGoogleSheetsClient();

    // 1. Webマーケティングシート全件取得
    console.log(`\n[1] ${TARGET_SHEET} シートを全件取得中...`);
    const res = await sheetsClient.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: TARGET_SHEET,
    });
    const allRows = res.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);

    // 列インデックス確認
    const nameCol   = header.indexOf('企業名');
    const urlCol    = header.indexOf('ホームページURL');
    const industryCol = header.indexOf('業種');
    console.log(`  全${dataRows.length}行 | 企業名列:${nameCol} URL列:${urlCol} 業種列:${industryCol}`);

    // 2. 判定
    console.log('\n[2] 全件精査中...');
    const ngRows = [];     // 除外すべき行（シート行番号と内容）
    const keepRows = [];   // 継続する行

    for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i];
        const rowNum = i + 2; // スプレッドシート行番号
        const name    = (row[nameCol] || '').trim();
        const url     = (row[urlCol] || '').trim();
        const industry = (row[industryCol] || '').trim();

        const nameCheck = isNGByName(name);
        const urlCheck  = isNGByUrl(url);

        if (nameCheck.ng || urlCheck.ng) {
            const reason = nameCheck.ng ? nameCheck.reason : urlCheck.reason;
            ngRows.push({ rowNum, name, url, reason });
            console.log(`  🚫 行${rowNum}: 「${name}」 → ${reason}`);
        } else {
            keepRows.push({ rowNum, name, url });
        }
    }

    console.log(`\n[結果] NG: ${ngRows.length}件 / 継続: ${keepRows.length}件`);

    if (ngRows.length === 0) {
        console.log('除外対象なし。終了します。');
        return;
    }

    // 3. 除外リストシートに追記
    console.log(`\n[3] ${EXCLUDE_SHEET} シートに${ngRows.length}件を追記中...`);
    const excludeRes = await sheetsClient.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: EXCLUDE_SHEET,
    });
    const excludeRows = excludeRes.data.values || [];
    // 除外リストの現在のドメインセット（重複チェック用）
    const existingInExclude = new Set(
        excludeRows.slice(1).map(r => (r[1] || '').trim().toLowerCase())
    );

    const toAdd = [];
    for (const ng of ngRows) {
        let domain = '';
        try { domain = new URL(ng.url).hostname.replace(/^www\./, ''); } catch {}
        if (!domain || existingInExclude.has(domain)) {
            console.log(`  スキップ（既存or URL不明）: ${ng.name}`);
            continue;
        }
        toAdd.push([ng.name, domain, ng.url, ng.reason, new Date().toLocaleDateString('ja-JP')]);
        existingInExclude.add(domain);
    }

    if (toAdd.length > 0) {
        await sheetsClient.spreadsheets.values.append({
            spreadsheetId: SPREADSHEET_ID,
            range: `${EXCLUDE_SHEET}!A:E`,
            valueInputOption: 'RAW',
            requestBody: { values: toAdd },
        });
        console.log(`  ✅ ${toAdd.length}件を除外リストに追加`);
    }

    // 4. Webマーケティングシートから対象行を削除
    // ★ 行番号を降順にして後ろから削除（行番号がずれないように）
    console.log(`\n[4] ${TARGET_SHEET} シートから${ngRows.length}行を削除中...`);

    // シートIDを取得
    const spreadsheet = await sheetsClient.spreadsheets.get({
        spreadsheetId: SPREADSHEET_ID,
    });
    const sheet = spreadsheet.data.sheets.find(s => s.properties.title === TARGET_SHEET);
    if (!sheet) {
        console.error('シートが見つかりません');
        return;
    }
    const sheetId = sheet.properties.sheetId;

    // 降順ソートして後ろから削除
    const sortedNgRows = [...ngRows].sort((a, b) => b.rowNum - a.rowNum);
    const deleteRequests = sortedNgRows.map(ng => ({
        deleteDimension: {
            range: {
                sheetId,
                dimension: 'ROWS',
                startIndex: ng.rowNum - 1, // 0-indexed
                endIndex: ng.rowNum,       // exclusive
            },
        },
    }));

    // バッチで削除
    await sheetsClient.spreadsheets.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        requestBody: { requests: deleteRequests },
    });
    console.log(`  ✅ ${ngRows.length}行の削除完了`);

    // 5. 最終サマリー
    console.log('\n========================================');
    console.log('  精査完了');
    console.log('========================================');
    console.log(`  除外・削除: ${ngRows.length}件`);
    console.log(`  除外リスト追記: ${toAdd.length}件`);
    console.log(`  継続（残存）: ${keepRows.length}件`);
    console.log('\n[除外一覧]');
    for (const ng of ngRows) {
        console.log(`  行${ng.rowNum}: ${ng.name} | ${ng.reason}`);
    }
}

main().catch(err => {
    console.error('Fatal:', err);
    process.exit(1);
});
