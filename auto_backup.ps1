# auto_backup.ps1 - antigravity-workspace 自動バックアップ
# タスクスケジューラーから定期実行される

$repoPath = "C:\Users\hangy\.gemini\antigravity"
$logFile  = "$repoPath\auto_backup.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Set-Location $repoPath

# --- ステージング ---
# .gitignoreのルールに従って、画像ファイルなどを除外しながらすべての変更を追加
git add . 2>$null

# 既存のルール引き継ぎ：TSVファイルは.gitignoreで除外されているが強制的に追加する
git add -f codex_project/*.tsv 2>$null

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
