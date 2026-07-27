---
name: template-fill
description: 会社名だけを変数にした固定のテンプレ営業文を、指定シートの company_name 列から社名を差し込んで message 列を作る。AIなし・HP不要の決定論的な文字置換で速い・安い・文面はユーザーが完全管理。「テンプレ営業文を差し込んで」「社名だけ差し替えて営業文を量産」「固定文で営業文を作って」「用意した営業文の宛名だけ差し替えて」で起動する。
allowed-tools: Bash(python *), Bash(uv *), Read, Write
---

# template-fill Skill

自分で用意した**固定のテンプレ営業文**を、宛名（会社名）だけ差し替えて量産する。
各社HPを読んでAI生成する ③opener-generate とは別物で、**AIなし・HP不要・決定論的**。
文面はユーザーが完全に管理する（速い・安い）。

## ③opener-generate との違い
- ③ = 各社HPを読み **AIで冒頭文を生成**（パーソナライズ・重い・BYOK/サーバー）。
- 本スキル = **AIなし・HP不要のテンプレ差し込み**（`{company_name}` の文字置換のみ）。
- どちらも統一スキーマの `message` 列を作る「代替手段」。message を作れば ⑤form-send /
  000-pipeline へそのまま繋がる。

## 手順
1. テンプレ準備：`shared/message_template.md`（初回は
   `cp shared/3_message_template.example.md shared/message_template.md` して自分の営業文に編集）。
   - 差し込める変数は `{company_name}` のみ。敬称（御中/様）はテンプレ内に手書き。
2. `references/step1_merge.md` に従って差し込み（初回のみ `uv sync`）：
   - `uv run python scripts/merge_on_sheet.py <シートURL> --preview`（列マッピング確認・書き込みなし）
   - ★ `--limit 3` で数社だけ差し込み、シート上の文面を人間レビュー
   - 問題なければ全件実行

## 契約（守る最低限）
- 出力は `message` 列（既定。`--out-col` で変更可）。列名は勝手に変えない。
- 会社名が空の行は差し込まない（Fail-safe）。既定は出力列が未記入の行だけ処理（二重生成防止）。
- ★大量に書き戻す前に、最初の数社は必ず人間レビュー。

## 入出力
- 今回はシートのみ（②③と同じ `--sheet` 経路＝`shared/sheets_io.py` を流用）。
- 会社名の入力列は `company_name`（『会社名』等の日本語列も自動検出。`--company-col` で明示可）。
