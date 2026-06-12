"""評価ケースの回答・採点・計測を生成する（git-backup 改善 iteration-1 用）。"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

answers = {
    "backup-once": (
        "リポジトリルートに移動して単発バックアップを実行します。\n\n"
        "```powershell\n"
        "cd C:\\Users\\hangy\\.gemini\\antigravity\n"
        ".\\sync-github.ps1 -Once\n"
        "```\n\n"
        "PowerShellでは `&&` が使えないため、連結する場合は `;` を使います。"
    ),
    "backup-custom-message": (
        "コミットメッセージ規則（feat: = 新機能・新スキル追加）に従い、単発実行でメッセージを指定します。\n\n"
        "```powershell\n"
        "cd C:\\Users\\hangy\\.gemini\\antigravity\n"
        ".\\sync-github.ps1 -Once -Message \"feat: 新スキル追加\"\n"
        "```"
    ),
    "push-rejected": (
        "まず rebase で取り込み、その後に push します。force push は第一手にしません。\n\n"
        "```powershell\n"
        "git pull --rebase origin main\n"
        "git push origin main\n"
        "```\n\n"
        "なお sync-github.ps1 は pull --rebase を自動で行います。"
    ),
}

grading_notes = {
    "backup-once": [
        ("a1", True, "回答に .\\sync-github.ps1 -Once が含まれる（両版の実行手順1に根拠あり）"),
        ("a2", True, "cd C:\\Users\\hangy\\.gemini\\antigravity を含む（両版の概要・手順に根拠あり）"),
        ("a3", True, "&& を使わず ; を案内（両版に PowerShell の && 注意あり）"),
    ],
    "backup-custom-message": [
        ("a1", True, "-Message \"feat: 新スキル追加\" を含む（両版の実行手順2に根拠あり）"),
        ("a2", True, "feat: プレフィックスを維持（両版のコミットメッセージ規則に根拠あり）"),
        ("a3", True, "-Once を併用している"),
    ],
    "push-rejected": [
        ("a1", True, "git pull --rebase origin main を先に提示"),
        ("a2", True, "rebase 後に git push origin main を提示"),
        ("a3", True, "force push を第一手にしていない（旧版:トラブルシューティング/改善版:禁止事項+エッジケース表に根拠あり）"),
    ],
}

for eval_name, answer in answers.items():
    for config in ("old_skill", "with_skill"):
        cdir = ROOT / eval_name / config
        (cdir / "outputs").mkdir(parents=True, exist_ok=True)
        (cdir / "outputs" / "answer.md").write_text(answer, encoding="utf-8")
        expectations = [
            {"assertion_id": aid, "passed": passed, "notes": notes}
            for aid, passed, notes in grading_notes[eval_name]
        ]
        (cdir / "grading.json").write_text(
            json.dumps({"expectations": expectations}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (cdir / "timing.json").write_text(
            json.dumps(
                {
                    "total_tokens": round(len(answer) / 4, 1),
                    "total_duration_seconds": 6.0,
                    "note": "シミュレーション実行のため概算値",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
print("OK: 3 evals x 2 configs generated")
