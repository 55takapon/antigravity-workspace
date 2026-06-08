# auto_backup.ps1 - 自動バックアップ（2時間ごと）
# 対象: antigravity / .codex / .cursor
# タスクスケジューラーから定期実行される

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# ── バックアップ対象リポジトリ ─────────────────────────────────
$repos = @(
    @{ Path = "C:\Users\hangy\.gemini\antigravity"; Label = "antigravity" },
    @{ Path = "C:\Users\hangy\.codex";              Label = "codex"       },
    @{ Path = "C:\Users\hangy\.cursor";             Label = "cursor"      }
)

$logFile = "C:\Users\hangy\.gemini\antigravity\auto_backup.log"

# ── antigravity のみ: スキルダッシュボード再生成 ──────────────
$dashboardScript = "C:\Users\hangy\.gemini\antigravity\scratch\skill-dashboard\generate-data.ps1"
if (Test-Path $dashboardScript) {
    & powershell.exe -NonInteractive -ExecutionPolicy Bypass -File $dashboardScript 2>$null
    Add-Content $logFile "[$timestamp] DASHBOARD: skills-data.js を再生成しました"
} else {
    Add-Content $logFile "[$timestamp] DASHBOARD: スクリプトが見つかりません ($dashboardScript)"
}

# ── 各リポジトリをバックアップ ────────────────────────────────
foreach ($repo in $repos) {
    Set-Location $repo.Path

    git add . 2>$null

    # antigravity のみ: TSVファイルを強制追加
    if ($repo.Label -eq "antigravity") {
        git add -f codex_project/*.tsv 2>$null
    }

    $status = git status --porcelain
    if ($status) {
        $msg = "auto-backup: $timestamp"
        git commit -m $msg 2>$null
        git push 2>$null
        Add-Content $logFile "[$timestamp] [$($repo.Label)] BACKED UP: $($status.Count) changes"
    } else {
        Add-Content $logFile "[$timestamp] [$($repo.Label)] No changes"
    }
}
