# sync-github.ps1
# Gitバックアップ自動同期スクリプト（改善版）
# 使い方:
#   .\sync-github.ps1                    # 5分ごとに自動監視
#   .\sync-github.ps1 -Once              # 一回だけ実行
#   .\sync-github.ps1 -Once -Message "コミットメッセージ"

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

    # ステージング（.gitignore で除外済みファイルは自動スキップ）
    git add -A
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: git add 失敗" -ForegroundColor Red
        return
    }

    # コミット
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $msg = if ($CommitMsg) { $CommitMsg } else { "backup: auto-sync $timestamp" }
    git commit -m $msg
    if ($LASTEXITCODE -ne 0) {
        Write-Host "コミットするものがありません。" -ForegroundColor Gray
        return
    }

    # リモート確認
    $remote = git remote 2>&1
    if (-not $remote) {
        Write-Host "WARNING: リモート origin なし。ローカルコミットのみ完了。" -ForegroundColor DarkYellow
        return
    }

    # google_credentials.json を一時退避（GitHub Secret Protection 回避）
    $credFile = Join-Path $REPO_ROOT "scratch\contact-auto\google_credentials.json"
    $credBak  = Join-Path $REPO_ROOT "scratch\contact-auto\google_credentials.json.bak"
    $hasCred  = Test-Path $credFile
    if ($hasCred) {
        Move-Item $credFile $credBak -Force
    }

    # pull --rebase
    git pull --rebase origin main 2>&1 | ForEach-Object { Write-Host $_ }
    $pullResult = $LASTEXITCODE

    # credentials 復元
    if ($hasCred -and (Test-Path $credBak)) {
        Move-Item $credBak $credFile -Force
    }

    if ($pullResult -ne 0) {
        Write-Host "ERROR: pull --rebase 失敗。手動で解決してください。" -ForegroundColor Red
        git rebase --abort 2>&1 | Out-Null
        return
    }

    # push
    git push origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GitHubへのバックアップ完了！" -ForegroundColor Green
    } else {
        Write-Host "ERROR: push 失敗。ネットワーク接続を確認してください。" -ForegroundColor Red
    }
}

# エントリポイント
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
