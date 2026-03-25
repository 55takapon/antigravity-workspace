# Workspace 自動同期システム

このフォルダの変更を自動的に検知して GitHub へプッシュするための設定です。

## セットアップ手順

### 1. Git の初期設定（未完了の場合）
ターミナルで以下のコマンドを実行し、あなたの情報を登録してください：
```powershell
git config --global user.name "あなたの名前"
git config --global user.email "あなたのメールアドレス"
```

### 2. GitHub リポジトリの作成と接続
1. GitHub で新しいリポジトリを作成します。
2. 以下のコマンドでリモートリポジトリを接続します：
   ```powershell
   git remote add origin https://github.com/ユーザー名/リポジトリ名.git
   ```

### 3. 自動同期スクリプトの実行
`sync-github.ps1` を実行すると、5分ごとに変更をチェックして自動的にコミット＆プッシュします。
```powershell
.\sync-github.ps1
```

> [!TIP]
> スクリプトをバックグラウンドで実行し続けたい場合は、専用のターミナルを開いておくか、Windows タスクスケジューラに登録することを推奨します。
