# step1 — テンプレ差し込み（シート → message）

会社名だけを変数にしたテンプレ営業文を、シートの `company_name` 列から社名を取り込んで
差し替え、指定列（既定 `message`）へ書き戻す。**AIなし・HP不要の決定論的な文字置換**。

## テンプレ記法
- 保存先：`shared/message_template.md`（初回は `cp shared/3_message_template.example.md shared/message_template.md`）
- 本文として使われるのは `---本文ここから---` 〜 `---本文ここまで---` の間だけ。
- 行頭 `<!--` のコメント行は無視。
- **差し込める変数は `{company_name}`（会社名）のみ。** 他の `{◯◯}`（氏名・電話など）は
  そのまま文字として残る＝テンプレ側で自分の情報に書き換えておく。
- 敬称（御中/様）は**テンプレ内に手書き**する（例：`{company_name} 御中`）。スキルは付与しない。

## 実行手順
0. 初回のみ依存を用意：このスキルのディレクトリで `uv sync`。
1. テンプレ準備を確認（無ければ example をコピーして自分の営業文に編集）。
2. まず `--preview` で列マッピングと出力先を確認（1セルも書かない）：
   ```
   uv run python scripts/merge_on_sheet.py <シートURL> --preview
   ```
   - `company_name` 入力列と、`message`（既定）出力列の検出結果・上書き有無・先頭サンプルが出る。
3. ★最初は `--limit 3` で数社だけ差し込み、シート上の文面を人間レビュー：
   ```
   uv run python scripts/merge_on_sheet.py <シートURL> --limit 3
   ```
4. 問題なければ全件：
   ```
   uv run python scripts/merge_on_sheet.py <シートURL>
   ```

## オプション
| 引数 | 既定 | 説明 |
|---|---|---|
| `--worksheet NAME` | 先頭シート | 対象ワークシート |
| `--template PATH` | `shared/message_template.md` | 別テンプレを使う場合 |
| `--out-col NAME` | `message` | 出力先ヘッダ名（統一スキーマ互換は message） |
| `--company-col NAME` | 自動検出 | 会社名入力列（『会社名』等の日本語列にも対応） |
| `--limit N` | 0（全件） | 先頭N社のみ |
| `--force` | off | 出力列が記入済みの行も再生成（既定は未記入行のみ） |
| `--preview` | off | 確認のみ・書き込みなし |
| `--creds PATH` | sheets_io 準拠 | サービスアカウントJSON |

## 再実行ポリシー
既定では出力列が**未記入の行だけ**差し込む（二重生成を避ける）。全行やり直すなら `--force`。

## 完了条件
- 出力列（既定 `message`）に「テンプレ全文の {company_name} を各社名へ差し替えた営業文」が入る。
- `message` 列として ⑤form-send / 000-pipeline へそのまま接続できる。
