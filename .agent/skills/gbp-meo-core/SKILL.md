---
name: gbp-meo-core
description: GBP（Googleビジネスプロフィール）のMEO戦略立案・現状分析・改善提案を行う時に必ず使うコアスキル。「MEO対策して」「GBP改善して」「上位表示したい」「競合分析して」等の依頼、および業種別の広告規制確認が必要な投稿・返信・診断作業で参照する。戦略チェックリスト・KPI設計・業種別法規制リファレンスを提供する。投稿文の作成はgbp-meo-post-core、月次レポートはgbp-monthly-report、診断レポートはgbp-diagnosticへ委譲する。
---

> ⚠️ **作業開始前に必ず knowledge/chat_ng_registry/artifacts/NG_RULES.md を読み、Pre-flight Check を実行すること。**

# GBP MEO運用コアスキル

実店舗を持つクライアントのGBP運用について、戦略立案（Plan）→実行（Do）→効果測定（Check）→改善（Act）の判断基準を提供する。作業の実行自体は下記の専用スキルへ必ず委譲すること。

| やりたいこと | 使うスキル |
|---|---|
| 投稿文の作成・改善 | `gbp-meo-post-core`（品質検査は `gbp-post-quality-check`） |
| 月次レポート生成 | `gbp-monthly-report`（絶対ルールR1〜R7は同スキルの references にある） |
| 診断レポート生成 | `gbp-diagnostic` |
| 口コミ分析・返信 | `gbp-review-analysis` / `gbp-review-reply` |

## ⛔ ファイル保存ルール（厳守）

クライアントごとの成果物は必ず `C:\Users\hangy\gbp-clients\{クライアント名}\` に保存すること。`skills/` 配下への成果物保存は禁止（スキル定義とクライアントデータの混在は管理が破綻する）。

## 工程と参照資料

### 1. 現状分析・戦略立案

- GBP健全性チェック: オーナー確認 / NAP正確性 / カテゴリ（メイン1つ＋サブ2〜3個）/ 説明文750文字の活用 / サービス項目 / 写真枚数 / 口コミ返信率 / 営業時間
- 競合分析: 同エリア同業種の上位3社の口コミ数・評価・返信・投稿頻度・写真品質を確認する
- キーワード設計: 「地域名＋業種」をメインに、「地域名＋サービス名」「近くの〇〇」型をサブに設定する
- KGI/KPI設計: KGI=MEO経由の来店数・売上。KPI=表示回数・アクション数（電話/ルート/Web/予約）・口コミ件数と評価・検索順位

この工程では [references/ranking-factors.md](references/ranking-factors.md)（ランキング要因・業種別ベンチマーク）を必ず読むこと。競合分析・完全度スコアリングの詳細手順は [references/practitioner-checklist.md](references/practitioner-checklist.md) を読むこと。

### 2. GBP最適化の実行

- 基本情報: ビジネス名は正式名称のみ（KW詰め込みは停止リスク）。説明文は最初の250文字に重要KWを自然に含める
- 写真: 最低10枚以上・月2〜4枚追加・1200x900px以上。外観/内観/商品/スタッフを揃える
- 投稿: 継続的な投稿（頻度の目安は業種で異なる。gbp-monthly-report の references/report-generation-rules.md R3 の閾値表を正とする）
- 口コミ: 全件返信・テンプレ丸写し禁止・報酬提供やらせは絶対NG
- NAP一貫性: 全ポータルで表記を完全一致させる。Web検索結果のみで判断せず、各ポータルを直接開いて目視確認すること

実行詳細（センチメント分析・リンク戦略・Schema実装・サイテーション）は [references/execution-details.md](references/execution-details.md) をこの工程で読むこと。

**業種別の広告規制（医療・施術院・士業・教育・美容・飲食・不動産・工務店・小売）に該当するクライアントでは、[references/industry-regulations.md](references/industry-regulations.md) を必ず読むこと。**

### 3. 効果測定と改善

- 週次: 表示回数・電話・ルート検索・口コミのトレンド確認
- 月次: レポート作成（`gbp-monthly-report` へ委譲）・営業時間/サービス情報の更新
- 四半期: NAP監査・カテゴリ見直し・構造化データ検証
- 症状別の改善アクション: 表示回数が少ない→カテゴリ/説明文/サービス項目見直し。転換率が低い→写真と説明文改善。口コミが増えない→獲得導線見直し。順位低下→投稿/写真/口コミの活動量強化

### 4. GEO対策（AI検索最適化）

AI Overviews / Gemini / ChatGPT等に引用されるための最適化。GBP完全性＋LocalBusinessスキーマ＋FAQスキーマ＋E-E-A-T強化が核心。詳細は [references/geo-optimization.md](references/geo-optimization.md) をこの工程で読むこと。ツール選定は [references/tools-and-appendix.md](references/tools-and-appendix.md) を必要なら読む。

## 禁止事項

1. ビジネス名へのキーワード詰め込み
2. 実在しない住所・バーチャルオフィスの使用
3. 口コミへの報酬提供・やらせ口コミ・スタッフ投稿
4. 虚偽/誇張情報の掲載・他社写真の無断使用
5. 説明欄・投稿内へのURL/電話番号の直書き
6. 複数店舗を1プロフィールで管理・看板と不一致のビジネス名
7. references/ 内の数値（ベンチマーク・比率等）を出典未確認のままクライアント向け資料へ断言として転記すること
8. クライアント成果物を skills/ 配下へ保存すること

## エッジケース

| 状況 | 対応 |
|:-----|:-----|
| 口コミ機能が突然停止した（塾等） | カテゴリに「学校」系が混入していないか確認（references/industry-regulations.md 教育の項） |
| ベンチマーク数値がスクレイピングで取れない | gbp-monthly-report の3段階フォールバック（R5）に従い前月値を引き継ぎ、必ず報告する |
| 規制業種か判断がつかない | references/industry-regulations.md の対象業種一覧を確認し、該当すれば慎重表現側に倒す |
| クライアントの業種が references に無い | 景品表示法（優良誤認・有利誤認・ステマ規制）だけは全業種共通で必ず確認する |
