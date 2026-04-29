const fs = require('fs');
const NEG = '-事例 -導入事例 -成功事例 -比較 -ランキング -おすすめ -一覧';
const GOOD = '    const query = `${keywords} 支援 ${config.search.region} ' + NEG + '`;';

let content = fs.readFileSync('searcher.js', 'utf8');
const lines = content.split('\n');

let fixed = 0;
for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    // 壊れたパターン: バックスラッシュが入っている query行
    if (l.trim().startsWith('const query') && l.includes('\\ 支援')) {
        console.log('FIX line', i, ':', JSON.stringify(l.trim().substring(0, 50)));
        lines[i] = GOOD;
        fixed++;
    }
}

console.log('Fixed', fixed, 'lines');
fs.writeFileSync('searcher.js', lines.join('\n'), 'utf8');

// 最終確認
fs.readFileSync('searcher.js', 'utf8').split('\n')
    .filter(l => l.trim().startsWith('const query'))
    .forEach((l, i) => console.log(i + ':', l.trim().substring(0, 100)));
console.log('Done');
