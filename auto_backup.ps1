# auto_backup.ps1 - antigravity-workspace 自動バックアップ
# タスクスケジューラーから定期実行される（2時間ごと）
# バックアップ前にスキルダッシュボードを自動再生成する

$repoPath      = "C:\Users\hangy\.gemini\antigravity"
$logFile       = "$repoPath\auto_backup.log"
$dashboardScript = "$repoPath\scratch\skill-dashboard\generate-data.ps1"
$timestamp     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Set-Location $repoPath

# ── スキルダッシュボード再生成 ──────────────────────────────────
if (Test-Path $dashboardScript) {
    & powershell.exe -NonInteractive -ExecutionPolicy Bypass -File $dashboardScript 2>$null
    Add-Content $logFile "[$timestamp] DASHBOARD: skills-data.js を再生成しました"
} else {
    Add-Content $logFile "[$timestamp] DASHBOARD: スクリプトが見つかりません ($dashboardScript)"
}

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
