const fs = require('fs');
const path = require('path');
const dir = 'c:/Users/hangy/.gemini/antigravity/scratch/jet-produce-blog/articles';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.md')).sort();

let output = '';
let currentCat = '';

const catNames = {
    'A': 'カテゴリA: GBP運用・MEO対策',
    'B': 'カテゴリB: SEO・AI検索対策',
    'C': 'カテゴリC: SNS集客（Instagram/LINE）',
    'D': 'カテゴリD: ホームページ・Web',
    'E': 'カテゴリE: マーケティング・集客戦略',
    'F': 'カテゴリF: 事例・ケーススタディ',
    'G': 'カテゴリG: マインド（オーナー心理）'
};

files.forEach(file => {
    const content = fs.readFileSync(path.join(dir, file), 'utf8');
    const idMatch = content.match(/【コンテンツブリーフ ([A-Z]-\d+)】/);
    if (!idMatch) return;
    const id = idMatch[1];
    
    const cat = id.charAt(0);
    if (cat !== currentCat) {
        output += `\n## ${catNames[cat]}（全${files.filter(f=>f.startsWith(cat)).length}本）\n\n`;
        output += `| ID | タイトル | メインKW | 構成 | ステータス |\n`;
        output += `|---|---|---|---|---|\n`;
        currentCat = cat;
    }

    const titleMatch = content.match(/1\. 記事タイトル:\s*(.+)/);
    const kwMatch = content.match(/2\. メインKW:\s*(.+)/);
    const frameMatch = content.match(/8\. 構成フレームワーク:\s*(.+)/);
    
    const title = titleMatch ? titleMatch[1] : '';
    const kw = kwMatch ? kwMatch[1] : '';
    const frame = frameMatch ? frameMatch[1] : '';
    
    output += `| ${id} | ${title} | ${kw} | ${frame} | ✅完成 |\n`;
});

// Also create file list
output += `\n---\n\n## ファイル一覧\n\n\`\`\`\nscratch/jet-produce-blog/articles/\n`;
files.forEach(file => {
    output += `├── ${file.padEnd(35)} ✅ NEW\n`;
});
output += `\`\`\`\n`;

fs.writeFileSync('c:/Users/hangy/.gemini/antigravity/scratch/jet-produce-blog/extracted_tables.md', output);
