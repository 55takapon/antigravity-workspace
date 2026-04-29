/**
 * rename_sheet.js - シート名を変更するユーティリティ
 */
const { getGoogleSheetsClient } = require('./sheets_writer');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const OLD_NAME = 'Webマーケティング_大阪';
const NEW_NAME = 'Webマーケティング';

async function main() {
    const configPath = path.join(__dirname, 'config.yaml');
    const config = yaml.load(fs.readFileSync(configPath, 'utf-8'));
    const spreadsheetId = config.output.spreadsheet_id;

    const sheets = await getGoogleSheetsClient();

    // シート一覧を取得
    const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId });
    const targetSheet = spreadsheet.data.sheets.find(s => s.properties.title === OLD_NAME);

    if (!targetSheet) {
        console.log(`シート「${OLD_NAME}」が見つかりません。`);
        // 既にリネーム済みかチェック
        const alreadyRenamed = spreadsheet.data.sheets.find(s => s.properties.title === NEW_NAME);
        if (alreadyRenamed) {
            console.log(`シート「${NEW_NAME}」は既に存在します。リネーム済みです。`);
        } else {
            console.log('既存シート一覧:');
            spreadsheet.data.sheets.forEach(s => console.log(`  - ${s.properties.title}`));
        }
        return;
    }

    const sheetId = targetSheet.properties.sheetId;

    // シート名を変更
    await sheets.spreadsheets.batchUpdate({
        spreadsheetId,
        requestBody: {
            requests: [{
                updateSheetProperties: {
                    properties: {
                        sheetId,
                        title: NEW_NAME,
                    },
                    fields: 'title',
                },
            }],
        },
    });

    console.log(`✅ シート名を「${OLD_NAME}」→「${NEW_NAME}」に変更しました`);
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
