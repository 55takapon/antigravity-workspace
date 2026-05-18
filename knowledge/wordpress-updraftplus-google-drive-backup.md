# WordPress月次バックアップ手順

## 目的

WordPressサイトのデータを、UpdraftPlus無料版で月1回自動バックアップし、Google Driveに保存する。

この手順は、Xserver上のWordPressサイトを想定しています。

## 採用する方法

- プラグイン: UpdraftPlus 無料版
- 保存先: Google Drive
- 実行頻度: 月1回
- 保存世代: 3世代
- All-in-One WP Migration: 削除せず、手動移行・緊急時の丸ごとバックアップ用として残す

## 事前準備

### Googleアカウントを用意する

普段使いのGoogleアカウントでも利用できますが、可能であればバックアップ専用アカウントを用意します。

例:

```txt
example.backup@gmail.com
```

Google Driveの無料容量は通常15GBです。サイト内の画像やPDFが多い場合は、容量不足に注意してください。

## 設定手順

### 1. UpdraftPlusをインストールする

WordPress管理画面にログインします。

```txt
プラグイン > 新規追加
```

検索欄で以下を検索します。

```txt
UpdraftPlus
```

「UpdraftPlus WordPress Backup Plugin」をインストールし、有効化します。

### 2. UpdraftPlusの設定画面を開く

WordPress管理画面で、以下のいずれかを開きます。

```txt
設定 > UpdraftPlus バックアップ
```

または

```txt
UpdraftPlus > 設定
```

### 3. バックアップ頻度を月1回にする

「設定」タブで、以下のように設定します。

```txt
ファイルバックアップのスケジュール: 毎月
データベースバックアップのスケジュール: 毎月
保持するバックアップ数: 3
```

3世代にしておくと、直近3か月分のバックアップを残せます。

### 4. 保存先にGoogle Driveを選ぶ

「保存先を選択」または「Choose your remote storage」で、以下を選択します。

```txt
Google Drive
```

その後、画面下部の「変更を保存」をクリックします。

### 5. Google Driveと連携する

「変更を保存」後、Google認証用のリンクが表示されます。

以下の流れで連携します。

```txt
Google認証リンクをクリック
↓
バックアップ保存用のGoogleアカウントを選択
↓
UpdraftPlusへのアクセスを許可
↓
WordPressに戻る
↓
Complete setup / セットアップ完了 をクリック
```

ここまで完了すると、WordPressとGoogle Driveが接続されます。

### 6. バックアップ対象を確認する

通常は初期設定のままで問題ありません。

バックアップ対象は以下です。

```txt
データベース
プラグイン
テーマ
アップロード
その他 wp-content 内のファイル
```

## 初回テスト

設定後、必ず手動で1回バックアップを実行します。

UpdraftPlusの「バックアップ / 復元」タブで、以下をクリックします。

```txt
今すぐバックアップ
```

チェック項目は以下をONにします。

```txt
データベースをバックアップに含める
ファイルをバックアップに含める
リモートストレージに送信する
```

実行後、Google Driveにバックアップファイルが作成されているか確認します。

## Google Drive側で確認するファイル

Google Drive内にUpdraftPlus用のフォルダが作成されます。

中に以下のようなファイルがあれば成功です。

```txt
backup_日付_サイト名_db.gz
backup_日付_サイト名_plugins.zip
backup_日付_サイト名_themes.zip
backup_日付_サイト名_uploads.zip
backup_日付_サイト名_others.zip
```

## 運用ルール

- 月1回の自動バックアップはUpdraftPlusに任せる
- Google Driveには3世代分を残す
- 3か月に1回、Google Driveにバックアップが残っているか確認する
- WordPress本体、テーマ、プラグインの大きな更新前は、手動で「今すぐバックアップ」を実行する
- All-in-One WP Migrationは、サイト移行や手動の丸ごとバックアップ用として残す

## 注意点

### Google Driveの容量不足

バックアップ容量がGoogle Driveの空き容量を超えると、保存に失敗する可能性があります。

画像やPDFが多いサイトでは、定期的にGoogle Driveの容量を確認してください。

### バックアップは復元できて初めて意味がある

可能であれば、別のテスト環境で復元確認を行うのが理想です。

最低限、Google Drive上にバックアップファイルが生成されていることは定期的に確認します。

### Xserverの自動バックアップは保険として扱う

Xserverにも自動バックアップ機能がありますが、長期保管用ではありません。

月次でGoogle Driveに保存するバックアップを、メインの保管先として扱います。

## 参考

- UpdraftPlus公式: スケジュールバックアップ
  - https://teamupdraft.com/documentation/updraftplus/topics/backing-up/faqs/how-do-i-schedule-backups-for-my-files-and-databases/
- UpdraftPlus公式: 保存先
  - https://teamupdraft.com/documentation/updraftplus/topics/backing-up/faqs/where-are-my-updraftplus-backups-stored/
- Xserver公式: 自動バックアップ
  - https://www.xserver.ne.jp/functions/
