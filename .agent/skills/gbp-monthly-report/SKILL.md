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

## レポート作成フロー（必須手順）

> 📌 **着手前に必ず読む**: [`references/file-naming-and-preflight.md`](references/file-naming-and-preflight.md)（作成前チェックリスト・CSV/HTML/PDF命名規則・保管場所・顧客正式名ルール）
> 📌 **スクリプトの実行・修正前に必ず読む**: [`references/report-generation-rules.md`](references/report-generation-rules.md)（絶対ルールR1〜R7: 競合ベンチマーク・業種閾値・前月継承・文字コード・CLIプロンプト完全一致）

| STEP | 作業内容 | 備考 |
|------|---------|------|
| 1 | **前月のHTMLを複製する** | コメント・ベンチマーク・構造すべて引き継がれる |
| 2 | **スプレッドシートからKPI数値を取得して更新** | 閲覧数・電話・ルート検索・Webクリック |
| 3 | **ベンチマーク（競合）の評価点数・口コミ数をGoogleマップから確認して更新** | ⚠️ 取得失敗・確認不能の場合は前月値を引き継ぎ、**必ずその旨を報告すること** |
| 4 | **担当者コメントを確認・必要に応じて更新** | 前月コメントを起点に修正する |
| 5 | **HTML → PDF変換** | |
| 6 | **`gbp-report-quality-check` でKPI数値を突合チェック** | 必須 |

> ⚠️ **ベンチマーク取得失敗時のルール**
> - データが取得できなかった場合は **前月値をそのまま引き継ぐ**（ゼロや空欄にしない）
> - 前月HTMLをコピーして作成しているため、前月値は元から入っている
> - 取得できなかった店舗名と理由をユーザーに必ず報告し、手動確認を促す

---

## コマンド実行例

### スプレッドシート連携版（推奨）

```bash
node generate_report_from_sheet.js --url "スプレッドシートの共有URL" --month 4
```

### ローカルCSV版

```bash
# Step 1: HTML生成
node generate_monthly_report.js --csv "%USERPROFILE%\gbp-clients\_report-templates\{name}_2026.csv" --month 3

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

- **HTML/PDF**: `{ホームフォルダ}\gbp-clients\_monthly-reports\{顧客正式名}_月次レポート_{年}年{月}月.html/pdf`
- **テンプレートCSV**: `{ホームフォルダ}\gbp-clients\_report-templates\{クライアント名}_{年}.csv`

> ⚠️ 2026-07: 保存先を `gbp-meo-core/reports|templates` から移動（skills/配下へのクライアント成果物保存禁止ルールに対応）。スクリプトのデフォルト出力先も変更済み。

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
- 2026-05-07: レポート作成フローを明文化。ベンチマーク確認をSTEP 3として必須化。取得失敗時は前月値引き継ぎ＋報告のルールを追記。
- 2026-07-07: 出力先を `gbp-clients\_monthly-reports`・テンプレートを `gbp-clients\_report-templates` へ移動し全スクリプトのパスを更新。旧 gbp-meo-core の絶対ルールR1〜R7を `references/report-generation-rules.md` として移管。

## NGパターン（NG_RULES棚卸しにより移管・このスキル実行時は必読）

| ID | When（いつ） | What（何をする/しないか） | How to verify（検証方法） |
|---|---|---|---|
| B-01 | グラフ描画で数値カラムを変換する時 | **カンマ付き文字列（例: "1,234"）を parseInt/parseFloat に直接渡さない。** ※batch_report.js / batch_two.js / generate_report_from_sheet.js に `replace(/,/g,'')` 実装済み。該当処理を削除してはならない。 | 生成HTMLのグラフ数値が元データと一致することを照合する。 |
| B-02 | レポートをバッチ再生成する時 | **人間が書いたカスタムコメンタリー（手動編集済みセクション）を上書きしない。** 再生成対象はデータセクションのみに限定する。 | 再生成前後のファイルを diff し、コメンタリーセクションに変更がないことを確認する。 |
| B-03 | 口コミ評価（星）を記載する時 | **レポート生成時点の最新データを使う。** 過去レポートからコピペした近似値を使わない。 | 出力された評価値を Google Maps の実際の表示と照合する。 |
