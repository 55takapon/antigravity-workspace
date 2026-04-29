/**
 * GBP診断スクリーンショット クリーンアップスクリプト
 * 
 * 使い方:
 *   node scripts/cleanup_screenshots.js              → 7日以上前のSSを削除（デフォルト）
 *   node scripts/cleanup_screenshots.js 3            → 3日以上前のSSを削除
 *   node scripts/cleanup_screenshots.js 0            → 全SSを削除
 *   node scripts/cleanup_screenshots.js --dry-run     → 削除せずリストのみ表示
 *   node scripts/cleanup_screenshots.js 3 --dry-run   → 3日以上前をリストのみ
 */
const fs = require('fs');
const path = require('path');

// ── 設定 ──
const BRAIN_DIR = path.join(process.env.USERPROFILE || process.env.HOME, '.gemini', 'antigravity', 'brain');
const TARGET_EXTENSIONS = ['.png', '.webp', '.jpg', '.jpeg'];
const DEFAULT_DAYS = 7;

// ── 引数パース ──
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const daysArg = args.find(a => /^\d+$/.test(a));
const retentionDays = daysArg !== undefined ? parseInt(daysArg) : DEFAULT_DAYS;
const cutoffDate = new Date(Date.now() - retentionDays * 24 * 60 * 60 * 1000);

console.log(`🧹 GBP診断スクリーンショット クリーンアップ`);
console.log(`   対象: ${retentionDays}日以上前のファイル（${cutoffDate.toLocaleDateString('ja-JP')}以前）`);
console.log(`   モード: ${dryRun ? '🔍 ドライラン（削除しない）' : '🗑️ 削除実行'}`);
console.log('');

// ── 対象ファイル収集 ──
let totalFiles = 0;
let totalSize = 0;
let deletedFiles = 0;
let deletedSize = 0;

function scanDir(dirPath) {
  if (!fs.existsSync(dirPath)) return;
  
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    
    if (entry.isDirectory()) {
      // .system_generated/click_feedback も対象
      scanDir(fullPath);
      continue;
    }
    
    const ext = path.extname(entry.name).toLowerCase();
    if (!TARGET_EXTENSIONS.includes(ext)) continue;
    
    // アーティファクト（mdファイルと同名のスクリーンショット等）は除外
    // 診断関連のスクリーンショットのみ対象
    const stat = fs.statSync(fullPath);
    totalFiles++;
    totalSize += stat.size;
    
    if (stat.mtime < cutoffDate) {
      deletedFiles++;
      deletedSize += stat.size;
      
      if (dryRun) {
        const age = Math.floor((Date.now() - stat.mtime) / (1000 * 60 * 60 * 24));
        console.log(`  📋 ${entry.name} (${(stat.size / 1024).toFixed(0)}KB, ${age}日前)`);
      } else {
        fs.unlinkSync(fullPath);
      }
    }
  }
}

// brain配下の全会話ディレクトリをスキャン
if (fs.existsSync(BRAIN_DIR)) {
  const conversations = fs.readdirSync(BRAIN_DIR, { withFileTypes: true });
  for (const conv of conversations) {
    if (!conv.isDirectory()) continue;
    const convPath = path.join(BRAIN_DIR, conv.name);
    scanDir(convPath);
  }
}

console.log('');
console.log(`📊 結果:`);
console.log(`   全ファイル: ${totalFiles}件 (${(totalSize / 1024 / 1024).toFixed(1)}MB)`);
console.log(`   ${dryRun ? '削除対象' : '削除済み'}: ${deletedFiles}件 (${(deletedSize / 1024 / 1024).toFixed(1)}MB)`);
console.log(`   残存: ${totalFiles - deletedFiles}件 (${((totalSize - deletedSize) / 1024 / 1024).toFixed(1)}MB)`);

if (dryRun && deletedFiles > 0) {
  console.log('');
  console.log(`💡 実際に削除するには: node scripts/cleanup_screenshots.js ${retentionDays}`);
}
