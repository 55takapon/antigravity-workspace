---
name: gbp-review-analysis
description: GBP口コミデータの全件抽出・テキスト分析・強み/弱み抽出・HTMLレポート生成スキル。GoogleマップURLを入力→Playwrightで口コミ全件取得→テーマ分類・感情分析→営業用/伴走用レポート出力。/gbp-review-analysis で起動。
---

> ⚠️ **作業開始前に必ず knowledge/chat_ng_registry/artifacts/NG_RULES.md を読み、Pre-flight Check を実行すること。**


# gbp-review-analysis

> GBPの口コミを全件抽出し、テキスト分析で「お客様が何に魅力を感じているか」「どこを改善すべきか」を可視化する。事業成長PDCA材料・競合ベンチマーク分析にも活用。

## 1. 実行フロー

```
【入力】
  GoogleマップURL（1つ）
  ※ または既存の口コミJSONファイル

         ↓

【STEP 1: 口コミデータ取得】 — scrape_reviews.js
  Playwrightで口コミページを開き、全件スクロール取得
  出力: review_data_{クライアント名}_{YYYYMMDD}.json
  所要時間: 約10分/50件

         ↓

【STEP 2: テキスト分析】 — analyze_reviews.js
  評価分布・テーマ分類・感情分析・頻出キーワード・強み弱み抽出
  出力: review_analysis_{クライアント名}_{YYYYMMDD}.json

         ↓

【STEP 3: レポート生成】 — render_review_report.js
  HTML形式の分析レポート（PDF化対応）
  出力: review_report_{クライアント名}_{YYYYMMDD}.html

         ↓

【STEP 4: ベンチマーク分析（オプション）】
  同業他社の口コミも取得・分析し、差別化ポイントを明確化
```

---

## 2. STEP 1: 口コミデータ取得

### 2.1 スクリプト実行

```bash
cd .agent/skills/gbp-review-analysis
node scripts/scrape_reviews.js --url "GoogleマップURL" --name "client_name"
```

### 2.2 取得項目

| フィールド | 説明 |
|-----------|------|
| `name` | 投稿者名 |
| `rating` | 星評価（1-5の数値） |
| `date` | 投稿日（「○か月前」等の相対表記） |
| `text` | 口コミ本文（「もっと見る」展開後の全文） |
| `hasOwnerReply` | オーナー返信の有無 |
| `ownerReplyText` | オーナー返信の本文 |

### 2.3 取得ロジック

1. Playwrightでブラウザ起動（headless）
2. GoogleマップURLを開く → 口コミタブに移動
3. 「新しい順」でソート
4. スクロールで全件ロード（ランダム遅延2-4秒でbot検知回避）
5. 各口コミの「もっと見る」を自動展開
6. データ抽出（名前・星・日付・本文・返信）
7. JSON出力

### 2.4 既存データからの入力

既存のテキストファイルやJSONがある場合、パーサーで統一フォーマットに変換:

```bash
node scripts/parse_review_data.js --input "既存ファイルパス" --format txt
# 対応形式: txt（区切り線区切り）, json（consolidated形式）
```

---

## 3. STEP 2: テキスト分析

### 3.1 スクリプト実行

```bash
node scripts/analyze_reviews.js --input review_data_xxx.json [--benchmark competitor.json] [--industry restaurant]
```

### 3.2 分析項目

| 分析カテゴリ | 内容 |
|-------------|------|
| **評価分布** | 星1〜5の件数・割合・平均・中央値 |
| **テーマ分類** | 口コミ本文を業種別カテゴリに自動分類 |
| **感情分析** | ポジティブ / ネガティブ / 中立 |
| **頻出キーワード** | 肯定的TOP10 / 否定的TOP10 |
| **強み抽出** | 高評価口コミの共通テーマ → 差別化ポイント |
| **弱み・改善点** | 低〜中評価口コミのテーマ → 改善アクション |
| **オーナー返信分析** | 返信率 / テンプレ vs 個別対応 |
| **時系列分析** | 口コミ投稿頻度の推移 |

### 3.3 業種別テーマ分類

| 業種 | 分類カテゴリ |
|------|------------|
| **飲食** | 味・品質 / 接客 / 雰囲気・清潔感 / 価格・コスパ / 立地 / 待ち時間 / メニュー |
| **医療** | 技術・腕 / 説明の丁寧さ / 痛み・不安配慮 / 待ち時間 / 設備 / スタッフ |
| **士業** | 専門性 / 対応速度 / 説明の分かりやすさ / 費用 / 人柄 |
| **美容** | 技術・仕上がり / カウンセリング / 雰囲気 / 価格 / スタッフ |
| **汎用** | 品質 / 接客 / 雰囲気 / 価格 / 立地 / その他 |

詳細な分類辞書は `references/analysis_methodology.md` を参照。

---

## 4. STEP 3: レポート生成

### 4.1 スクリプト実行

```bash
node scripts/render_review_report.js --input review_analysis_xxx.json --business-name "ビジネス名"
```

### 4.2 レポートセクション構成

```
1. エグゼクティブサマリー（3行で結論）
2. 評価分布チャート（テキストベース棒グラフ）
3. 強みTOP3（具体的な口コミ引用付き）
4. 改善ポイントTOP3（具体的な口コミ引用付き）
5. テーマ別分析マトリクス
6. 頻出キーワード（テーブル形式）
7. オーナー返信分析
8. 競合ベンチマーク比較（オプション）
9. 推奨アクションリスト（優先度・想定工数付き）
```

---

## 5. ファイル命名規則・保管場所

> 🚨 このルールに従わないファイル出力は絶対に行わない

| ファイル種類 | 命名規則 | 例 |
|-------------|---------|---|
| 口コミ生データJSON | `review_data_{クライアント名}_{YYYYMMDD}.json` | `review_data_bomnal_chicken_20260504.json` |
| 分析結果JSON | `review_analysis_{クライアント名}_{YYYYMMDD}.json` | `review_analysis_bomnal_chicken_20260504.json` |
| HTMLレポート | `review_report_{クライアント名}_{YYYYMMDD}.html` | `review_report_bomnal_chicken_20260504.html` |
| PDFレポート | `review_report_{クライアント名}_{YYYYMMDD}.pdf` | `review_report_bomnal_chicken_20260504.pdf` |
| 競合ベンチマーク | `review_benchmark_{クライアント名}_{YYYYMMDD}.json` | `review_benchmark_bomnal_chicken_20260504.json` |

**保管場所**: `.agent/skills/gbp-review-analysis/` 直下

**クライアント名**: 半角英数小文字＋アンダースコア。gbp-diagnostic の業種コードに準拠。

---

## 6. NGパターン

| NG | 正しいやり方 |
|----|-------------|
| 口コミ本文に含まれるオーナー返信を口コミテキストに混在させる | `hasOwnerReply` と `ownerReplyText` で分離して保存 |
| 星評価を文字列（"5 stars"）のまま保存 | 数値（5）に変換して保存 |
| 日付を相対表記（"1か月前"）のまま分析に使う | 相対表記はそのまま記録するが、時系列分析では大まかな時期区分（直近3ヶ月/3-6ヶ月/6ヶ月以上）で処理 |
| CSSセレクタのハードコード | セレクタはスクリプト冒頭の設定ブロックに集約。変更しやすくする |

---

## 7. ファイル構成

```
gbp-review-analysis/
├── SKILL.md                           ← このファイル
├── scripts/
│   ├── scrape_reviews.js              ← Playwright口コミ全件抽出
│   ├── analyze_reviews.js             ← テキスト分析エンジン
│   ├── render_review_report.js        ← HTMLレポート生成
│   └── parse_review_data.js           ← 複数形式パーサー
└── references/
    └── analysis_methodology.md        ← 分析手法・テーマ辞書詳細
```

---

## 関連スキル

- **口コミへの返信文作成は本スキルの範囲外。** 抽出・分析（STEP 1〜2）のあとに返信案を作る場合は、必ず `gbp-review-reply` スキル（`.agent/skills/gbp-review-reply/SKILL.md`）を先に読み、スタイル判定・業種別リスク・クライアント別 `profile.md` / `log.md` に従って作成すること。本スキルの流れで返信を自作しないこと。

---

## 変更履歴

- 2026-05-04: 初版作成
- 2026-07-15: 「関連スキル」節を追記（返信作成は gbp-review-reply スキルを使う導線を明示）
