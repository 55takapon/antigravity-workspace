const fs = require('fs');
let content = fs.readFileSync('search_companies.js', 'utf8');

// 記事展開ブロックのある行範囲を確認
const lines = content.split('\n');
const startIdx = lines.findIndex(l => l.includes('for (const item of filtered)'));
console.log('article expansion block starts at line:', startIdx + 1);
for (let i = startIdx; i < startIdx + 25; i++) {
    console.log(i + 1, ':', lines[i]);
}
