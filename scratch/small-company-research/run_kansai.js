const { execSync } = require('child_process');

const regions = ['kyoto', 'nara', 'wakayama', 'shiga'];

for (const region of regions) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`  ${region.toUpperCase()} 開始`);
    console.log(`${'='.repeat(50)}`);

    try {
        console.log(`[1/2] シード収集...`);
        execSync(`node portal_seeder.js --region ${region} --skip-imitsu`, { stdio: 'inherit', cwd: __dirname });

        console.log(`[2/2] クロール・書き込み...`);
        execSync(`node search_companies_v2.js --seeds seeds_${region}.jsonl`, { stdio: 'inherit', cwd: __dirname });

        console.log(`✅ ${region} 完了`);
    } catch (e) {
        console.error(`❌ ${region} でエラー: ${e.message}`);
    }
}

console.log('\n全地域完了！');
