const fs = require('fs');
const { execSync } = require('child_process');
const yaml = require('js-yaml');

const configPath = 'config.yaml';
const config = yaml.load(fs.readFileSync(configPath, 'utf8'));

const keywordLists = [
    ["MEO対策"],
    ["Googleビジネスプロフィール", "運用代行"],
    ["SEO", "MEO"],
    ["店舗集客"],
    ["ローカルSEO"]
];

config.search.region = "大阪";

for (let i = 0; i < keywordLists.length; i++) {
    const list = keywordLists[i];
    console.log(`\n========================================`);
    console.log(` バッチ実行 ${i + 1}/${keywordLists.length}: ${list.join(' ')}`);
    console.log(`========================================`);
    
    config.search.keywords = list;
    fs.writeFileSync(configPath, yaml.dump(config));
    
    try {
        execSync('node search_companies.js --max 30', { stdio: 'inherit' });
    } catch (err) {
        console.error(`実行エラー: ${err.message}`);
    }
}
console.log('\nバッチ全体の実行が完了しました。');
