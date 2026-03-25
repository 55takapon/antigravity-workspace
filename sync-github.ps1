# sync-github.ps1
# 自動同期スクリプト

$INTERVAL = 300 # 秒単位（5分ごと）

function Sync-Git {
    Write-Host "$(Get-Date -Format 'HH:mm:ss') Checking for changes..." -ForegroundColor Cyan
    
    $status = git status --short
    if ($status) {
        Write-Host "Changes detected. Syncing..." -ForegroundColor Yellow
        git add .
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        git commit -m "Auto-sync: $timestamp"
        
        $remote = git remote
        if ($remote) {
            # プルとプッシュを実行
            git pull --rebase origin main
            git push origin main
            Write-Host "Successfully synced to GitHub." -ForegroundColor Green
        } else {
            Write-Host "Warning: No remote 'origin' found." -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "No changes detected." -ForegroundColor Gray
    }
}

Write-Host "Auto-sync script started. Monitoring every $INTERVAL seconds..." -ForegroundColor Cyan
while ($true) {
    Sync-Git
    Start-Sleep -Seconds $INTERVAL
}
