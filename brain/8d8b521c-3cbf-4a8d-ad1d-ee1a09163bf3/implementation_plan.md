# Zoom to YouTube Automation Tool

このツールは、Zoomのクラウドレコーディングを自動的に取得し、YouTubeチャンネルに「限定公開」でアップロードするためのPythonスクリプト群です。

## User Review Required

> [!IMPORTANT]
> **API認証情報の準備が必要です**
> このツールを使用するには、ユーザー自身で以下のAPI設定を行い、認証情報を取得する必要があります。
> 1. **Zoom App Marketplace**: Server-to-Server OAuthアプリを作成し、Account ID, Client ID, Client Secretを取得。
> 2. **Google Cloud Console**: YouTube Data API v3を有効化し、OAuth 2.0クライアントIDを作成して `client_secret.json` を取得。

## Proposed Changes

### Project Structure
新しく `zoom_to_youtube` ディレクトリを作成し、以下の構成で開発します。

#### [NEW] [main.py](file:///C:/Users/hangy/.gemini/antigravity/scratch/zoom_to_youtube/main.py)
- メインの実行スクリプト。
- Zoomから録画リストを取得 -> ダウンロード -> YouTubeへアップロードのフローを制御。

#### [NEW] [zoom_manager.py](file:///C:/Users/hangy/.gemini/antigravity/scratch/zoom_to_youtube/zoom_manager.py)
- Zoom APIとの通信を担当。
- Server-to-Server OAuth認証の実装。
- レコーディング一覧の取得と動画ファイルのダウンロード機能。

#### [NEW] [youtube_manager.py](file:///C:/Users/hangy/.gemini/antigravity/scratch/zoom_to_youtube/youtube_manager.py)
- YouTube Data APIとの通信を担当。
- Google OAuth認証フロー（初回実行時にブラウザで認証）。
- 動画のアップロード機能（`privacyStatus: unlisted` を指定）。

#### [NEW] [config.py](file:///C:/Users/hangy/.gemini/antigravity/scratch/zoom_to_youtube/config.py)
- 環境変数（`.env`）から設定を読み込む。

#### [NEW] [requirements.txt](file:///C:/Users/hangy/.gemini/antigravity/scratch/zoom_to_youtube/requirements.txt)
- 必要なライブラリ: `requests`, `google-auth-oauthlib`, `google-api-python-client`, `python-dotenv` 等。

## Verification Plan

### Automated Tests
- APIキーが存在しない環境では完全なE2Eテストはできないため、モックを使用した単体テスト、またはドライラン機能を実装して動作確認を行います。

### Manual Verification
1. ユーザーに `client_secret.json` と `.env` ファイルを設定してもらう。
2. スクリプトを実行し、以下の動作を確認する。
    - Zoomから録画データがダウンロードされること。
    - YouTubeへのアップロードが開始されること。
    - アップロードされた動画が「限定公開」になっていること。
