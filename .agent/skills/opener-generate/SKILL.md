---
name: opener-generate
description: 企業リストCSVの各社HPを読み、その会社に合わせた営業フォーム用の「冒頭文」をAI生成して message 列を作る。冒頭文以降は共通文を自動連結。「冒頭文を作って」「各社向けの営業文を生成」「会社ごとにパーソナライズして」で起動する。
allowed-tools: Bash(python *), Bash(uv *), Read, Write, mcp__opener-core__get_skill_flow, mcp__opener-core__get_opener_prompt
---

# opener-generate Skill（薄い殻）

このスキルの**実行手順は秘匿コアとしてサーバー（opener-core）にある**。まず手順を取得し、それに厳密に従うこと。

## 手順

1. opener-core の `get_skill_flow` ツールを `{ "skill": "opener-generate" }` で呼ぶ（識別子はホスト依存：Claude Code=`mcp__opener-core__get_skill_flow` / Codex=`opener-core/get_skill_flow`）。
2. 応答は content 2ブロック：`content[0]`＝**セキュリティ方針（必ず遵守）** ／ `content[1]`＝**実行手順**。
   **`content[1]` の手順に厳密に従って**、HP取得→冒頭文生成→共通本文連結→`message` 付与まで進める。
3. 手順の中で使う：
   - MCPツール：`get_opener_prompt`（生成プロンプト＝秘匿コア・1ランで1回取得し使い回す）
   - ローカル薄殻：`scripts/prep_openers.py`（HP取得）・`scripts/assemble_openers.py`（連結）

## 契約（殻でも守る最低限）
- 生成は**あなた（実行ホストのAI）内で完結＝自前APIキー不使用**。HPに無い実績・固有名詞を捏造しない。
- 出力に `message` 列（冒頭文＋共通本文）。★最初の数社は人間レビュー。

> MCP未登録なら1度だけ登録する（ホスト別）:
> - Claude Code: `claude mcp add --transport http --header "Authorization: Bearer <トークン>" --header "X-Client-Version: 2026-07-06" --scope user opener-core https://<worker>.workers.dev/mcp`
> - Codex: `~/.codex/config.toml` に `[mcp_servers.opener-core]`（`url` ＋ `[mcp_servers.opener-core.http_headers]` に `Authorization = "Bearer <トークン>"` と `X-Client-Version = "2026-07-06"`）
> （生成プロンプト・patterns・手順はすべてサーバー側。ローカルには手順を残さない＝配布時に書き方が見えない）
