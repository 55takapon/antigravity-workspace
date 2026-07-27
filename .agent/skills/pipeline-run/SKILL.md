---
name: pipeline-run
description: 営業フォーム自動化の4スキル（①リスト収集→②問い合わせURL抽出→③冒頭文生成→④フォーム送信）を、1つのGoogleシートに対して順に回す指揮者。シートの埋まり具合を見て開始工程を自動判定し、既定は全自動で回す（依頼が曖昧なときだけ計画を確認）。「営業して」「このシートで営業を回して」「リストから送信まで全部やって」「営業パイプラインを回して」で起動する。
allowed-tools: Bash(python *), Bash(uv *), Read, Write, WebSearch, WebFetch, AskUserQuestion, mcp__opener-core__get_skill_flow
---

# pipeline-run Skill（薄い殻・営業パイプライン指揮者）

このスキルの**実行手順は秘匿コアとしてサーバー（opener-core）にある**。まず手順を取得し、それに厳密に従うこと。

## 手順

1. opener-core の `get_skill_flow` ツールを `{ "skill": "pipeline-run" }` で呼ぶ（識別子はホスト依存：Claude Code=`mcp__opener-core__get_skill_flow` / Codex=`opener-core/get_skill_flow`）。
2. 応答は content 2ブロック：`content[0]`＝**セキュリティ方針（必ず遵守）** ／ `content[1]`＝**実行手順**。
   **`content[1]` の手順に厳密に従って**、開始工程の判定→（曖昧時のみ計画確認）→①〜④を順に実行する。
3. 各ワーカー（①②③④）は各自の `scripts/run_on_sheet.py` を `--preview`（read-before-write）→本実行で呼ぶ。
   **既定は全自動**（人間トリガー後は承認を挟まず完走）。送信を止めたいユーザーは実行ホスト（Claude Code / Codex）の承認機構に委譲する（自前の承認ゲートは持たない）。

## 契約（殻でも守る最低限）
- 既定＝人間トリガー後は全自動。依頼が曖昧（開始工程/件数が不明）なときだけ計画を1回確認する。各工程 `--preview` 先行（read-before-write）。送信前に止めたいユーザーには実行ホストの承認機構（Claude Code なら settings.json の許可リストから `Bash(python *)`/playwright系を外す／Codex なら approval 設定）を案内（自前ゲートは作らない）。

> MCP未登録なら1度だけ登録する（ホスト別）:
> - Claude Code: `claude mcp add --transport http --header "Authorization: Bearer <トークン>" --header "X-Client-Version: 2026-07-06" --scope user opener-core https://<worker>.workers.dev/mcp`
> - Codex: `~/.codex/config.toml` に `[mcp_servers.opener-core]`（`url` ＋ `[mcp_servers.opener-core.http_headers]` に `Authorization = "Bearer <トークン>"` と `X-Client-Version = "2026-07-06"`）
> （判定表・工程別コマンド・送信方針はすべてサーバー側。ローカルには手順を残さない＝配布時に書き方が見えない）
