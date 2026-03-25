# GitHub 連携と自動同期システムの構築プラン

ユーザーの作業フォルダ（Workspace）を GitHub と連携させ、履歴管理と自動更新（継続的な同期）を実現します。

## ユーザー確認事項
> [!IMPORTANT]
> GitHub CLI (`gh`) がインストールされていないため、標準の Git コマンドを使用するか、`gh` のインストールを推奨します。本プランでは基本的な Git 連携と、PowerShell による自動同期スクリプトの作成を提案します。
> 以下の手順で GitHub との認証（SSH または HTTPS + PAT）が必要になります。

## 提案事項

### [Workspace 初期化]
- `C:\Users\hangy\.gemini\antigravity\scratch` を Git リポジトリとして初期化します。
- 不要なファイル（一時ファイルなど）を除外するための `.gitignore` を追加します。

#### [NEW] [.gitignore](file:///C:/Users/hangy/.gemini/antigravity/scratch/.gitignore)

### [自動同期システム]
- 定期的に変更を検知して `git add`, `git commit`, `git push` を行うスクリプトを作成します。

#### [NEW] [sync-github.ps1](file:///C:/Users/hangy/.gemini/antigravity/scratch/sync-github.ps1)

## 検証プラン

### 自動テスト
- `sync-github.ps1` を実行し、変更がある場合に適切にコミットが作成されるかを確認します。
- `git status` で未追跡のファイルが残っていないか確認します。

### 手動検証
- ユーザーによる GitHub リポジトリの作成と `git remote add origin ...` の実行。
- ユーザーによる初回の認証処理。
- スクリプト実行後、GitHub 上でファイルが更新されているかを確認。
