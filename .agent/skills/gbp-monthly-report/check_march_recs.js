const fs = require('fs');
const path = require('path');

const dir = path.join(require('os').homedir(), '.gemini', 'antigravity', '.agent', 'clients', '00monthly-reports');
const files = fs.readdirSync(dir).filter(f => f.includes('03') && f.endsWith('.html'));
files.forEach(file => {
  const html = fs.readFileSync(path.join(dir, file), 'utf8');
  // Check post count recommendation
  const recIdx = html.indexOf('rec-action');
  if (recIdx !== -1) {
    const recs = [];
    let idx = 0;
    while (true) {
      idx = html.indexOf('rec-action', idx + 1);
      if (idx === -1) break;
      const end = html.indexOf('</div>', idx);
      recs.push(html.substring(idx + 12, end).replace(/<[^>]+>/g, ''));
    }
    if (recs.length > 0) {
      console.log(file.substring(0, 20) + ':');
      recs.forEach(r => console.log('  -', r));
    }
  }
});
