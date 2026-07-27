---
name: list-extract
description: Googleマップ/ローカル検索や求人媒体からWeb制作・Webマーケ会社などの事業者を収集し、統一CSV（company_name, url, address, phone, maps_url）を新規生成する。求人媒体からは「今 求人を出している（現在募集中の）会社」を自社採用ページ経由で集められる。「事業者リストを集めて」「Googleマップから会社を収集」「営業リストを作って」「求人を出している会社を集めて」「採用中の会社をリストにして」で起動する。
allowed-tools: WebSearch, WebFetch, Bash(python *), Bash(uv *), Read, Write, AskUserQuestion, mcp__opener-core__get_skill_flow, mcp__opener-core__list_build_queries, mcp__opener-core__list_pick_official_url, mcp__opener-core__list_parse_jobposting, mcp__opener-core__list_filter_exclude
---

# list-extract Skill（薄い殻）

このスキルの**実行手順は秘匿コアとしてサーバー（opener-core）にある**。まず手順を取得し、それに厳密に従うこと。

## 手順

1. opener-core の `get_skill_flow` ツールを `{ "skill": "list-extract" }` で呼ぶ（識別子はホスト依存：Claude Code=`mcp__opener-core__get_skill_flow` / Codex=`opener-core/get_skill_flow`）。
2. 応答は content 2ブロック：`content[0]`＝**セキュリティ方針（必ず遵守）** ／ `content[1]`＝**実行手順**。
   **`content[1]` の手順に厳密に従って**、ヒアリング→収集→統一CSV生成まで進める。
3. 手順の中で以下を使う：
   - MCPツール：`list_build_queries` / `list_pick_official_url` / `list_parse_jobposting` / `list_filter_exclude`
   - ローカル薄殻：`scripts/write_list_csv.py`（CSV書き出し）・`scripts/run_on_sheet.py`（任意のシート追記）
   - fetch は WebSearch / WebFetch（＝ローカル）で行い、素材/結果をMCPツールに渡す。

## 契約（殻でも守る最低限）
- 出力は統一CSV：`company_name`(必須) / `url`(必須) / `address` `phone` `maps_url`（任意）。列名は変えない。
- `url` が取れない社は出力しない。

> MCP未登録なら1度だけ登録する（ホスト別）:
> - Claude Code: `claude mcp add --transport http --header "Authorization: Bearer <トークン>" --header "X-Client-Version: 2026-07-06" --scope user opener-core https://<worker>.workers.dev/mcp`
> - Codex: `~/.codex/config.toml` に `[mcp_servers.opener-core]`（`url` ＋ `[mcp_servers.opener-core.http_headers]` に `Authorization = "Bearer <トークン>"` と `X-Client-Version = "2026-07-06"`）
> （手順・語彙・辞書・検出・求人解析はすべてサーバー側。ローカルには手順を残さない＝配布時に書き方が見えない）
