async function check() {
  const res = await fetch('https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv');
  const text = await res.text();
  const rows = text.split('\n').map(l => l.split(',').map(c => c.replace(/\r$/,'').replace(/^"|"$/g,'').trim()));

  // 行112と128付近を表示
  console.log('--- rows 110-145 ---');
  for (let i = 110; i <= 145; i++) {
    if (rows[i]) console.log(i + ':', JSON.stringify(rows[i].slice(0,9)));
  }
}
check().catch(console.error);
