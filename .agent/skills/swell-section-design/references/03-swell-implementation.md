# SWELL実装規則と移植パターン

## 何をするか

確定した型とトークンから、SWELL貼付用HTML/CSSとプレビューHTML、貼付手順を生成する。

移植元: 旧ツール `3col-design-tool/index.html`（.cursor\test 配下、2026年7月に廃棄）。
SWELL実装手順・スコープ設計・ブレークポイントと下記の実CSSパターンは同ツールから移植した実物。
色・サイズの固定値はそのまま使わず、必ずステップ3で検証済みのトークンへ置き換える。

## スコープ規則

- 案件ごとの名前空間クラスでルート要素を包む。命名は `jp-sec-[セクション名]`（例: `.jp-sec-service`）
- CSSセレクタは必ず `.jp-sec-service .クラス名` 形式で書き、素のタグセレクタ・汎用クラス単独指定を出さない
- `!important` は使わない。SWELL側と競合したら詳細度（ルートクラスの重ねがけ）で解決する
- 色・余白はルート要素のCSSカスタムプロパティで一元化する（検証済みトークンの反映先を1箇所にするため）

```css
.jp-sec-service {
  --mc: #1e3a5f;      /* プライマリ（検証済みトークンで置換） */
  --ac: #c8a96e;      /* アクセント（CTA・強調のみ） */
  --bg: #ffffff;      /* ベース */
  --tx: #1f2a37;      /* テキスト（--bgとの比率検証済みであること） */
  --tx2: rgba(31,42,55,0.72); /* 補助テキスト */
  --line: rgba(31,42,55,0.24); /* 罫線 */
}
```

## ブレークポイント（SWELL準拠・変更禁止）

| 幅 | 扱い |
|:---|:---|
| 〜959px | タブレット。3列は2列または1列へ。gapを20px前後に縮める |
| 〜599px | スマホ。原則1列。写真高さを縮める |

## SWELL貼付手順の書き方（成果物に必ず添える）

貼付方式は2つ。生成コードに合わせてどちらかを明記する。

- **A. カスタムHTMLブロック方式**（HTML構造が独自の型: ステップ型・主役1+補助2・写真主役など）
  1. 投稿/固定ページ編集でカスタムHTMLブロックを挿入し、HTMLを貼る
  2. 「外観 → カスタマイズ → 追加CSS」へCSSを貼る
  3. 実テキスト・写真URLへの差し替え箇所を列挙する
- **B. カラムブロック+追加CSS方式**（SWELL標準ブロックで組める型のみ）
  1. カラムブロック（1/3×3列等）を挿入し、各カラムに見出し・段落・画像を配置
  2. ブロックの「追加CSSクラス」へ名前空間クラスを設定
  3. 追加CSSを貼る

難易度目安も添える: **easy**（追加CSS20行以内・ブロック標準機能中心）/ **mid**（カスタムHTML＋擬似要素）/ **hard**（重なり・clip-path等、崩れたときの調整知識が必要）。

## 移植パターン（実CSS・トークン置換して使う）

### P1. ファインライン罫線（罫線編集リスト型・造形差つき3カラムの基礎）— easy

余白と罫線1本だけで品格を出す。影・角丸と併用しない。高単価・上質トーン向き。

```css
.jp-sec-x .col { padding-top: 28px; border-top: 1px solid var(--mc); }
.jp-sec-x { display: grid; grid-template-columns: repeat(3, 1fr); gap: 48px; }
/* 959px: 2列 gap20px / 599px: 1列 */
```

### P2. 背景ナンバー（ステップ型・造形ルール「番号」）— easy

透過6%の大数字を背景に敷き、番号を視覚の主役にする。SEOに影響しない装飾テキスト。

```css
.jp-sec-x .bg-num {
  position: absolute; top: -12px; right: 8px;
  font-size: 8rem; font-weight: 900;
  color: var(--mc); opacity: 0.06;
  line-height: 1; letter-spacing: -0.04em;
  pointer-events: none; user-select: none;
}
.jp-sec-x .col { position: relative; overflow: hidden; }
```

### P3. カード+出現アンダーライン（造形差つき3カラム）— easy

ホバーで2pxのアクセント線が伸びる。動きは1種類だけに絞る。

```css
.jp-sec-x .line { height: 2px; width: 0; background: var(--ac); transition: width 0.3s; }
.jp-sec-x .col:hover .line { width: 40px; }
```

### P4. 写真フェード合流（写真主役バナー型）— mid

写真下部をベース色グラデーションで溶かし、本文と融合させる。写真の主要被写体は上半分に収める。

```css
.jp-sec-x .photo { height: 200px; background-size: cover; background-position: center; position: relative; }
.jp-sec-x .photo::after {
  content: ''; position: absolute; inset: auto 0 0 0; height: 55%;
  background: linear-gradient(to bottom, transparent, var(--bg));
}
.jp-sec-x .body { margin-top: -10px; position: relative; z-index: 1; }
```

### P5. オーバーラップカード（写真主役バナー型・主役1+補助2の主役側）— hard

本文カードが写真に24px被さり立体感を作る。`margin-top: -24px` が重なり量。

```css
.jp-sec-x .card {
  position: relative; margin: -24px 10px 0;
  background: var(--bg); border-radius: 10px;
  padding: 22px 22px 26px;
  box-shadow: 0 6px 32px rgba(0,0,0,0.13);
}
```

## プレビューHTMLの生成規則

- 保存先は案件プロジェクトフォルダ、なければ scratch 配下の作業フォルダ。スキルフォルダ直下・カレント直下へ確認なしに作らない
- プレビューは実際に貼るHTML/CSSをそのまま読み込み、959px/599pxで崩れを確認できる素の1ファイルにする
- プレビュー専用の装飾（ダーク背景・ガラス風UIなど成果物と無関係な飾り）を加えない

## 確認方法

- 全セレクタが名前空間クラス配下にあること
- 固定色がカスタムプロパティ経由になっていること（写真URLを除く）
- 959px/599pxのメディアクエリが含まれていること
- 貼付手順と難易度が成果物に含まれていること

## 不合格時の対応

- スコープ漏れ・固定色が見つかったら、出力前に修正する（そのまま納品してはならない）
- SWELL実機で崩れた場合は、`!important` ではなくルートクラスの重ねがけで詳細度を上げて解決する
