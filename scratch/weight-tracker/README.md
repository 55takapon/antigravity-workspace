# 体重記録

個人利用の体重記録アプリ。スマホ（複数台）とPCの同一アカウントでログインし、体重を記録・閲覧する。

- ビルド: Vite + React 19 + TypeScript
- スタイル: Tailwind CSS + shadcn/ui
- グラフ: Recharts（グラフ画面でのみ動的読み込み）
- データ/認証: Supabase（Postgres + Auth, Magic Link）
- PWA: vite-plugin-pwa（ホーム画面に追加してスタンドアロン起動できる）

## セットアップ

### 1. 依存関係のインストール

```bash
npm install
```

### 2. Supabase プロジェクトを作成する

1. [supabase.com](https://supabase.com) でプロジェクトを新規作成する。作成画面の **Security** セクションは以下のとおりにする
   - **Enable Data API**: ON（`supabase-js` からのアクセスに必須）
   - **Automatically expose new tables**: OFF（新規テーブルを都度手動で公開する運用にする。RLSの付け忘れによる公開事故を防ぐため）
   - **Enable automatic RLS**: ON（新規テーブル作成時に自動でRLSを有効化する安全網）

   「Automatically expose new tables」をOFFにする場合、`0002_weights_rls.sql` 内の `grant` 文（authenticatedロールへの権限付与）を必ず実行すること。ONのまま作成した場合はこの1文は実行してもしなくても影響しない。

2. ダッシュボードの **SQL Editor** を開き、次の2ファイルの内容を**この順番で**貼り付けて実行する
   - [`supabase/migrations/0001_create_weights.sql`](supabase/migrations/0001_create_weights.sql) — `weights` テーブルとインデックスを作成
   - [`supabase/migrations/0002_weights_rls.sql`](supabase/migrations/0002_weights_rls.sql) — RLS（行レベルセキュリティ）を有効化

   RLSを先に有効化せずにアプリを使い始めないこと。他人のデータが見える状態で運用することになる。

3. **Authentication > Providers** で Email（Magic Link）が有効になっていることを確認する（デフォルトで有効）
4. **Authentication > URL Configuration** の Site URL / Redirect URLs に、開発用の `http://localhost:5173` と、本番でデプロイしたURL（例: `https://xxxx.netlify.app`）を追加する。ここに登録していないURLへはマジックリンクのログインが返ってこない

### 3. 環境変数を設定する

`.env.example` をコピーして `.env.local` を作り、Supabaseダッシュボードの **Project Settings > API** から値を埋める。

```bash
cp .env.example .env.local
```

```
VITE_SUPABASE_URL=https://xxxxxxxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOi...
```

`.env.local` はコミットしない（`.gitignore` 済み）。anon key がクライアントに露出するのは設計上想定内で、安全性はRLS側で担保している。

`.env.local` が無い、または値が空の場合はアプリは自動的に**プレビューモード**（Supabase未接続でもブラウザ内のダミーデータで動作確認できるモード）で起動する。ヘッダーに「プレビュー」バッジが出ていればこのモード。

### 4. 起動

```bash
npm run dev
```

## ビルド

```bash
npm run build
```

`tsc -b && vite build` を実行し、`dist/` に出力する。Recharts はグラフ画面専用の別チャンクに分割される。

## Netlify へのデプロイ

1. GitHubにpushし、Netlifyで **Add new site > Import an existing project** からリポジトリを連携する
2. ビルド設定（[`netlify.toml`](netlify.toml) に定義済みなので自動検出される）
   - Build command: `npm run build`
   - Publish directory: `dist`
3. **Site configuration > Environment variables** に `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` を設定する（値は手順2と同じ）
4. SPAのルーティング用リダイレクト（`/* → /index.html`）は [`public/_redirects`](public/_redirects) と `netlify.toml` の両方に設定済みなので追加作業は不要
5. デプロイ後のURLを、Supabase側の **Authentication > URL Configuration** の Redirect URLs に追加する（手順を戻ってセットアップの2-4を参照）

## ディレクトリ構成

```
src/
  components/ui/       shadcn/ui のコンポーネント
  components/layout/   共通レイアウト（AppShell, PlaceholderPanel 等）
  features/auth/       Supabase Auth（Magic Link）
  features/weights/    体重データのCRUD・グラフ用データ変換・フォーム
  pages/               記録 / グラフ / 履歴の3画面
  lib/                 日付処理・定数・env判定など
supabase/migrations/   テーブル定義・RLSポリシーのSQL
```

## 仕様上の定数

`src/lib/constants.ts` に集約している。

- `DAILY_SAMPLE`: 1日に複数回記録があるとき、グラフ用にどちらを採用するか（`'first'` = 最初の記録）
- `MOVING_AVERAGE_DAYS`: グラフの移動平均日数（7日）
- `HISTORY_PAGE_SIZE`: 履歴のページングサイズ（50件）
