// Check: what competitor data actually goes into the report
const fs = require('fs');
const path = require('path');

// 1. Check eiwa-south HTML for competitor section
const htmlPath = path.join(require('os').homedir(), '.gemini', 'antigravity', '.agent', 'clients', '00monthly-reports', 'eiwa-juku-south_monthly_202604.html');
const html = fs.readFileSync(htmlPath, 'utf8');

// Find benchmark table
const benchIdx = html.indexOf('benchmark') !== -1 ? html.indexOf('benchmark') : html.indexOf('ベンチマーク');
console.log('=== Benchmark section ===');
console.log(html.substring(benchIdx, benchIdx + 800));

// 2. Check 3月 eiwa report for post recommendation
const reports = fs.readdirSync(path.join(require('os').homedir(), '.gemini', 'antigravity', '.agent', 'clients', '00monthly-reports'));
const march = reports.find(f => f.includes('03') && f.endsWith('.html') && !f.startsWith('eiwa'));
console.log('\n=== March reports found ===', reports.filter(f => f.includes('03')));
