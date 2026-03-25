# Implementation Plan - Sugimoto Judicial Scrivener Office Website

杉本司法書士事務所のトップページ制作計画です。
「誠実で信頼できそう」というイメージを最優先し、日本のプロのデザイナーが作成したようなクオリティを目指します。

## Theme & Design Concept
*   **キーワード**: 誠実、信頼、プロフェッショナル、安心感
*   **カラーパレット**:
    *   メインカラー: **濃紺 (Deep Navy)** `#0f172a` - 知的で落ち着いた印象
    *   ベースカラー: **白 (White) & 淡いグレー (Light Gray)** `#f8fafc` - 清潔感と読みやすさ
    *   アクセントカラー: **落ち着いたゴールド (Muted Gold)** `#c5a059` - 高品質、品格
*   **タイポグラフィ**:
    *   Google Fontsより「Shippori Mincho (しっぽり明朝)」または「Noto Serif JP」を採用し、美しい日本語表現を実現します。

## Proposed Changes

ディレクトリ: `C:\Users\hangy\.gemini\antigravity\scratch\sugimoto-office`

### 1. HTML Structure (`index.html`)
セマンティックなマークアップを行い、SEOとアクセシビリティを考慮します。

*   **Header**: ロゴ、ナビゲーション、お問い合わせCTA
*   **Hero Section**: ファーストビューで安心感を与えるイメージとキャッチコピー
    *   キャッチコピー案: 「あなたの悩みに、誠実に向き合います。」
*   **About / Philosophy**: 事務所の理念、代表挨拶
*   **Services**: 業務案内（相続、遺言、登記、債務整理など）
*   **News**: お知らせ（更新性を示す）
*   **Access / Contact**: 地図、お問い合わせフォームへの誘導
*   **Footer**: サイトマップ、著作権表示

### 2. CSS Architecture (`css/`)
保守性が高く、予測可能なCSS設計を行います。

*   `css/reset.css`: モダンなリセットCSS (Eric Meyer's reset or similar modern approach)
*   `css/style.css`:
    *   **Variables**: 色、フォント、スペーシングを変数管理
    *   **Base**: 基本スタイル
    *   **Layout**: グリッド、フレックスボックスを用いたレイアウト
    *   **Components**: ボタン、カード、見出しなどの再利用可能なパーツ
    *   **Responsive**: メディアクエリを使用したモバイルファーストまたはデスクトップファーストの適切なレスポンシブ対応

### 3. Assets (`images/`)
AI生成ツールを使用して以下の画像を生成します。
*   ヒーローイメージ（落ち着いた法律事務所の雰囲気、または相談風景）
*   代表司法書士のポートレート風イメージ（誠実そうな日本人男性または女性）
*   アイコンや装飾的な背景素材

## Verification Plan

### Automated Tests
*   現状、静的なHTML/CSSサイトのため、自動テストスクリプトは作成しません。

### Manual Verification
1.  **ブラウザプレビュー**:
    *   Chromeブラウザで `index.html` を開き、表示を確認します。
2.  **レスポンシブチェック**:
    *   デスクトップ (1920px, 1280px)
    *   タブレット (768px)
    *   モバイル (375px)
    *   各サイズでレイアウト崩れがないか、文字サイズが適切かを確認します。
3.  **デザイン品質チェック**:
    *   余白（Whitespace）が適切に取られているか。
    *   フォントの可読性は高いか。
    *   色が意図した印象を与えているか。

## User Review Required
*   色味や雰囲気の方向性について、もし特定の希望があれば指摘してください（現状は上記の「濃紺＋ゴールド」で進めます）。
