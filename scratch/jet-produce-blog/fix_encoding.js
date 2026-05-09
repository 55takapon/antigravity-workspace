const fs = require('fs');
let content = fs.readFileSync('c:/Users/hangy/.gemini/antigravity/scratch/jet-produce-blog/extracted_tables.md', 'utf8');
const catG = `
## カテゴリG: マインド（オーナー心理）（全2本）

| ID | タイトル | メインKW | 構成 | ステータス |
|---|---|---|---|---|
| G-01 | Googleマップの口コミ声かけが怖い？私もしてた大きな勘違い | 口コミ 頼み方 声かけ | PAS法 | ✅完成 |
| G-02 | Googleマップの口コミを増やしたいなら、まずこれをやるだけ | 口コミ 増やし方 店舗 | PAS法 | ✅完成 |
`;
content = content.replace('---\n\n## ファイル一覧', catG + '\n---\n\n## ファイル一覧');
const header = '# ブログ記事バッチ計画（全38本）\n\n> 作成: 2026-05-03\n> 更新: 2026-05-09\n> 全38本執筆完了 ✅\n\n---\n';
fs.writeFileSync('c:/Users/hangy/.gemini/antigravity/scratch/jet-produce-blog/batch-plan.md', header + content, 'utf8');
