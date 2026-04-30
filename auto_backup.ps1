# auto_backup.ps1 - antigravity-workspace 自動バックアップ
# タスクスケジューラーから定期実行される

$repoPath = "C:\Users\hangy\.gemini\antigravity"
$logFile  = "$repoPath\auto_backup.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Set-Location $repoPath

# --- ステージング ---
# contact-auto コアファイル
git add scratch/contact-auto/contact_auto.js 2>$null
git add scratch/contact-auto/core/ 2>$null
git add scratch/contact-auto/config/ 2>$null
git add scratch/contact-auto/temp_extract.js 2>$null

# スキルファイル
git add .agent/ 2>$null

# 日次レポート
git add daily-reports/ 2>$null

# small-company-research
git add scratch/small-company-research/.agent/ 2>$null
git add scratch/small-company-research/fix_ng_cells.js 2>$null

# codex_project（TSV は -f で強制、JSON も追加）
git add -f codex_project/*.tsv 2>$null
git add codex_project/*.json 2>$null
git add codex_project/*.js 2>$null
git add codex_project/*.md 2>$null

# --- 変更があれば commit & push ---
$status = git status --porcelain
if ($status) {
    $msg = "auto-backup: $timestamp"
    git commit -m $msg
    git push
    Add-Content $logFile "[$timestamp] BACKED UP: $($status.Count) changes"
} else {
    Add-Content $logFile "[$timestamp] No changes to backup"
}
