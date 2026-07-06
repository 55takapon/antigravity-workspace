# ファイル命名規則・保管場所

> このルールに従わないファイル出力は絶対に行わない。

## 保管場所

成果物は全て `C:\Users\hangy\gbp-clients\{クライアント名}\` 配下に出力する。

- **スキルディレクトリ（gbp-diagnostic/）配下への成果物出力は禁止**
- クライアントごとにサブフォルダを1つ作る（例: `C:\Users\hangy\gbp-clients\meet_dental\`）
- スクリプトで出力先を組み立てる場合はホームディレクトリ基準（`os.homedir()` 等）で解決し、絶対パスをハードコードしない

## 診断レポートファイルの命名規則

| ファイル種類 | 命名規則 | 例 |
|-------------|---------|---|
| HTMLレポート（PDF化用） | `diagnostic_report_{クライアント名}_{YYYYMMDD}.html` | `diagnostic_report_meet_dental_20260329.html` |
| PDFレポート | `diagnostic_report_{クライアント名}_{YYYYMMDD}.pdf` | `diagnostic_report_meet_dental_20260329.pdf` |
| NotebookLMテキスト | `diagnostic_report_{クライアント名}_{YYYYMMDD}_notebook.txt` | `diagnostic_report_meet_dental_20260329_notebook.txt` |
| 営業トーク稿 | `diagnostic_sales_pitch_{クライアント名}_{YYYYMMDD}.txt` | `diagnostic_sales_pitch_meet_dental_20260329.txt` |
| 診断データJSON | `diagnostic_data_{クライアント名}_{YYYYMMDD}.json` | `diagnostic_data_meet_dental_20260329.json` |

## クライアント名のルール

- **形式**: `{名称}_{業種コード}`（半角英数小文字＋アンダースコア）
- 30〜50社規模を見据え、ファイル名から業種を判別できるようにする
- 法人格（医療法人社団等）は省略し、識別しやすい短い名称にする
- 日本語は使わない

### 業種コード一覧

| 業種コード | 業種 | 例 |
|---|---|---|
| `dental` | 歯科 | `meet_dental`, `kamada_dental` |
| `dentalkamiawase` | 歯科（噛み合わせ） | `koukenbi_dentalkamiawase` |
| `izakaya` | 居酒屋 | `iami_izakaya` |
| `okonomiyaki` | お好み焼き | `michi_okonomiyaki` |
| `cafe` | カフェ | `harenohi_cafe` |
| `legal` | 士業（税理士・司法書士等） | `sakakibara_legal` |
| `juku` | 学習塾 | `eiwa_juku` |
| `web` | Web集客 | `jetproduce_web` |
| `petsitter` | ペットシッター | `nyanpon_petsitter` |
| `beauty` | 美容室・エステ | — |
| `seitai` | 整体・施術院 | — |
| `realestate` | 不動産 | — |
| `reform` | 工務店・リフォーム | — |
| `retail` | 小売・物販 | — |

新規業種の場合は上記の形式（短い英語小文字）で新コードを追加し、この表を更新すること。

## 日付のルール

- 形式は `YYYYMMDD`（ハイフンなし・8桁）
- **必ずJST（日本時間）基準で生成する**。`new Date().toISOString()` はUTCのため、
  15:00〜24:00 JSTの作業で日付が1日ズレる。スクリプトでは必ずJST変換を通すこと

## 禁止パターン

```
❌ スキルディレクトリ（gbp-diagnostic/）直下・output/ サブフォルダへの出力
❌ diagnostic_shibamoto_20260329.html （diagnostic_report_ プレフィックスなし）
❌ diagnostic_report_shibamoto_2026-03-29.html （日付にハイフン使用）
❌ diagnostic_report_芝本_20260330.html （日本語ファイル名）
✅ C:\Users\hangy\gbp-clients\shibamoto_legal\diagnostic_report_shibamoto_legal_20260330.html
```
