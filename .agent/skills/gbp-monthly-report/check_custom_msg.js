const fs = require('fs'), path = require('path');
const dir = path.join(require('os').homedir(), 'gbp-clients', '_monthly-reports');

fs.readdirSync(dir).filter(f => f.includes('03') && f.endsWith('.html')).forEach(file => {
  const html = fs.readFileSync(path.join(dir, file), 'utf8');
  const match = html.match(/<div class="custom-message">([\s\S]*?)<\/div>/);
  if (match) {
    const text = match[1].replace(/<[^>]+>/g, '').trim();
    console.log(file.slice(0, 30) + ': ' + JSON.stringify(text.slice(0, 120)));
  } else {
    console.log(file.slice(0, 30) + ': (div.custom-message not found)');
  }
});
