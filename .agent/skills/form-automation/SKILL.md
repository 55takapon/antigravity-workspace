---
name: form-automation
version: 1.0.0
description: PlaywrightベースのWebフォーム自動入力スキル。Google Sheetsから企業リストを読み込み、各社の問い合わせフォームに自動入力する（送信は人間が手動）。
tags: [playwright, google-sheets, form, automation, sales]
updated: 2026-04-12
disable-model-invocation: true
---

# 📝 フォーム自動入力スキル

> **実行ファイルの場所:** `C:\Users\hangy\.gemini\antigravity\scratch\form_automation\`
> **このスキルファイルは:** 使い方・ノウハウ・更新履歴を集積する知識ファイルです。

---

## ⚠️ 絶対ルール（厳守）

| # | ルール |
|---|--------|
| ❌ | スクリプトは**送信ボタンを押さない**（入力のみ） |
| ❌ | G列（送信日）に**日付が入力済みの行は対象外** |
| ❌ | I列（送信不可理由）に「営業NG」等の**コメントがある行は対象外** |
| ✅ | ユーザーが内容を確認してから**手動で送信ボタンを押す** |
| ✅ | 送信後、ターミナルで `y` を入力するとシートに送信日が自動記録される |
| 🤖 | AIがチャット上でコピー用テキストを作成・出力する際は、プロファイルの `{{company}} 代表取締役 {{rep_name}}様` に忠実に従い、**「代表取締役」等の役職を絶対に勝手に省略しない**（ただし `{{rep_name}}` が「ご担当者」の場合のみ「代表取締役」を省く） |

---

## 🚀 実行コマンド（標準）

```powershell
cd C:\Users\hangy\.gemini\antigravity\scratch\form_automation

node run_form_session.js `
  --sheets [スプレッドシートID] `
  --sheet-name [シート名] `
  --rows 2-10
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

## 📁 ファイル構成（実行フォルダ）

```
scratch/form_automation/
├── run_form_session.js          ← 人間確認型スクリプト（メイン）
├── auto_form_filler.js          ← 旧スクリプト（フル自動化用・非推奨）
├── web-company_profile.json     ← 制作会社向け送信プロファイル
├── web-company_mapping.json     ← フォームフィールドマッピング
├── marketing-company_profile.json  ← マーケ会社向け（参考）
├── google_credentials.json      ← Google Sheets API認証（.gitignore）
├── screenshots/                 ← 入力後スクリーンショット保存先
└── PROCEDURE.md                 ← 詳細手順書
```

---

## 📊 スプレッドシート列構成（標準フォーマット）

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

## 🔧 他業種への横展開

別の業種向けに同じ仕組みを使う場合：

1. プロファイルJSONを新規作成（例: `interior-company_profile.json`）
2. 必要に応じてマッピングJSONを新規作成
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

## ❓ トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------| 
| フォームが開かない | URLが間違っているか、サイトがBlocked → スクリーンショット確認 |
| 入力項目が空のまま | フォームのラベルが未マッチ → `web-company_mapping.json` にキーワード追加 |
| 送信日が記録されない | スプレッドシートの共有設定を確認（サービスアカウントに編集権限が必要） |
| 「営業NG」と判定された | フォームページに営業お断りの文言があるため自動スキップ |

---

## 📈 バージョン履歴

| バージョン | 日付 | 更新内容 |
|-----------|------|---------|
| v1.0 | 2026-04-12 | スキルファイル新規作成（scratch/form_automation/PROCEDURE.md から知識統合） |

---
*スキル保存場所: `C:\Users\hangy\.gemini\antigravity\.agent\skills\form-automation\SKILL.md`*
