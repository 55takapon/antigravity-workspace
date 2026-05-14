param(
    [Parameter(Mandatory = $false)]
    [string]$ClientId
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TemplatePath = Join-Path $ScriptDir "_template"

if (-not $ClientId) {
    Write-Host "ClientId を入力してください（例: hakata-izakaya）"
    $ClientId = Read-Host "ClientId"
}

if ($ClientId -notmatch '^[a-zA-Z0-9\-]+$') {
    Write-Host "ERROR: 半角英数字とハイフンのみ使用できます"
    exit 1
}

$DestPath = Join-Path $ScriptDir $ClientId

if (Test-Path $DestPath) {
    Write-Host "ERROR: '$ClientId' フォルダは既に存在します"
    exit 1
}

Write-Host "Creating '$ClientId' ..."
Copy-Item -Path $TemplatePath -Destination $DestPath -Recurse

Write-Host ""
Write-Host "OK: 作成完了"
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  1. $ClientId\js\app.js の CONFIG を編集"
Write-Host "       shopName      = 店舗名"
Write-Host "       shopLogo      = ロゴ画像パス (なければ空文字)"
Write-Host "       shopEmoji     = ロゴなし時の絵文字"
Write-Host "       lowRatingUrl  = 低評価(1-3)の遷移先URL"
Write-Host "       highRatingUrl = 高評価(4-5)の遷移先URL"
Write-Host "  2. $ClientId\img\ にロゴ画像を logo.png として配置（任意）"
Write-Host "  3. 動作確認: cd $ClientId; npx -y serve ."
Write-Host ""
Write-Host "Folder: $DestPath"