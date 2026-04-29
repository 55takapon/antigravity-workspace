const {google}=require('googleapis');
const fs=require('fs');
const path=require('path');
async function run(){
  const auth=new google.auth.GoogleAuth({
    credentials:JSON.parse(fs.readFileSync(path.join(process.cwd(), 'google_credentials.json'), 'utf-8')),
    scopes:['https://www.googleapis.com/auth/spreadsheets']
  });
  const sheets=google.sheets({version:'v4',auth});
  await sheets.spreadsheets.values.batchUpdate({
    spreadsheetId:'1cBraHQGD5xAYTX-ljt8JaekiqshlMqZ2GTFGSLJKodE',
    requestBody:{
      valueInputOption:'USER_ENTERED',
      data:[
        {range:"'260311(260202copy) '!G726",values:[['']]},
        {range:"'260311(260202copy) '!H726",values:[['']]}
      ]
    }
  });
}
run().catch(console.error);
