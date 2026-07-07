// Extract benchmark table from all 03 HTML reports
const fs = require('fs');
const path = require('path');

const reportsDir = path.join(require('os').homedir(), 'gbp-clients', '_monthly-reports');
const files = fs.readdirSync(reportsDir).filter(f => f.includes('03') && f.endsWith('.html'));

files.forEach(file => {
  const content = fs.readFileSync(path.join(reportsDir, file), 'utf8');
  const titleMatch = content.match(/<title>(.*?)<\/title>/);
  const title = titleMatch ? titleMatch[1] : file;
  
  // Extract benchmark table rows
  const benchmarkSection = content.match(/ベンチマーク参考([\s\S]*?)<\/div>\s*<\/div>/);
  const rows = content.match(/<tr[\s\S]*?<\/tr>/g) || [];
  
  // Look for table rows with review counts
  const tableRows = rows.filter(r => r.includes('件'));
  
  console.log('\n=== ' + title + ' ===');
  console.log('File:', file);
  tableRows.forEach(r => {
    const cells = r.match(/<td>(.*?)<\/td>/g);
    if (cells) console.log(cells.map(c => c.replace(/<[^>]+>/g,'')).join(' | '));
  });
});
