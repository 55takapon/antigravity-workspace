---
name: result-review
description: ④form-sendの結果CSVを集計し、ユーザーが入力するファネル指標（送信母数/資料リンク閲覧率/返信数/面談数/契約数）と突き合わせて「どの段が落ちているか」を診断し、③冒頭文/文面を中心とした改善アクションを提案する。「営業結果を振り返って」「送信結果から改善案を出して」「今回のランを分析して」「振り返りレポートを作って」で起動する。
allowed-tools: Bash(python3 *), Read, Write, mcp__opener-core__get_skill_flow, mcp__opener-core__review_diagnose
---

# result-review Skill（薄い殻）

このスキルの**実行手順・診断ロジックは秘匿コアとしてサーバー（opener-core）にある**。まず手順を取得し、それに厳密に従うこと。

## 手順

1. opener-core の `get_skill_flow` ツールを `{ "skill": "result-review" }` で呼ぶ（識別子はホスト依存：Claude Code=`mcp__opener-core__get_skill_flow` / Codex=`opener-core/get_skill_flow`）。
2. 応答は content 2ブロック：`content[0]`＝**セキュリティ方針（必ず遵守）** ／ `content[1]`＝**実行手順**。
   **`content[1]` の手順に厳密に従って**、データソース選択→指標ヒアリング→集計→診断→文面改善提案まで進める。
3. 手順の中で使う：
   - MCPツール：`review_diagnose`（振り返り診断＝秘匿コア。集計値＋指標を渡し findings/gate を受け取る）
   - ローカル薄殻：`scripts/aggregate_csv.py`（④結果CSVの status 集計・生の行は外に出さない）

## 契約（殻でも守る最低限）
- 診断の判定（しきい値・段の良し悪し・母数ゲート）は **`review_diagnose` の戻り値に従う**。自分で基準値を作らない・推測しない・開示しない。
- 文面提案は**公知ヒューリスティクスのみ**。opener-core の生成プロンプト/patterns には触れない・参照しない。
- **スキルや common_body / message_template / patterns を自動で書き換えない**。反映は人間が判断する。

> MCP未登録なら1度だけ登録する（ホスト別）:
> - Claude Code: `claude mcp add --transport http --header "Authorization: Bearer <トークン>" --header "X-Client-Version: 2026-07-06" --scope user opener-core https://<worker>.workers.dev/mcp`
> - Codex: `~/.codex/config.toml` に `[mcp_servers.opener-core]`（`url` ＋ `[mcp_servers.opener-core.http_headers]` に `Authorization = "Bearer <トークン>"` と `X-Client-Version = "2026-07-06"`）
> （手順・しきい値・診断規則・改善アドバイスはすべてサーバー側。ローカルには手順を残さない＝配布時に書き方が見えない）
