const fs = require('fs');
let c = fs.readFileSync('core/playwright_submitter.js', 'utf8');

// 1. SELECT_PREFERENCESに「それ以外」を追加
const before1 = "        // その他（最終フォールバック）\r\n        'その他のお問い合わせ', 'その他'";
const after1  = "        // それ以外・その他（最終フォールバック）\r\n        'それ以外のお問い合わせ', 'それ以外',\r\n        'その他のお問い合わせ', 'その他'";
if (!c.includes(before1)) { console.error('PATCH1 not found'); process.exit(1); }
c = c.replace(before1, after1);
console.log('PATCH1 applied: それ以外 added to SELECT_PREFERENCES');

// 2. フォールバック除外リストに海外・越境・EC・BtoB系を追加
const before2 = "        const exclude = ['採用', '応募', 'recruit', 'career', 'job'];";
const after2  = "        const exclude = ['採用', '応募', 'recruit', 'career', 'job',\r\n                         '越境', '海外', '輸出', 'グローバル', 'BtoB展開', 'EC',\r\n                         '海外BtoB', '越境EC'];";
if (!c.includes(before2)) { console.error('PATCH2 not found'); process.exit(1); }
c = c.replace(before2, after2);
console.log('PATCH2 applied: overseas/EC keywords added to exclude list');

// 3. 除外された場合の「その他/それ以外」探索ロジック追加
const before3 = "        if (!exclude.some(e => firstVal.includes(e))) {\r\n            try { await radioGroup.first().check({ timeout: 1000, force: true }); }\r\n            catch (e) { await radioGroup.first().evaluate(el => el.click()).catch(() => {}); }\r\n            console.log(`     → ラジオ フォールバック選択: 先頭 (value=${firstVal})`);\r\n        }\r\n    }\r\n}";
const after3  = "        if (!exclude.some(e => firstVal.includes(e))) {\r\n            try { await radioGroup.first().check({ timeout: 1000, force: true }); }\r\n            catch (e) { await radioGroup.first().evaluate(el => el.click()).catch(() => {}); }\r\n            console.log(`     → ラジオ フォールバック選択: 先頭 (value=${firstVal})`);\r\n        } else {\r\n            // 除外キーワードが先頭にある場合、「その他/それ以外」系を探す\r\n            let altClicked = false;\r\n            for (let i = 0; i < count; i++) {\r\n                const r = radioGroup.nth(i);\r\n                const val = await r.getAttribute('value') || '';\r\n                if (['その他', 'それ以外', 'その他のお問い合わせ', 'それ以外のお問い合わせ'].some(kw => val.includes(kw))) {\r\n                    try { await r.check({ timeout: 1000, force: true }); }\r\n                    catch (e) { await r.evaluate(el => el.click()).catch(() => {}); }\r\n                    console.log(`     → ラジオ 除外回避: 「その他/それ以外」を選択 (value=${val})`);\r\n                    altClicked = true;\r\n                    break;\r\n                }\r\n            }\r\n            if (!altClicked) console.log(`     ⚠️  先頭ラジオが除外対象のためスキップ`);\r\n        }\r\n    }\r\n}";
if (!c.includes(before3)) { console.error('PATCH3 not found'); process.exit(1); }
c = c.replace(before3, after3);
console.log('PATCH3 applied: fallback alt-selection logic added');

fs.writeFileSync('core/playwright_submitter.js', c, 'utf8');
console.log('All patches applied successfully.');
