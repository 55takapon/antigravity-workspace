# Web会社分類ルール運用メモ

目的: Web制作会社とWebマーケティング会社を、サイト本文から低コストに自動仕訳する。

## ファイル

- ルール定義: `small-company-research/rules/web_company_classification_rules.json`
- 判定スクリプト: `small-company-research/scripts/classify_web_company_sites.py`

## 分類

- `web_production`: Web制作会社
- `web_marketing`: Webマーケティング会社
- `hybrid`: 制作・マーケの両方が強い、または差が小さい
- `unknown`: 情報不足、またはどちらのスコアも低い

## 基本方針

- LLMには本文全文を投げない。
- サイトを最大4ページだけ取得する。
- title、meta description、h1、h2、nav、link text、bodyを抽出する。
- キーワード辞書で制作スコアとマーケスコアを出す。
- 差が大きいものだけ自動分類し、差が小さいものは`hybrid`にする。

## MEO/GBPの扱い

以下が明確に出ている場合は、マーケティング側に強く加点する。

- `MEO`
- `MEO対策`
- `Googleビジネスプロフィール`
- `Google Business Profile`
- `GBP`
- `Googleマップ集客`

## 実行例

```powershell
python small-company-research/scripts/classify_web_company_sites.py `
  --input csv_book2_1266092372_after_sort.csv `
  --output web_company_classification_result.csv `
  --company-column 企業名 `
  --url-column URL
```

先頭10件だけ試す場合:

```powershell
python small-company-research/scripts/classify_web_company_sites.py `
  --input csv_book2_1266092372_after_sort.csv `
  --output web_company_classification_sample.csv `
  --company-column 企業名 `
  --url-column URL `
  --limit 10
```

## 出力列

- `classification`: 分類結果
- `confidence`: 確信度
- `production_score`: 制作スコア
- `marketing_score`: マーケスコア
- `production_keywords`: 制作側の根拠キーワード
- `marketing_keywords`: マーケ側の根拠キーワード
- `source_pages`: 判定に使ったページ
- `fetch_status`: 取得状態

## 更新方法

分類がずれる場合は、まず`web_company_classification_rules.json`を更新する。

- キーワード追加: `categories.web_production.terms` または `categories.web_marketing.terms`
- 強いキーワード追加: `strong_terms`
- 判定を慎重にしたい: `thresholds.medium_confidence_gap`や`thresholds.high_confidence_gap`を上げる
- 取得ページ数を増やす: `fetch.max_pages_per_site`を上げる

運用上は、`hybrid`と`unknown`だけを目視確認し、必要なキーワードをルールに戻すと精度が上がる。
