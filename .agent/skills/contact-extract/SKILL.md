---
name: contact-extract
description: 企業リスト（CSV または Googleスプレッドシート）の各社HP（url列）から問い合わせページURLを抽出・正規化し、contact_url列を足す。「シートのURLを問い合わせページのリンクに変換して」「スプレッドシートの会社の問い合わせフォームURLを埋めて」「問い合わせURLを抽出」「各社の問い合わせページを探して」「contact_urlを埋めて」で起動する。
allowed-tools: Bash(python *), Bash(uv *), Read, Write, mcp__opener-core__get_skill_flow, mcp__opener-core__contact_detect
---

# contact-extract Skill（薄い殻）

このスキルの**実行手順は秘匿コアとしてサーバー（opener-core）にある**。まず手順を取得し、それに厳密に従うこと。

## 手順

1. opener-core の `get_skill_flow` ツールを `{ "skill": "contact-extract" }` で呼ぶ（識別子はホスト依存：Claude Code=`mcp__opener-core__get_skill_flow` / Codex=`opener-core/get_skill_flow`）。
2. 応答は content 2ブロック：`content[0]`＝**セキュリティ方針（必ず遵守）** ／ `content[1]`＝**実行手順**。
   **`content[1]` の手順に厳密に従って**、各社HP→問い合わせURL抽出→`contact_url` 付与まで進める。
3. 手順の中で使う：
   - MCPツール：`contact_detect`（検出＝秘匿コア）
   - ローカル薄殻：`scripts/fetch_pages.py`（素材化）・`scripts/write_contacts.py`（書き戻し＋probe確認）・
     `scripts/run_on_sheet.py`／`scripts/fetch_sheet.py`（シート入出力）

## 契約（殻でも守る最低限）
- produce：`company_name, url, contact_url` の3列キー付き。列名は変えない。未検出は空（Fail-safe）。

> MCP未登録なら1度だけ登録する（ホスト別）:
> - Claude Code: `claude mcp add --transport http --header "Authorization: Bearer <トークン>" --header "X-Client-Version: 2026-07-06" --scope user opener-core https://<worker>.workers.dev/mcp`
> - Codex: `~/.codex/config.toml` に `[mcp_servers.opener-core]`（`url` ＋ `[mcp_servers.opener-core.http_headers]` に `Authorization = "Bearer <トークン>"` と `X-Client-Version = "2026-07-06"`）
> （検出ルール・共通パス・手順はすべてサーバー側。ローカルには手順を残さない＝配布時に書き方が見えない）
