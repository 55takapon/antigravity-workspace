const { execSync } = require('child_process');

const sheets = [
  'Webマーケティング',
  'Webマーケティング_名古屋',
  'Webマーケティング_名古屋_テスト',
  'クリニック専門支援'
];

for (const sheet of sheets) {
  console.log(`\n========================================`);
  console.log(` Starting check for sheet: ${sheet}`);
  console.log(`========================================\n`);
  try {
    execSync(`node check_ng_forms.js --sheet "${sheet}"`, { stdio: 'inherit' });
  } catch (err) {
    console.error(`Error checking sheet ${sheet}: ${err.message}`);
  }
}
