# Google Sheets API 連携 セットアップガイド

このガイドの手順を **1回だけ** 実施していただければ、以後はスプレッドシートの自動読み書きが使えるようになります。

---

## Step 1：Google Cloud でサービスアカウントを作成する（約5分）

1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. 左上のプロジェクト名をクリック → **「新しいプロジェクト」** を作成（名前は何でも可、例: `form-automation`）
3. 左メニュー **「APIとサービス」→「ライブラリ」** を開く
4. 検索欄に **「Google Sheets API」** と入力 → 選択 → **「有効にする」**
5. 左メニュー **「APIとサービス」→「認証情報」** を開く
6. 上部の **「認証情報を作成」→「サービスアカウント」** をクリック
7. サービスアカウント名に `form-automation` 等を入力 → **「作成して続行」→「完了」**
8. 作成したサービスアカウントをクリック → **「キー」タブ** → **「鍵を追加」→「新しい鍵を作成」→「JSON」** → ダウンロード

---

## Step 2：ダウンロードしたJSONファイルを配置する

1. ダウンロードしたJSONファイルの名前を **`google_credentials.json`** に変更する
2. **このフォルダ（`form_automation/`）** に置く

> ⚠️ このファイルは `.gitignore` に登録済みなので、GitHubに誤って公開されることはありません。

---

## Step 3：スプレッドシートをサービスアカウントと共有する

1. `google_credentials.json` をテキストエディタで開く
2. `"client_email"` の値（例: `form-automation@myproject.iam.gserviceaccount.com`）をコピー
3. 対象のGoogleスプレッドシートを開く
4. 右上の **「共有」** ボタンをクリック
5. コピーしたメールアドレスを貼り付け → **「編集者」** として追加 → **「送信」**

---

## Step 4：スプレッドシートIDをメモする

スプレッドシートのURLから `SPREADSHEET_ID` を確認します：
```
https://docs.google.com/spreadsheets/d/ [ここがID] /edit
```

---

## Step 5：実行する

```powershell
# スプレッドシートから直接読み込み & 結果を書き戻す
node auto_form_filler.js --sheets [SPREADSHEET_ID] --sheet-name [シート名] --submit --all-fields

# 例：
node auto_form_filler.js --sheets 1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk --sheet-name 260325test --submit --all-fields
```

---

## 書き込まれる内容

スクリプトは1件処理するごとに、該当行の以下の列を自動で更新します：

| 列名 | 内容 |
|---|---|
| `送信日` | 実行日（YYYY/MM/DD） |
| `送信○×` | `〇`（成功）/ `×`（失敗・NG） |
| `送信不可理由` | 失敗時の理由（営業NGキーワード等） |
