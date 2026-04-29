const { spawn } = require('child_process');
const fs = require('fs');

const regions = ['ibaraki', 'tochigi', 'gunma'];

async function runRegion(region) {
    console.log(`\n============================================================`);
    console.log(`🚀 開始: ${region} → run_${region}.log`);
    console.log(`============================================================`);
    
    return new Promise((resolve, reject) => {
        const outStream = fs.createWriteStream(`run_${region}.log`);
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
    console.log('  Webマーケティング 新規地域 バッチ収集（第4弾: 関東残り）');
    console.log('  対象: 茨城県, 栃木県, 群馬県');
    console.log('========================================\n');
    
    for (const r of regions) {
        await runRegion(r);
    }
    
    console.log('\n🎉 第4弾バッチの全処理が完了しました！');
}

main().catch(console.error);
