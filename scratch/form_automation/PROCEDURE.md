# フォーム自動入力 運用手順書

> **バージョン**: v1.0 (2026-03-31 作成)  
> **対象スクリプト**: `run_form_session.js`（人間確認型）

---

## ⚠️ 絶対ルール（厳守）

| # | ルール |
|---|--------|
| ❌ | スクリプトは**送信ボタンを押さない**（入力のみ） |
| ❌ | G列（送信日）に**日付が入力済みの行は対象外** |
| ❌ | I列（送信不可理由）に「営業NG」等の**コメントがある行は対象外** |
| ✅ | ユーザーが内容を確認してから**手動で送信ボタンを押す** |
| ✅ | 送信後、ターミナルで `y` を入力するとシートに送信日が自動記録される |

---

## 📋 送信前チェックリスト

スクリプトを実行する前に確認してください。

- [ ] スプレッドシートID・シート名・対象行が正しいか
- [ ] I列（送信不可理由）に記載のある行を除外しているか
- [ ] G列（送信日）が入力済みの行を除外しているか
- [ ] 送信文（`web-company_profile.json`）の内容が最新か
- [ ] `{{company}}` `{{rep_name}}` のプレースホルダーが機能するか確認

---

## 🚀 実行コマンド

### 基本形（制作会社向け）

```powershell
cd c:\Users\hangy\.gemini\antigravity\scratch\form_automation

node run_form_session.js `
  --sheets 1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk `
  --sheet-name 260325test `
  --rows 2-3
```

### 引数一覧

| 引数 | 必須 | 説明 |
|------|------|------|
| `--sheets <ID>` | ✅ | スプレッドシートID（URLの `/d/` と `/edit` の間） |
| `--sheet-name <名前>` | ✅ | シート名（タブ名） |
| `--rows <開始>-<終了>` | ✅ | 対象行（シート上の行番号、1行目=ヘッダー） |
| `--profile <ファイル名>` | ❌ | プロファイルJSONファイル名（デフォルト: `web-company_profile.json`） |
| `--mapping <ファイル名>` | ❌ | マッピングJSONファイル名（デフォルト: `web-company_mapping.json`） |
| `--all-fields` | ❌ | 任意項目にも入力する（デフォルト: 必須のみ） |

---

## 🔄 1件あたりの操作フロー

```
① スクリプトがスプレッドシートから対象行を読み込む
          ↓
② スキップ判定（送信日・営業NG・URLなし）
          ↓
③ ブラウザが自動で問い合わせフォームを開く
          ↓
④ 各フィールドに自動入力（会社名・代表者名を文章に挿入）
          ↓
⑤ ターミナルに「入力完了」の通知が表示される
          ↓
⑥ ユーザーがブラウザを確認 → 送信ボタンを手動でクリック
          ↓
⑦ ターミナルに戻り回答を入力:
     y = 送信済み（シートに送信日を自動記録）
     n = 送信しなかった
     s = この行をスキップ
          ↓
⑧ 次の行へ（同じ流れを繰り返す）
```

---

## 📊 スプレッドシート列構成（260325testシート）

| 列 | ヘッダー | 説明 |
|----|---------|------|
| A | № | 行番号 |
| B | エリア | 地域 |
| C | 企業名 | 送信先企業名（`{{company}}`に使用） |
| D | 代表者名 | 代表者名（`{{rep_name}}`に使用） |
| E | URL | 企業のWebサイトURL |
| F | 問い合わせフォームURL | 自動入力先URL |
| G | 送信日 | **入力済み→スキップ対象**（y入力で自動記録） |
| H | 送信○× | 送信結果（〇/×） |
| I | 送信不可理由 | **営業NG等→スキップ対象** |

---

## ✏️ 送信文テンプレート（`web-company_profile.json`）

送信文には2つのプレースホルダーが使えます：

- `{{company}}` → C列の企業名に自動置換
- `{{rep_name}}` → D列の代表者名に自動置換

**例**:
```
{{company}} 代表取締役 {{rep_name}}様
```
→ `ジェットプロデュース株式会社 代表取締役 田中様`

---

## 🔧 他業種への横展開

別の業種向けに同じ仕組みを使う場合：

1. プロファイルJSONを新規作成（例: `interior-company_profile.json`）
2. 必要に応じてマッピングJSONを新規作成（例: `interior-company_mapping.json`）
3. 実行時に `--profile` `--mapping` で指定

```powershell
node run_form_session.js `
  --sheets <SHEET_ID> `
  --sheet-name <シート名> `
  --rows 2-10 `
  --profile interior-company_profile.json `
  --mapping interior-company_mapping.json
```

---

## 🗂️ ファイル構成

```
form_automation/
├── run_form_session.js          ← 人間確認型スクリプト（メイン）
├── auto_form_filler.js          ← 旧スクリプト（フル自動化用・非推奨）
├── web-company_profile.json     ← 制作会社向け送信プロファイル
├── web-company_mapping.json     ← フォームフィールドマッピング
├── marketing-company_profile.json  ← マーケ会社向け（参考）
├── google_credentials.json      ← Google Sheets API認証（.gitignore）
├── screenshots/                 ← 入力後スクリーンショット保存先
└── PROCEDURE.md                 ← この手順書
```

---

## ❓ トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| フォームが開かない | URLが間違っているか、サイトがBlocked → スクリーンショット確認 |
| 入力項目が空のまま | フォームのラベルが未マッチ → `web-company_mapping.json` にキーワード追加 |
| 送信日が記録されない | スプレッドシートの共有設定を確認（サービスアカウントに編集権限が必要） |
| 「営業NG」と判定された | フォームページに営業お断りの文言があるため自動スキップ |
