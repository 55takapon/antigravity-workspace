# kick_sales.ps1 <job>  — 配布用・汎用kick殻（Windows / Task Scheduler から起動）。job = prep | send
# ★雛形（要実地検証）。Mac版 kick_sales.sh と同じ挙動を PowerShell で再現する。
#   prep : ①②③（送信しない）。send : schedule.json の send.mode に従う（notify 既定 / auto）。
param(
  [string]$Job = "prep",
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"

$ConfigPath = Join-Path $HOME ".simesapo-sales\schedule.json"
$ClaudeBin  = "claude"   # PATH 上の claude（nodebrew/npm グローバル）
$LogDir     = Join-Path $HOME "AppData\Local\simesapo-sales\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "claude-sales-$Job.log"

function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -Append -Encoding utf8 $Log }
function Fail($m) { Log "ERROR: $m"; throw $m }

if (-not (Test-Path $ConfigPath)) { Fail "設定がありません: $ConfigPath" }
$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$RepoRoot = $cfg.repo_root
$SheetKey = $cfg.sheet_key
$Criteria    = $cfg.criteria
$SendMode    = $cfg.send.mode
$Cap         = $cfg.send.cap
$MessageMode = if ($cfg.prep.message_mode) { $cfg.prep.message_mode } else { "ai" }
$PrepCount   = if ($cfg.prep.count) { $cfg.prep.count } else { 100 }
if (-not $SheetKey) { Fail "sheet_key 未設定" }

# --- ホスト解決（config.host: auto|claude|codex。auto=claude優先→codex）※$Host は予約変数のため $UseHost ---
$UseHost   = if ($cfg.host) { $cfg.host } else { "auto" }
$CodexBin  = "codex"
$CodexFlags = if ($cfg.codex_exec_flags) { $cfg.codex_exec_flags } else { "--full-auto" }
if ($UseHost -eq "auto") {
  if (Get-Command claude -ErrorAction SilentlyContinue) { $UseHost = "claude" }
  elseif (Get-Command codex -ErrorAction SilentlyContinue) { $UseHost = "codex" }
  else { Fail "claude も codex も見つかりません（どちらかのCLIが必要）" }
}
Set-Location $RepoRoot

# ロック（ジョブ別）
$Lock = Join-Path $RepoRoot "ops\scheduler\.lock-$Job"
if (Test-Path $Lock) {
  $age = (Get-Date) - (Get-Item $Lock).CreationTime
  if ($age.TotalMinutes -lt 180) { Fail "別の実行が進行中 ($Job)" } else { Remove-Item -Recurse -Force $Lock }
}
New-Item -ItemType Directory -Force -Path $Lock | Out-Null
try {
  Log "=== kick_sales $Job start (dry=$DryRun, mode=$SendMode) ==="

  $baseTools = @("Read","Write","Bash(python *)","Bash(uv *)","WebFetch","WebSearch",
    "mcp__opener-core__get_skill_flow","mcp__opener-core__list_build_queries",
    "mcp__opener-core__list_parse_jobposting","mcp__opener-core__list_pick_official_url",
    "mcp__opener-core__list_filter_exclude","mcp__opener-core__contact_detect",
    "mcp__opener-core__get_opener_prompt")

  if ($Job -eq "prep") {
    # ★実行レシピは秘匿フロー schedule-run（サーバー）に閉じる。ここは委譲だけの薄殻。
    $allowed = $baseTools
    $drynote = if ($DryRun) { "これはドライラン。各工程は --preview のみ・シートへ書き込まず確認して終わること。" } else { "" }
    $prompt = @"
あなたは simesapo-sales-auto-skills です。opener-core の get_skill_flow を {"skill":"schedule-run"} で呼び、返る手順に厳密に従って実行してください（無人実行・依頼確認は挟まない）。
パラメータ: sheet_key=$SheetKey / count=$PrepCount / message_mode=$MessageMode / criteria=$Criteria
$drynote
手順が定める安全弁（④送信は絶対にしない・message列まで用意して停止）を厳守し、最後にサマリを1メッセージで出力。
"@
  } elseif ($Job -eq "send") {
    if ($SendMode -eq "auto" -and -not $DryRun) {
      $allowed = $baseTools + @("mcp__playwright__browser_navigate","mcp__playwright__browser_snapshot",
        "mcp__playwright__browser_click","mcp__playwright__browser_type","mcp__playwright__browser_fill_form",
        "mcp__playwright__browser_select_option","mcp__playwright__browser_press_key",
        "mcp__playwright__browser_wait_for","mcp__playwright__browser_take_screenshot",
        "mcp__playwright__browser_navigate_back","mcp__playwright__browser_handle_dialog",
        "mcp__playwright__browser_evaluate","mcp__playwright__browser_find","mcp__playwright__browser_close")
      $prompt = @"
あなたは simesapo-sales-auto-skills です。005-form-send で、シート(キー: $SheetKey) の未送信行へ送信。必ず --limit $Cap（1回上限）、--force は付けない。status=excluded は送らない。reCAPTCHA等はスキル規定どおり assist/手動へ振り分け、無理に送らない。
最後に 送信成功/スキップ/失敗(理由) の件数サマリを出力。
"@
    } else {
      $allowed = @("Read","Bash(python *)")
      $prompt = @"
あなたは simesapo-sales-auto-skills です。送信はしないこと。005-form-send の run_on_sheet.py を --preview で回し、シート(キー: $SheetKey) の未送信で送信対象になる行数を数え、『本日の送信候補は N 件です。確認して手動送信してください』とだけ出力。
"@
    }
  } else { Fail "未知のjob: $Job" }

  if ($UseHost -eq "claude") {
    & $ClaudeBin -p $prompt --allowedTools $allowed --max-turns 150 --max-budget-usd 6.00 --no-session-persistence *>> $Log
  } else {
    # Codex（無人実行）。ツールは ~/.codex/config.toml の MCP から供給＝per-run のツール制限は無い。
    # ★prep の「送信ツール非許可＝構造的に送れない」保証は効かず、プロンプトの安全弁で担保。
    #   $CodexFlags 既定 --full-auto＝承認を挟まない。--max-budget-usd 相当も無い。⚠️未実機検証。
    & $CodexBin exec ($CodexFlags -split ' ') $prompt *>> $Log
  }
  if ($LASTEXITCODE -ne 0) { Fail "$UseHost $Job run exited $LASTEXITCODE" }
  Log "=== kick_sales $Job end (rc=0) ==="
}
finally { Remove-Item -Recurse -Force $Lock -ErrorAction SilentlyContinue }
