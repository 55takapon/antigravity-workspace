# GBP月次レポート バッチ — Windowsタスクスケジューラ登録スクリプト
#
# 使い方（管理者権限のPowerShellで実行）:
#   .\setup_scheduler.ps1
#
# 登録内容:
#   タスク名  : GBP月次レポート自動生成
#   トリガー  : 毎月1日 11:00
#   実行内容  : node batch_report.js（前月を自動判定）
#   作業Dir   : monthly-report フォルダ

$taskName   = "GBP月次レポート自動生成"
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$nodeExe    = (Get-Command node -ErrorAction SilentlyContinue).Source
$batchScript = Join-Path $scriptDir "batch_report.js"

if (-not $nodeExe) {
    Write-Error "node.exe が見つかりません。Node.jsをインストールしてください。"
    exit 1
}

# 既存タスクがあれば削除
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "既存のタスクを削除しました。"
}

# タスク設定
$action  = New-ScheduledTaskAction -Execute $nodeExe -Argument $batchScript -WorkingDirectory $scriptDir
$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At "11:00"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -Description "毎月1日11:00にGBPの月次レポートを自動生成します" `
    -RunLevel Highest

Write-Host ""
Write-Host "✅ タスクスケジューラへの登録が完了しました。"
Write-Host "   タスク名 : $taskName"
Write-Host "   実行日時 : 毎月1日 11:00"
Write-Host "   スクリプト: $batchScript"
Write-Host ""
Write-Host "▶ 今すぐテスト実行する場合:"
Write-Host "   Start-ScheduledTask -TaskName '$taskName'"
