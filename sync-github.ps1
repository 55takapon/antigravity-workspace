# sync-github.ps1
# 変更を自動的にコミットしてプル/プッシュするスクリプト

$INTERVAL = 300 # 秒単位（例：5分ごと）

function Sync-Git {
    Write-Host "Checking for changes..." -ForegroundColor Cyan
    
    # 未コミットの変更があるか確認
    $status = git status --short
    if ($status) {
        Write-Host "Changes detected. Syncing..." -ForegroundColor Yellow
        git add .
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git commit -m "Auto-sync: $timestamp"
        
        # リモートが設定されている場合のみプッシュ
        $remote = git remote
        if ($remote) {
            git pull --rebase origin main
            git push origin main
            Write-Host "Successfully synced to GitHub." -ForegroundColor Green
        } else {
            Write-Host "Warning: No remote 'origin' found. Changes committed locally." -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "No changes detected." -ForegroundColor Gray
    }
}

# 無限ループで定期実行（必要に応じてタスクスケジューラなどで実行することを推奨）
while ($true) {
    Sync-Git
    Start-Sleep -Seconds $INTERVAL
}
