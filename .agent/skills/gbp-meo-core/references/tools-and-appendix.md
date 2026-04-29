# ツール・リソース・付録

> **参照元**: gbp-meo-core SKILL.md §10・§11・付録B

---

## 10. GBP新機能チェックリスト（2025-2026）

### 対応すべき新機能
- [ ] **WhatsApp連携**: GBPにWhatsAppリンクを追加し、リアルタイム顧客対応を実現
- [ ] **SNSプロフィール連携**: Instagram/X/Facebook等のリンクをGBPに追加
- [ ] **Ask Maps（AI自動回答）**: AI生成回答の確認・承認フローを確立（※旧Q&A機能は2025年12月に新規投稿廃止済み。Ask MapsはGBP情報+口コミから自動生成される別機能として継続）
- [ ] **予約投稿・一括投稿**: 複数店舗の投稿管理を効率化
- [ ] **クーポン表示機能**: メニュー連携クーポンの設定
- [ ] **Eコマース連携**: 商品表示・直接購入機能の活用
- [ ] **サステナビリティ属性**: 環境への取り組みをプロフィールに表示
- [ ] **アクセシビリティ属性**: バリアフリー対応をプロフィールに表示
- [ ] **検索・マップからの直接編集**: 管理画面ではなく検索/マップから即時編集

---

## 11. ツール・リソース

### 推奨ツール
| カテゴリ | ツール名 | 用途 |
|----------|----------|------|
| 順位計測 | Gyro-n MEO | 順位トラッキング＋インサイト分析 |
| 順位計測 | MEOチェキ | 手軽な順位確認 |
| 順位計測 | LocalFalcon | グリッド型の順位ヒートマップ |
| 一括管理 | Canly / StorePad | 多店舗のGBP一括管理 |
| 口コミ管理 | EmbedSocial | 口コミ収集・表示・分析（LSAレビュー統合対応）|
| 構造化データ | Schema Markup Generator | JSON-LD生成 |
| 検証 | Googleリッチリザルトテスト | 構造化データの検証 |
| 写真 | GeoImgr | 写真へのジオタグ埋め込み |
| AI検索モニタリング | 手動確認/専用ツール | AI OverviewsでのPresence Rate計測 |

### Google公式リソース
- [Googleビジネスプロフィール ヘルプ](https://support.google.com/business)
- [Google検索セントラル - ローカルビジネス](https://developers.google.com/search/docs/appearance/structured-data/local-business)
- [Googleビジネスプロフィール ガイドライン](https://support.google.com/business/answer/3038177)

---

## 付録B: 月次レポート自動生成ツール

### 概要
CSVに蓄積した月次データから、プロフェッショナルなA4 PDFレポートを自動生成する。

### ファイル構成
```
monthly-report/
├── generate_monthly_report.js  ← メインスクリプト（CLI）
├── parse_csv.js                ← CSVパーサー
├── calculate_kpis.js           ← KPI計算・推奨アクション判定
└── render_html.js              ← HTMLテンプレート（デザイン・テキスト全般）

templates/
└── gbp_monthly_report_template.csv  ← 空テンプレート（顧客ごとにコピー）

reports/
└── （生成されたPDF・HTMLがここに出力される）
```

### レポート生成フロー（必ずこの手順に従うこと）

#### Step 1: CSVデータの確認
顧客のCSVファイルに対象月のデータが入力されているか確認する。

#### Step 2: HTML生成（PDF化前の中間ファイル）
```bash
node generate_monthly_report.js --csv "CSVパス" --month 対象月
```

#### Step 3: ★個別メッセージの確認（重要）
**PDF化の前に、必ずユーザーに確認すること：**

> 「個別メッセージはありますか？レポート末尾の『✉️ 担当者より』セクションに追記します。不要であれば空欄でPDF化します。」

- メッセージがある場合 → `--message "テキスト"` 引数を付けて再実行
- HTMLを直接編集する場合 → `reports/` 内の `.html` ファイルの `id="custom-message-section"` を編集

#### Step 4: PDF出力
`--message` 付きで最終実行：
```bash
node generate_monthly_report.js --csv "CSVパス" --month 3 --message "個別メッセージテキスト"
```

### CLI引数一覧

| 引数 | 必須 | 説明 | 例 |
|------|------|------|---|
| `--csv` | ✅ | CSVファイルパス | `"../templates/英和塾_2026.csv"` |
| `--month` | ✅ | 対象月（1-12） | `3` |
| `--output` | | 出力ディレクトリ | `"../reports"` |
| `--message` | | 個別メッセージ | `"来月は投稿を再開しましょう"` |

### テキスト編集先

| 変更内容 | ファイル |
|----------|----------|
| セクション見出し・レイアウト・色 | `render_html.js` |
| KPIカードのラベル | `calculate_kpis.js` |
| 推奨アクションの文面・判定条件 | `calculate_kpis.js`（92-153行目） |
| CSVの読み取り項目 | `parse_csv.js` |

### CSV設定項目
- **目標口コミ数**: CSVヘッダー5行目に `目標口コミ数,30` のように設定。クライアントごとに変更可能。

