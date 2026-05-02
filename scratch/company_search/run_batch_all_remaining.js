const { spawn } = require('child_process');
const fs = require('fs');

// 実行順序: 近畿 → 中部 → 九州 → 中国四国 → 東北・その他
const phases = [
    {
        name: '近畿（残り）',
        regions: ['mie', 'shiga', 'nara', 'wakayama'],
    },
    {
        name: '中部（残り）',
        regions: ['yamanashi', 'nagano', 'toyama', 'ishikawa', 'fukui'],
    },
    {
        name: '九州（残り）',
        regions: ['saga', 'nagasaki', 'oita', 'miyazaki'],
    },
    {
        name: '中国四国',
        regions: ['tottori', 'shimane', 'yamaguchi', 'tokushima', 'kagawa', 'ehime', 'kochi'],
    },
    {
        name: '東北・その他',
        regions: ['aomori', 'iwate', 'akita', 'yamagata', 'fukushima'],
    },
];

async function runRegion(region) {
    const logFile = `run_${region}.log`;
    
    // ★ 既存ログが存在する場合はスキップ（上書き防止）
    if (fs.existsSync(logFile)) {
        console.log(`⏭ スキップ（実行済み）: ${region} (${logFile} が既存)`);
        return 0;
    }
    
    console.log(`\n============================================================`);
    console.log(`🚀 開始: ${region} → ${logFile}`);
    console.log(`============================================================`);

    return new Promise((resolve, reject) => {
        const outStream = fs.createWriteStream(logFile);
        const proc = spawn('node', ['search_companies.js', '--config', `config_${region}.yaml`]);

        proc.stdout.pipe(outStream);
        proc.stderr.pipe(outStream);

        proc.on('close', (code) => {
            console.log(`✅ 完了: ${region} (exit code: ${code})`);
            resolve(code);
        });

        proc.on('error', (err) => {
            console.error(`❌ エラー: ${region}`, err);
            reject(err);
        });
    });
}

async function main() {
    console.log('========================================');
    console.log('  Webマーケティング 全国バッチ（第5弾〜）');
    console.log('  近畿→中部→九州→中国四国→東北');
    console.log('========================================\n');

    for (const phase of phases) {
        console.log(`\n======== ${phase.name} ========`);
        for (const region of phase.regions) {
            await runRegion(region);
        }
        console.log(`\n✅ ${phase.name} フェーズ完了`);
    }

    console.log('\n🎉 全国バッチ処理が完了しました！');
}

main().catch(console.error);
