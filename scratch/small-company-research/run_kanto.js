const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const regions = ['tokyo', 'kanagawa', 'saitama', 'chiba', 'ibaraki', 'tochigi', 'gunma'];

console.log(`=================================================`);
console.log(`  関東エリア 順次抽出＆クローリング処理開始`);
console.log(`=================================================\n`);

for (const region of regions) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`  ${region.toUpperCase()} 開始`);
    console.log(`${'='.repeat(50)}`);

    try {
        const seedFile = path.join(__dirname, `seeds_${region}.jsonl`);
        
        // 再発防止ルール: 処理前に必ず古いシードファイルを破棄する
        if (fs.existsSync(seedFile)) {
            console.log(`[0/2] ⚠️ 古いシードファイルを破棄します (再発防止): ${path.basename(seedFile)}`);
            fs.unlinkSync(seedFile);
        }

        console.log(`[1/2] 🔍 シード収集 (Web奉行のみ)...`);
        execSync(`node portal_seeder.js --region ${region} --skip-imitsu`, { stdio: 'inherit', cwd: __dirname });

        if (!fs.existsSync(seedFile)) {
            console.log(`[!] シードファイルが生成されませんでした。スキップします。`);
            continue;
        }

        console.log(`[2/2] 🕷️ クロール・品質判定・シート書き込み...`);
        execSync(`node search_companies_v2.js --seeds seeds_${region}.jsonl`, { stdio: 'inherit', cwd: __dirname });

        console.log(`✅ ${region} 完了`);
    } catch (e) {
        console.error(`❌ ${region} でエラー発生: ${e.message}`);
        console.error(`🚨 安全のため、後続の処理を停止します。`);
        process.exit(1);
    }
}

console.log('\n✅ 関東エリアすべての処理が完了しました！');
