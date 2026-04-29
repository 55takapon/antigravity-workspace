/**
 * fix_ng_reasons.js
 * 既に「【営業NG】」として書き込まれている長文の理由を、
 * 一文のみの綺麗な形式に再抽出してシートを上書きする（横展開）
 */
const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
const TARGET_SHEETS = ['Webマーケティング', 'クリニック専門支援']; // 他にあれば追加

function extractSentence(text, keyword) {
    const lines = text.split(/\r?\n/);
    for (let line of lines) {
        if (line.includes(keyword)) {
            const sentences = line.split(/(?<=[。！？])/);
            for (let s of sentences) {
                if (s.includes(keyword)) {
                    s = s.trim();
                    if (s.includes('※') && s.indexOf(keyword) > s.indexOf('※')) {
                        s = s.substring(s.indexOf('※'));
                    }
                    return s;
                }
            }
            return line.trim();
        }
    }
    const idx = text.indexOf(keyword);
    return text.substring(Math.max(0, idx - 40), Math.min(text.length, idx + 40)).trim();
}

async function fixSheet(sheets, sheetName) {
    console.log(`\n=== シート: ${sheetName} の修正を開始 ===`);
    const res = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: sheetName,
    });
    const allRows = res.data.values || [];
    if (allRows.length === 0) return;

    const header = allRows[0];
    const reasonCol = header.indexOf('送信不可理由');
    if (reasonCol < 0) {
        console.log('送信不可理由列なし');
        return;
    }

    const updates = [];
    for (let i = 1; i < allRows.length; i++) {
        const reason = (allRows[i][reasonCol] || '').trim();
        if (reason.startsWith('【営業NG】') && reason.length > 50) {
            // "【営業NG】" を一旦外して本来のテキストから抽出
            const rawText = reason.replace(/^【営業NG】(?:\[.*?\])?\s*/, '');
            // キーワードを推測（基本は「営業」または「セールス」など）
            let keyword = '営業';
            if (rawText.includes('セールス')) keyword = 'セールス';
            if (rawText.includes('売り込み')) keyword = '売り込み';
            if (rawText.includes('勧誘')) keyword = '勧誘';

            const cleanSentence = extractSentence(rawText, keyword);
            // 綺麗になった文を再度フォーマットしてセット
            const newReason = `【営業NG】${cleanSentence}`;

            if (newReason !== reason) {
                // 列番号をアルファベットに変換（A=0, B=1...）
                const colLetter = String.fromCharCode(65 + reasonCol);
                const rowNum = i + 1;
                updates.push({
                    range: `${sheetName}!${colLetter}${rowNum}`,
                    values: [[newReason]],
                    oldReason: reason,
                    newReason: newReason
                });
            }
        }
    }

    console.log(`修正対象: ${updates.length}件`);
    if (updates.length === 0) return;

    for (const u of updates) {
        console.log(`\n[変更前]: ${u.oldReason}`);
        console.log(`[変更後]: ${u.newReason}`);
    }

    // バッチアップデート（Dataの更新）
    const data = updates.map(u => ({ range: u.range, values: u.values }));
    await sheets.spreadsheets.values.batchUpdate({
        spreadsheetId: SPREADSHEET_ID,
        requestBody: {
            valueInputOption: 'USER_ENTERED',
            data: data
        }
    });
    console.log(`\nシート ${sheetName} の更新完了`);
}

async function main() {
    const sheets = await getGoogleSheetsClient();
    for (const sheetName of TARGET_SHEETS) {
        await fixSheet(sheets, sheetName);
    }
}

main().catch(e => console.error(e.message));
