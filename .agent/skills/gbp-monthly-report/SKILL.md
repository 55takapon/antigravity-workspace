---
name: GBP月次レポート自動生成
description: クライアント向けGBP月次パフォーマンスレポートをNode.jsスクリプトで自動生成するスキル。Google SheetsのCSVデータを読み込み、KPI計算・競合比較・推奨アクションを含むHTML/PDFレポートを一括生成。スプレッドシート連携版（generate_report_from_sheet.js）とローカルCSV版（generate_monthly_report.js）の2モードを搭載。
---

# GBP月次レポート自動生成スキル

> **目的**: クライアントのGBPパフォーマンスデータを月次で集計し、営業品質のHTML/PDFレポートを自動生成する  
> **前提**: コアスキル（`gbp-meo-core/SKILL.md`）の知識があること  
> **QC**: 生成後は必ず `gbp-report-quality-check` スキルで検証すること

---

## スクリプト構成

```
gbp-monthly-report/
├── generate_monthly_report.js      ← ローカルCSV版 メインスクリプト
├── generate_report_from_sheet.js   ← スプレッドシート連携版 メインスクリプト
├── parse_csv.js                    ← CSVパーサー・データ構造
├── calculate_kpis.js               ← KPI計算・推奨アクション生成ロジック
├── render_html.js                  ← HTMLテンプレート・セクション構成
├── client_registry.js              ← クライアント管理レジストリ
├── scrape_competitors.js           ← 競合データ自動スクレイピング
└── batch_report.js                 ← 複数クライアント一括実行
```

---

## 実行フロー

### スプレッドシート連携版（推奨）

```bash
node generate_report_from_sheet.js --url "スプレッドシートの共有URL" --month 4
```

### ローカルCSV版

```bash
# Step 1: HTML生成
node generate_monthly_report.js --csv "../gbp-meo-core/templates/{name}_2026.csv" --month 3

# Step 2: 個別メッセージ確認後、PDF出力
node generate_monthly_report.js --csv "..." --month 3 --message "個別メッセージ"
```

---

## CLI引数一覧

| 引数 | スクリプト | 必須 | 説明 |
|------|-----------|------|------|
| `--csv` | generate_monthly_report | ✅ | ローカルCSVパス |
| `--url` | generate_report_from_sheet | ✅ | スプレッドシート共有URL |
| `--month` | 両方 | ✅ | 対象月（1-12） |
| `--output` | 両方 | | 出力ディレクトリ |
| `--message` | 両方 | | 個別メッセージ（PDF末尾に追記） |

---

## 出力先・命名規則

- **HTML/PDF**: `gbp-meo-core/reports/{顧客正式名}_月次レポート_{年}年{月}月.html/pdf`
- **テンプレートCSV**: `gbp-meo-core/templates/{クライアント名}_{年}.csv`

> ⚠️ 命名規則の詳細は `gbp-diagnostic/SKILL.md` セクション11.2 を参照

---

## テキスト編集先

| 変更内容 | ファイル |
|----------|----------|
| セクション見出し・レイアウト・色 | `render_html.js` |
| KPIカードのラベル | `calculate_kpis.js` |
| 推奨アクションの文面・判定条件 | `calculate_kpis.js`（92-153行目） |
| CSVの読み取り項目 | `parse_csv.js` |
| クライアント一覧 | `client_registry.js` |

---

## 連携スキル

- `gbp-meo-core` → 戦略・ベンチマーク・KPIの基準
- `gbp-diagnostic` → 月次レポート作業手順（Section 0.2）
- `gbp-report-quality-check` → 生成後の品質検証（必須）

---

## 変更履歴

- 2026-05-03: `gbp-meo-core/monthly-report/` から独立スキルとして分離。SKILL.md新規作成。
