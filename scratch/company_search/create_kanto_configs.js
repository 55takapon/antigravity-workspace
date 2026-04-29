const fs = require('fs');
const regions = {ibaraki: '茨城県', tochigi: '栃木県', gunma: '群馬県'};
const base = fs.readFileSync('config_tokyo.yaml', 'utf8');
for (const [k, v] of Object.entries(regions)) {
    fs.writeFileSync(`config_${k}.yaml`, base.replace('region: 東京都', `region: ${v}`));
}
console.log('Configs created.');
