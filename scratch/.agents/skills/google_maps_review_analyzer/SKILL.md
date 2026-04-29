---
name: google_maps_review_analyzer
description: GoogleマップのURLを入力すると、レビュー口コミを自動抽出し、プロマーケター視点で多面的に分析するスキル
---

# Google Maps レビュー口コミ 抽出・分析スキル

## 概要

GoogleマップのURLを受け取り、以下を自動実行する：
1. レビュー口コミの全件抽出（Playwright）
2. プロマーケター・プロアナリスト視点での5セクション分析
3. Markdown + JSONレポートの出力

## 前提条件

- Python 3.10+
- Playwright（`pip install playwright && playwright install chromium`）
- 追加の外部NLPライブラリは不要（日本語キーワード辞書ベース）

## ファイル構成

```
scripts/
├── extract_reviews.py   # レビュー抽出
└── analyze_reviews.py   # レビュー分析
```

---

## 実行手順

### ステップ1: レビュー抽出

ユーザーからGoogleマップのURLを受け取る。以下の形式に対応：
- `https://maps.google.com/maps/place/...`
- `https://www.google.com/maps/place/...`
- `https://maps.app.goo.gl/...`（短縮URL）
- CID付きURL

```powershell
// turbo
python "C:\Users\hangy\.gemini\antigravity\scratch\.agents\skills\google_maps_review_analyzer\scripts\extract_reviews.py" "{GOOGLE_MAPS_URL}" --output reviews.json
```

出力: `reviews.json`（抽出データ）

> [!NOTE]
> Google側のDOM変更でセレクタが動作しない場合、ブラウザツールを使って
> 手動でレビューページを開き、DOMを確認してセレクタを更新する。

### ステップ2: レビュー分析

```powershell
// turbo
python "C:\Users\hangy\.gemini\antigravity\scratch\.agents\skills\google_maps_review_analyzer\scripts\analyze_reviews.py" reviews.json --output review_report.md --json-output review_data.json
```

出力:
- `review_report.md` — Markdownレポート
- `review_data.json` — 構造化分析データ

### ステップ3: レポート提示

生成された `review_report.md` の内容をユーザーに提示する。
必要に応じて追加の深掘り分析を行う。

---

## 分析内容（5セクション）

| # | セクション | データソース | 出力内容 |
|---|-----------|------------|---------|
| 1 | 評価サマリー | ★ + 件数 + 日付 | 平均・分布・時期別傾向 |
| 2 | テキスト分析 | コメント本文 | センチメント・頻出キーワード・トピック分類・顧客像 |
| 3 | 強み・弱み | ★ + コメント統合 | USP・改善点・リピート/推奨意向 |
| 4 | オーナー返信 | 返信テキスト | 返信率・テンプレ度・要対応レビュー |
| 5 | アクションプラン | 全統合 | エグゼクティブサマリー・MEOヒント・返信テンプレ・SNS素材 |

---

## 既存データの分析

抽出済みJSONがある場合はステップ2から直接実行可能。
以下のフォーマットに対応：

```json
// フォーマットA（本スキルの出力）
{"meta": {...}, "reviews": [{"name": "...", "rating": 5, "text": "..."}]}

// フォーマットB（既存の店舗名キー形式）
{"store_name": [{"name": "...", "rating": "5 stars", "text": "..."}]}

// フォーマットC（単純リスト）
[{"name": "...", "rating": 5, "text": "..."}]
```

---

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| レビューが0件 | Googleの構造変更の可能性。ブラウザツールで実ページのDOMを確認 |
| CAPTCHAで止まる | headless=Falseに変更してリトライ。または時間をおいて再実行 |
| 文字化け | encoding="utf-8" を確認 |
