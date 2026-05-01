const https = require('https');
https.get('https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/export?format=csv&gid=0', (res) => {
  let body = '';
  res.on('data', d => body += d);
  res.on('end', () => {
    const lines = body.split('\n');
    const names = [];
    for (const line of lines) {
      const first = line.split(',')[0].replace(/^\"|\"$/g, '').trim();
      if (first && !first.includes('2026-') && first !== '月') {
         names.push(first);
      }
    }
    console.log(names);
  });
});
