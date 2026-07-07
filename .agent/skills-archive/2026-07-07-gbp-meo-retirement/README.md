# 2026-07-07 GBP/MEOスキル整理アーカイブ

> 方針決定の経緯・実施事項の詳細・設計判断の記録は [HISTORY.md](HISTORY.md) を参照。

skill-creator最新品質基準（SKILL.md 2,000トークン以下・references/examples分離・description4要素・スキップ防止パターン）への不適合と、実運用スキル群（gbp-meo-post-core / gbp-post-quality-check / gbp-review-reply / gbp-monthly-report / gbp-diagnostic）との重複を理由に、以下の12スキルを廃止・退避した。

## 廃止した業種別スキル（9本）

gbp-meo-beauty / bodywork / education / legal / medical / real-estate / restaurant / retail / service

- 実態は「スキル（実行手順）」ではなく業種別コンサル資料。工程・完了条件・発火条件が未定義で、他スキルからの参照もなかった。
- KPIベンチマーク・成功事例等の数値は出典未確認のため再利用禁止（新基準「プロ事例は実物確認済みのみ」に不適合）。
- **法規制・カテゴリ落とし穴の部分だけは救出済み** → `skills/gbp-meo-core/references/industry-regulations.md`
- shibamoto-legal の画像生成ルール（gbp-meo-legal セクション12）→ `clients/shibamoto-legal/knowledge.md` へ移管済み。

## 廃止したpost系スキル（3本）

gbp-meo-post-dental-occlusion / gbp-meo-post-dental-preventive / gbp-meo-post-jetproduce

- 「ChatGPTへコピペするプロンプト」形式の旧世代。役割は gbp-meo-post-core（新基準準拠）＋クライアントナレッジに移行済み。
- 移管先:
  - 噛み合わせ特化ルール → `clients/sapporo-occlusion/knowledge.md`（⑱投稿フォーマットルール）
  - 予防歯科特化ルール → `clients/meet-dental/knowledge.md`（投稿フォーマットルール）
  - 自社投稿ルール一式（トーン・固定フッター・30テーマ・信憑性ルール・画像生成ルール） → `clients/jetproduce/knowledge.md`（新規作成）

## 復元方法

該当フォルダを `skills/` 直下へ戻し、skill-management の「現在のスキル一覧」テーブルに行を再追加する。ただし復元よりも、必要な内容を新基準準拠の形で作り直すことを推奨。
