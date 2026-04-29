/**
 * run_batch_regions_3.js
 * 新規地域第3弾を順番に検索・収集するバッチスクリプト
 */

const { execSync } = require('child_process');

const REGIONS = [
    { name: '新潟県',  config: 'config_niigata.yaml' },
    { name: '岡山県',  config: 'config_okayama.yaml' },
    { name: '熊本県',  config: 'config_kumamoto.yaml' },
    { name: '鹿児島県',  config: 'config_kagoshima.yaml' },
    { name: '沖縄県',  config: 'config_okinawa.yaml' },
];

async function runRegion(region) {
    const logFile = `run_${region.config.replace('config_', '').replace('.yaml', '')}.log`;
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 開始: ${region.name} → ${logFile}`);
    console.log(`${'='.repeat(60)}`);

    try {
        execSync(
            `node search_companies.js --config ${region.config} > ${logFile} 2>&1`,
            {
                cwd: __dirname,
                stdio: 'inherit',
                shell: true,
                timeout: 30 * 60 * 1000, // 30分タイムアウト
            }
        );
        console.log(`\n✅ 完了: ${region.name}`);
    } catch (err) {
        console.error(`\n❌ エラー: ${region.name} - ${err.message}`);
        console.log('次の地域に進みます...');
    }
}

async function main() {
    console.log('========================================');
    console.log('  Webマーケティング 新規地域 バッチ収集（第3弾）');
    console.log(`  対象: ${REGIONS.map(r => r.name).join(', ')}`);
    console.log('========================================\n');

    for (const region of REGIONS) {
        await runRegion(region);
        await new Promise(resolve => setTimeout(resolve, 3000));
    }

    console.log('\n========================================');
    console.log('  全地域バッチ完了');
    console.log('========================================');
}

main().catch(console.error);
