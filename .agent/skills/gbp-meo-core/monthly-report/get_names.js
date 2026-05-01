const { fetchSheetData } = require('./generate_report_from_sheet.js');
async function run() {
  const rows = await fetchSheetData('https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/edit?usp=sharing');
  const names = new Set();
  for (const row of rows) {
    if (row[0] && !row[0].includes('2026-') && row[0] !== '月') names.add(row[0]);
  }
  console.log(Array.from(names).filter(n => n.length > 0));
}
run();
