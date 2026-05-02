const fs = require('fs');
const path = require('path');

const files = fs.readdirSync(__dirname).filter(f => f.startsWith('seeds_') && f.endsWith('.jsonl'));
let bugyo = 0, imitsu = 0, total = 0;

files.forEach(f => {
    const lines = fs.readFileSync(path.join(__dirname, f), 'utf-8').split('\n').filter(Boolean);
    total += lines.length;
    let b = 0, i = 0;
    lines.forEach(l => {
        try {
            const j = JSON.parse(l);
            if(j.portal_source === 'web-bugyo') { bugyo++; b++; }
            else if(j.portal_source === 'imitsu') { imitsu++; i++; }
        } catch(e) {}
    });
    console.log(`[${f}] Total: ${lines.length} | Web奉行: ${b} | アイミツ: ${i}`);
});

console.log(`\n============================`);
console.log(`Grand Total Seeds: ${total}`);
console.log(`Web奉行 (web-bugyo): ${bugyo}`);
console.log(`PRONIアイミツ (imitsu): ${imitsu}`);
console.log(`============================`);
