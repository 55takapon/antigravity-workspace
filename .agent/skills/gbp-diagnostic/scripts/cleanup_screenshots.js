/**
 * GBP診断スクリーンショット クリーンアップスクリプト
 *
 * 対象ディレクトリは --dir で必ず明示指定する（誤削除防止のため必須）。
 * 指定ディレクトリ配下を再帰的にスキャンし、古い画像ファイルを削除する。
 *
 * 使い方:
 *   node scripts/cleanup_screenshots.js --dir <対象ディレクトリ>              → 7日以上前のSSを削除（デフォルト）
 *   node scripts/cleanup_screenshots.js --dir <対象ディレクトリ> 3            → 3日以上前のSSを削除
 *   node scripts/cleanup_screenshots.js --dir <対象ディレクトリ> 0            → 全SSを削除
 *   node scripts/cleanup_screenshots.js --dir <対象ディレクトリ> --dry-run    → 削除せずリストのみ表示
 *   node scripts/cleanup_screenshots.js --dir <対象ディレクトリ> 3 --dry-run  → 3日以上前をリストのみ
 */
const fs = require('fs');
const path = require('path');

// ── 設定 ──
const TARGET_EXTENSIONS = ['.png', '.webp', '.jpg', '.jpeg'];
const DEFAULT_DAYS = 7;

// ── 引数パース ──
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const dirIdx = args.indexOf('--dir');
const targetDir = dirIdx !== -1 ? args[dirIdx + 1] : null;

if (!targetDir) {
  console.error('使い方: node scripts/cleanup_screenshots.js --dir <対象ディレクトリ> [日数] [--dry-run]');
  console.error('  --dir      スキャン対象ディレクトリ（必須・誤削除防止のため明示指定）');
  console.error('  日数       この日数以上前の画像を削除（デフォルト: 7）');
  console.error('  --dry-run  削除せずリストのみ表示');
  process.exit(1);
}

if (!fs.existsSync(targetDir) || !fs.statSync(targetDir).isDirectory()) {
  console.error(`❌ 対象ディレクトリが存在しません: ${targetDir}`);
  process.exit(1);
}

const daysArg = args.filter((a, i) => i !== dirIdx + 1).find(a => /^\d+$/.test(a));
const retentionDays = daysArg !== undefined ? parseInt(daysArg) : DEFAULT_DAYS;
const cutoffDate = new Date(Date.now() - retentionDays * 24 * 60 * 60 * 1000);

console.log(`🧹 GBP診断スクリーンショット クリーンアップ`);
console.log(`   ディレクトリ: ${targetDir}`);
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

// 指定ディレクトリ配下をスキャン
scanDir(targetDir);

console.log('');
console.log(`📊 結果:`);
console.log(`   全ファイル: ${totalFiles}件 (${(totalSize / 1024 / 1024).toFixed(1)}MB)`);
console.log(`   ${dryRun ? '削除対象' : '削除済み'}: ${deletedFiles}件 (${(deletedSize / 1024 / 1024).toFixed(1)}MB)`);
console.log(`   残存: ${totalFiles - deletedFiles}件 (${((totalSize - deletedSize) / 1024 / 1024).toFixed(1)}MB)`);

if (dryRun && deletedFiles > 0) {
  console.log('');
  console.log(`💡 実際に削除するには: node scripts/cleanup_screenshots.js --dir "${targetDir}" ${retentionDays}`);
}
