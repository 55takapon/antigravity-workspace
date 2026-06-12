# sync-github.ps1
# GitHub backup script
# Usage:
#   .\sync-github.ps1                    # Auto-sync every 5 minutes
#   .\sync-github.ps1 -Once              # Run once
#   .\sync-github.ps1 -Once -Message "commit message"

param(
    [switch]$Once,
    [string]$Message = "",
    [int]$Interval = 300
)

$REPO_ROOT = "C:\Users\hangy\.gemini\antigravity"

function Sync-Git {
    param([string]$CommitMsg = "")

    Write-Host "$(Get-Date -Format 'HH:mm:ss') 変更チェック中..." -ForegroundColor Cyan

    Set-Location $REPO_ROOT

    $status = git status --short 2>&1
    if (-not $status) {
        Write-Host "変更なし。スキップ。" -ForegroundColor Gray
        return
    }

    Write-Host "変更を検出。バックアップ開始..." -ForegroundColor Yellow

    # staging
    git add -A
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: git add 失敗" -ForegroundColor Red
        return
    }

    # commit
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $msg = if ($CommitMsg) { $CommitMsg } else { "backup: auto-sync $timestamp" }
    git commit -m $msg
    if ($LASTEXITCODE -ne 0) {
        Write-Host "コミットするものがありません。" -ForegroundColor Gray
        return
    }

    # remote check
    $remote = git remote
    if (-not $remote) {
        Write-Host "WARNING: リモート origin なし。ローカルコミットのみ完了。" -ForegroundColor DarkYellow
        return
    }

    # stash google_credentials.json to avoid GitHub Secret Protection
    $credFile = Join-Path $REPO_ROOT "scratch\contact-auto\google_credentials.json"
    $credBak  = Join-Path $REPO_ROOT "scratch\contact-auto\google_credentials.json.bak"
    $hasCred  = Test-Path $credFile
    if ($hasCred) {
        Move-Item $credFile $credBak -Force
    }

    # pull --rebase (run stderr separately to avoid PS5.1 ErrorRecord wrapping)
    $pullOutput = git pull --rebase origin main
    $pullResult = $LASTEXITCODE
    if ($pullOutput) { Write-Host $pullOutput }

    # restore credentials
    if ($hasCred -and (Test-Path $credBak)) {
        Move-Item $credBak $credFile -Force
    }

    if ($pullResult -ne 0) {
        Write-Host "ERROR: pull --rebase 失敗。手動で解決してください。" -ForegroundColor Red
        git rebase --abort
        return
    }

    # push
    git push origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: GitHub へのバックアップ完了!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: push 失敗。ネットワーク接続を確認してください。" -ForegroundColor Red
    }
}

# entry point
if ($Once) {
    Sync-Git -CommitMsg $Message
} else {
    Write-Host "自動バックアップ開始。${Interval}秒ごとに監視中..." -ForegroundColor Cyan
    Write-Host "停止するには Ctrl+C を押してください。" -ForegroundColor DarkCyan
    while ($true) {
        Sync-Git -CommitMsg $Message
        Start-Sleep -Seconds $Interval
    }
}
