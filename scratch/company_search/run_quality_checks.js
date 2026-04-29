const { execSync } = require('child_process');

console.log('Running AXIS-B: check_ng_forms.js');
execSync('node check_ng_forms.js --sheet Webマーケティング', { stdio: 'inherit' });

console.log('Running AXIS-C: deep_verify_sheet.js');
execSync('node deep_verify_sheet.js --sheet Webマーケティング', { stdio: 'inherit' });

console.log('Running AXIS-D: verify_sheet.js');
execSync('node verify_sheet.js > final_verify.log', { stdio: 'inherit' });

console.log('All quality checks complete.');
