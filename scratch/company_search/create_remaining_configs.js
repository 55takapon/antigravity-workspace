const fs = require('fs');
const path = require('path');

// 近畿（残り）: 三重・滋賀・奈良・和歌山
// 中部（残り）: 山梨・長野・富山・石川・福井
// 九州（残り）: 佐賀・長崎・大分・宮崎
// 中国四国（残り）: 鳥取・島根・山口・徳島・香川・愛媛・高知
// その他（東北）: 青森・岩手・秋田・山形・福島
const regions = [
    // 近畿（残り）
    { id: 'mie',        region: '三重県' },
    { id: 'shiga',      region: '滋賀県' },
    { id: 'nara',       region: '奈良県' },
    { id: 'wakayama',   region: '和歌山県' },
    // 中部（残り）
    { id: 'yamanashi',  region: '山梨県' },
    { id: 'nagano',     region: '長野県' },
    { id: 'toyama',     region: '富山県' },
    { id: 'ishikawa',   region: '石川県' },
    { id: 'fukui',      region: '福井県' },
    // 九州（残り）
    { id: 'saga',       region: '佐賀県' },
    { id: 'nagasaki',   region: '長崎県' },
    { id: 'oita',       region: '大分県' },
    { id: 'miyazaki',   region: '宮崎県' },
    // 中国四国
    { id: 'tottori',    region: '鳥取県' },
    { id: 'shimane',    region: '島根県' },
    { id: 'yamaguchi',  region: '山口県' },
    { id: 'tokushima',  region: '徳島県' },
    { id: 'kagawa',     region: '香川県' },
    { id: 'ehime',      region: '愛媛県' },
    { id: 'kochi',      region: '高知県' },
    // 東北・その他
    { id: 'aomori',     region: '青森県' },
    { id: 'iwate',      region: '岩手県' },
    { id: 'akita',      region: '秋田県' },
    { id: 'yamagata',   region: '山形県' },
    { id: 'fukushima',  region: '福島県' },
];

const configTemplate = (region) => `search:
  keywords:
    - ホームページ制作
    - Webマーケティング
    - MEO対策
    - SEO対策
    - Web制作
  region: ${region}
  max_results: 150

filters:
  max_employees: 20
  hp_check_keywords:
    - Web制作
    - マーケティング
    - ホームページ
    - SEO
    - MEO

exclude:
  spreadsheet_id: 1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk
  sheet_name: 除外リスト

output:
  spreadsheet_id: 1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk
  sheet_name: Webマーケティング

google_cse:
  enabled: false
  api_key: AIzaSyCJrYuW_XKCk_k3lOMdBU64AKh9tGnWtSg
  cx: 2180f0a6c545843bf

speed:
  page_wait_min: 2000
  page_wait_max: 4000
  crawl_interval_min: 3000
  crawl_interval_max: 6000
`;

let created = 0;
let skipped = 0;

for (const r of regions) {
    const filePath = path.join(__dirname, `config_${r.id}.yaml`);
    if (fs.existsSync(filePath)) {
        console.log(`⏭ スキップ（既存）: config_${r.id}.yaml`);
        skipped++;
    } else {
        fs.writeFileSync(filePath, configTemplate(r.region), 'utf-8');
        console.log(`✅ 作成: config_${r.id}.yaml (${r.region})`);
        created++;
    }
}

console.log(`\n完了: ${created}件作成, ${skipped}件スキップ`);
console.log('地域一覧:', regions.map(r => r.id).join(', '));
