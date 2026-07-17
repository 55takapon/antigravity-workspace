# 起動・運用・トラブル対応

## 目的

サーバーの起動、オプション指定、NGワード管理、証跡・バックアップ運用、トラブル対応を1か所で参照できるようにする。

## 起動コマンド

作業ディレクトリ: `C:\Users\hangy\.cursor\test\contact-form-assist`

```powershell
# Web UIモード（推奨）
npm run ui -- --sheets <スプレッドシートID> --sheet-name <シート名>

# CSVモード
npm run ui -- --csv data\test_forms.csv

# CLIモード（ターミナル対話式）
npm run cli -- --sheets <スプレッドシートID> --sheet-name <シート名>
```

## オプション一覧

| オプション | 必須 | 説明 |
|---|---|---|
| `--sheets <ID>` | どちらか必須 | Google SheetsのスプレッドシートID |
| `--csv <パス>` | どちらか必須 | CSVファイルパス（Sheetsの代わり） |
| `--sheet-name <名前>` | 任意 | シート名（デフォルト: Sheet1） |
| `--rows <開始>-<終了>` | 任意 | 処理行範囲（例: 2-10。デフォルト: 2行目以降すべて） |
| `--profile <名前>` | 任意 | プロファイル名（デフォルト: web-company。config/profiles/ のファイル名） |
| `--campaign <ID>` | 任意 | キャンペーンID（二重送信判定キーに含まれる。デフォルト: default） |
| `--port <番号>` | 任意 | UIポート（デフォルト: 3001。127.0.0.1のみで待ち受け） |

## UI操作の流れ

1. 一覧から1件選び「ブラウザを開く」→ Playwrightが自動入力
2. 入力結果パネルで入力済み（緑）・必須未入力（赤）を確認
3. 未入力欄はブラウザ上で人間が補完 → 人間が送信ボタンを押す
4. UIで「送信した」を押すと記録され、次の1件へ
5. 中断したい場合は「スキップ」（理由コメント可）、動かなくなった場合は「強制キャンセル」

## NGワード管理

- 営業お断り検出語は `config/ng-keywords.json`（117語）で管理する
- 実運用で新しいお断り表現を見つけたら、このファイルに追記する（コード修正不要）
- 検出時はI列に「営業NG」、DBに検出語つきで記録される

## 証跡とバックアップ

| 対象 | 場所 | 保持ポリシー |
|---|---|---|
| スクリーンショット | `evidence/screenshots/` | 3日（毎日8:30 cleanup-evidence.ps1 が削除） |
| HTMLスナップショット | `evidence/html/` | 3日（同上） |
| 送信記録DB | `data/contact-assist.sqlite` | 無期限（削除禁止） |
| コード・設定 | GitHub `55takapon/cursor-test-backup` | 毎日6:57から3時間ごと backup.ps1 がpush |

## トラブル対応

| 症状 | 対応 |
|---|---|
| 「認証ファイルが見つかりません」 | `%USERPROFILE%\.gcp\contact-form-assist\google_credentials.json` の存在を確認。移設した場合は環境変数 `CONTACT_ASSIST_CREDENTIALS` で新パスを指定 |
| Sheets書き込みエラー | サービスアカウントのメールアドレスが対象シートに編集権限で共有されているか確認 |
| ポート使用中エラー | `--port 3002` 等で別ポートを指定 |
| ブラウザが固まった | UIの「強制キャンセル」を使う（スキップとして記録され、DB・Sheetsの二重更新は起きない） |
| 二重送信が疑われる | DBの `submission_targets` が正本。`data/backups/` に移行前スナップショットあり |

## 不合格時の対応

- 送信完了件数とSheets反映件数が一致しない場合は、送信を止めてDB（`submission_attempts`）とSheetsを突き合わせ、差分をユーザーに報告する
