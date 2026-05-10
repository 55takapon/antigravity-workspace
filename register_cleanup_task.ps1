# register_cleanup_task.ps1
# 【初回のみ管理者として実行してください】
# このスクリプトを右クリック → "管理者として実行" で実行すると
# タスクスケジューラに週次クリーンアップタスクが登録されます。

$taskName   = "AntigravityWeeklyCleanup"
$scriptPath = "C:\Users\hangy\.gemini\antigravity\auto_cleanup.ps1"
$xmlPath    = "C:\Users\hangy\.gemini\antigravity\AntigravityWeeklyCleanup.xml"

Write-Host "AntigravityWeeklyCleanup タスクを登録します..." -ForegroundColor Cyan

# 既存タスクがあれば削除
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# XML で登録
$result = schtasks /Create /TN $taskName /XML $xmlPath /F 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "===== 登録成功 =====" -ForegroundColor Green
    schtasks /Query /TN $taskName /FO LIST
    Write-Host ""
    Write-Host "次回実行: 毎週日曜日 3:00 AM" -ForegroundColor Yellow
    Write-Host "ログ出力先: C:\Users\hangy\.gemini\antigravity\auto_backup.log"
} else {
    Write-Host "エラー: $result" -ForegroundColor Red
    Write-Host "管理者として実行してください。" -ForegroundColor Red
}

Read-Host "Enterキーで終了"
