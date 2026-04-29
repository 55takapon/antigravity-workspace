const {google} = require('googleapis');
const fs = require('fs');
const cred = JSON.parse(fs.readFileSync('google_credentials.json','utf-8'));
const auth = new google.auth.GoogleAuth({credentials:cred,scopes:['https://www.googleapis.com/auth/spreadsheets']});
const ID = '1WHq7_pmFKa5ZZu2NmiUx_d90JqRGlfRRFkj494Fb3yc';
async function fix(){
  const sheets = google.sheets({version:'v4',auth:await auth.getClient()});
  const meta = await sheets.spreadsheets.get({ spreadsheetId: ID });
  const sheetId = meta.data.sheets.find(s => s.properties.title === 'スケジュール').properties.sheetId;

  // D列の既存の文字列を数値のみに変換
  const res = await sheets.spreadsheets.values.get({ spreadsheetId: ID, range: 'スケジュール!D6:D' });
  const rows = res.data.values || [];
  const newVals = rows.map(r => {
    if(r[0]) {
      const num = parseInt(r[0].replace(/[^0-9]/g, ''), 10);
      return [isNaN(num) ? '' : num];
    }
    return [''];
  });
  if (newVals.length > 0) {
    await sheets.spreadsheets.values.update({ spreadsheetId: ID, range: 'スケジュール!D6', valueInputOption: 'RAW', requestBody: { values: newVals } });
  }

  // D列にカスタム数値フォーマット（〇〇日）を適用
  const reqs = [{
    repeatCell: {
      range: { sheetId: sheetId, startRowIndex: 5, startColumnIndex: 3, endColumnIndex: 4 },
      cell: { userEnteredFormat: { numberFormat: { type: 'NUMBER', pattern: '0"日"' }, horizontalAlignment: 'CENTER', textFormat: { bold: true, foregroundColor: {red:44/255, green:62/255, blue:80/255} } } },
      fields: 'userEnteredFormat.numberFormat,userEnteredFormat.horizontalAlignment,userEnteredFormat.textFormat'
    }
  }];
  await sheets.spreadsheets.batchUpdate({spreadsheetId:ID,requestBody:{requests:reqs}});
  console.log('D列のフォーマット変更完了');
}
fix().catch(e=>console.error(e.message));
