const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const files = fs.readdirSync(__dirname).filter(f => f.startsWith('seeds_') && f.endsWith('.jsonl'));

console.log(`=================================================`);
console.log(`  クローリング対象: ${files.length}ファイル`);
console.log(`=================================================\n`);

for (const file of files) {
    console.log(`\n▶▶▶ クローリング開始: ${file} ◀◀◀`);
    try {
        execSync(`node search_companies_v2.js --seeds ${file}`, { stdio: 'inherit', cwd: __dirname });
        console.log(`✅ 完了: ${file}`);
    } catch (e) {
        console.error(`❌ エラー終了 (${file}): ${e.message}`);
    }
}

console.log('\n✅ すべてのクローリングが完了しました！');
