# auto_cleanup.ps1 - Antigravity 週次クリーンアップ
# タスクスケジューラーから週次実行される（毎週日曜 3:00）
# 分析・リサーチで蓄積した一時ファイル・スクショを自動削除する

$repoPath  = "C:\Users\hangy\.gemini\antigravity"
$logFile   = "$repoPath\auto_backup.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$totalDeleted = 0
$totalSizeMB  = 0

Set-Location $repoPath

function Remove-TempDir {
    param([string]$Path, [string]$Label, [bool]$Recreate = $false)

    if (-not (Test-Path $Path)) {
        Add-Content $logFile "[$timestamp] CLEANUP: $Label - スキップ（パスなし）"
        return
    }

    $files = Get-ChildItem $Path -Recurse -File -ErrorAction SilentlyContinue
    $count = $files.Count
    $sizeMB = [math]::Round(($files | Measure-Object Length -Sum).Sum / 1MB, 1)

    Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue

    if ($Recreate) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }

    Add-Content $logFile "[$timestamp] CLEANUP: $Label - ${count}ファイル / ${sizeMB}MB 削除"

    $script:totalDeleted += $count
    $script:totalSizeMB  += $sizeMB
}

Add-Content $logFile "[$timestamp] CLEANUP: ===== 週次クリーンアップ 開始 ====="

# ─────────────────────────────────────────────────────────────────
# [1] ブラウザ録画フレーム（browser_recordings/ 以下を全削除・再作成）
# ─────────────────────────────────────────────────────────────────
Remove-TempDir -Path "$repoPath\browser_recordings" `
               -Label "browser_recordings/" `
               -Recreate $true

# ─────────────────────────────────────────────────────────────────
# [2] 会話ごとの一時メディアキャッシュ（brain/*/.tempmediaStorage）
# ─────────────────────────────────────────────────────────────────
Get-ChildItem "$repoPath\brain" -Recurse -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq ".tempmediaStorage" } |
    ForEach-Object {
        Remove-TempDir -Path $_.FullName -Label ".tempmediaStorage ($($_.Parent.Name))" -Recreate $false
    }

# ─────────────────────────────────────────────────────────────────
# [3] フォーム送信スクショ（contact-auto/screenshots/）
# ─────────────────────────────────────────────────────────────────
Remove-TempDir -Path "$repoPath\scratch\contact-auto\screenshots" `
               -Label "contact-auto/screenshots/" `
               -Recreate $true

# ─────────────────────────────────────────────────────────────────
# サマリーログ
# ─────────────────────────────────────────────────────────────────
Add-Content $logFile "[$timestamp] CLEANUP: ===== 完了 | 合計 ${totalDeleted}ファイル / ${totalSizeMB}MB 解放 ====="
