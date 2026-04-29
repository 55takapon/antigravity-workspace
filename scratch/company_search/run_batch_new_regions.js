/**
 * run_batch_new_regions.js
 * 新規地域（関西・名古屋以外）を順番に検索・収集するバッチスクリプト
 *
 * 完了済み: 大阪・兵庫（関西）、名古屋（愛知）、神奈川、埼玉、千葉、京都
 * 今回追加: 東京、福岡、北海道、宮城、広島、静岡
 */

const { execSync } = require('child_process');
const path = require('path');

const REGIONS = [
    { name: '福岡県',  config: 'config_fukuoka.yaml' },
    { name: '北海道',  config: 'config_hokkaido.yaml' },
    { name: '宮城県',  config: 'config_miyagi.yaml' },
    { name: '広島県',  config: 'config_hiroshima.yaml' },
    { name: '静岡県',  config: 'config_shizuoka.yaml' },
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
    console.log('  Webマーケティング 新規地域 バッチ収集');
    console.log(`  対象: ${REGIONS.map(r => r.name).join(', ')}`);
    console.log('========================================\n');

    for (const region of REGIONS) {
        await runRegion(region);
        // 地域間インターバル（3秒）
        await new Promise(resolve => setTimeout(resolve, 3000));
    }

    console.log('\n========================================');
    console.log('  全地域バッチ完了');
    console.log('========================================');
    console.log('\n次の手順:');
    console.log('1. node sync_master_db.js         # ローカルDB再同期');
    console.log('2. node sweep_all.js               # AXIS-A: ノイズ除去');
    console.log('3. node fix_representative_names.js # AXIS-A: 代表者名修正');
    console.log('4. node check_ng_forms.js --sheet Webマーケティング  # AXIS-B');
    console.log('5. node deep_verify_sheet.js --sheet Webマーケティング # AXIS-C');
    console.log('6. node apply_auto_reject.js       # AXIS-E: 規模フィルター');
    console.log('7. node verify_sheet.js            # AXIS-D: 全件バリデーション');
}

main().catch(console.error);
