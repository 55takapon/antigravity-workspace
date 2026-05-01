async function run() {
  const url = 'https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv';
  try {
    const response = await fetch(url);
    const text = await response.text();
    const rows = text.split('\n').map(line => line.split(',').map(c => c.replace(/\r$/, '').replace(/^\"|\"$/g, '').trim()));
    const names = new Set();
    for (const row of rows) {
      if (row[0] && !row[0].includes('2026-') && row[0] !== '月') names.add(row[0]);
    }
    console.log(Array.from(names).filter(n => n.length > 0));
  } catch (e) { console.error(e); }
}
run();
