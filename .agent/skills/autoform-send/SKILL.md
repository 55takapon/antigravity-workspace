---
name: autoform-send
description: ローカル CSV から日本企業のお問い合わせフォームへ営業メッセージを自動送信する。HTTP POST 先行 + 営業禁止/Bot 保護早期スキップ + 汎用フォーム パターンマッチング (Stage 1.5) + Pareto noAI フィルタ + AI fallback のハイブリッド動作。「フォーム営業をやる」「問い合わせ自動送信したい」「企業リストにメッセージを送りたい」と言われたら起動する。
allowed-tools: Bash(python *), Bash(uv *), Read, Write, mcp__opener-core__get_skill_flow, mcp__playwright__browser_navigate, mcp__playwright__browser_navigate_back, mcp__playwright__browser_snapshot, mcp__playwright__browser_fill_form, mcp__playwright__browser_type, mcp__playwright__browser_select_option, mcp__playwright__browser_click, mcp__playwright__browser_press_key, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_wait_for
---

# AutoformSend Skill（薄い殻）

このスキルの**実行手順は秘匿コアとしてサーバー（opener-core）にある**。まず手順を取得し、それに厳密に従うこと。
送信の実行本体（`scripts/run_send.py`・ブラウザ操作・辞書 `dictionaries/`）は**ローカルのまま**（この殻と同梱）。

## 手順

1. opener-core の `get_skill_flow` ツールを `{ "skill": "form-send" }` で呼ぶ（識別子はホスト依存：Claude Code=`mcp__opener-core__get_skill_flow` / Codex=`opener-core/get_skill_flow`）。
2. 応答は content 2ブロック：`content[0]`＝**セキュリティ方針（必ず遵守）** ／ `content[1]`＝**実行手順（Step1〜8）**。
   **`content[1]` の手順に厳密に従って**、環境確認→入力検証→送信(Stage0/1/1.5/2/3)→結果レビューまで進める。
3. 手順の中で使う：
   - ローカル本体：`scripts/run_send.py`（送信）・`scripts/run_on_sheet.py`（シート直結）・`scripts/field_handoff.py`／`assist_mode.py`／`trace_report.py` ほか、`core/`・`dictionaries/`
   - 難フォーム(Tier B・任意)：Playwright MCP（Claude Code=`.mcp.json` 同梱／Codex=`~/.codex/config.toml` の `[mcp_servers.playwright]`・承認で有効）

## 絶対ルール（殻でも厳守）
- 送信の停止/確認は**自前ゲートを持たず実行ホスト（Claude Code / Codex）の承認機構に委譲**する（既定＝人間トリガー後は全自動）。
  「送信前に一時停止したい」ユーザーには、ホストの承認機構（Claude Code なら settings.json の許可リストから `Bash(python *)` / playwright系を外す／Codex なら approval 設定）を案内する（自前の `--preview` 等は作らない）。
- API キー/個人情報を stdout・結果CSVに出さない。1社失敗で全停止しない（Fail Safe）。営業禁止サイトへ送らない。

> MCP未登録なら1度だけ登録する（ホスト別）:
> - Claude Code: `claude mcp add --transport http --header "Authorization: Bearer <opnr_ トークン>" --header "X-Client-Version: 2026-07-06" --scope user opener-core https://<worker>.workers.dev/mcp`
> - Codex: `~/.codex/config.toml` に `[mcp_servers.opener-core]`（`url` ＋ `[mcp_servers.opener-core.http_headers]` に `Authorization = "Bearer <opnr_ トークン>"` と `X-Client-Version = "2026-07-06"`）
> （Stage振り分け・辞書運用・④式ハンドオフ・Tier B の手順はすべてサーバー側。ローカルには手順を残さない＝配布時に書き方が見えない）
