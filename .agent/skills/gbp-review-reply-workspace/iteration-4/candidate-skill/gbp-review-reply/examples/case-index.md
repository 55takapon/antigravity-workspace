# 良好全文例インデックス

このindexには、ユーザー確認済みの全文例26件だけを登録する。G06-RPは返信済み生成停止の工程制御であり、全文例数に含めない。状態は通常生成で参照できる`confirmed-good`または、条件付き提案中の`active-conditional-proposed`に限定する。

## router

| カテゴリ | 選択条件 | ファイル | 収録数 |
|:---|:---|:---|---:|
| star-only | 本文なし | [cases/star-only.md](cases/star-only.md) | 5 |
| positive-short | 短い肯定本文 | [cases/positive-short.md](cases/positive-short.md) | 2 |
| positive-detailed | 情報量の多い肯定本文 | [cases/positive-detailed.md](cases/positive-detailed.md) | 5 |
| mixed-low-rating | 肯定と不満の混合、または低評価 | [cases/mixed-low-rating.md](cases/mixed-low-rating.md) | 7 |
| high-risk-special | 医療・施術、士業、BtoB、外国語、事実争い等 | [cases/high-risk-special.md](cases/high-risk-special.md) | 7 |

カテゴリ決定後、評価帯、本文量、業種、論点、risk、profile条件が近いIDを最大2〜3件だけ読む。複数ファイルの総当たりと26件全読込を禁止する。

## ID一覧

| ID | 状態 | 主な条件 |
|:---|:---|:---|
| W13-SH | confirmed-good | 一般サービス、星5、本文なし |
| W14-SF | confirmed-good | 飲食、星5、本文なし |
| W15-SC | confirmed-good | 医療、星5、本文なし |
| W16-SL | confirmed-good | 一般サービス、星1、本文なし |
| W17-SO | confirmed-good | 整骨院、星1、本文なし |
| C02-UR04 | confirmed-good | 飲食、雰囲気とスタッフ対応 |
| C03-UR05 | confirmed-good | 飲食、料理と接客 |
| C01-A35 | active-conditional-proposed | 飲食、詳細高評価。posted事実は保持。本番前にユーザー確認必要 |
| W01-HF | confirmed-good | 飲食、料理・雰囲気・再訪意思 |
| W02-HB | confirmed-good | 美容、仕上がり・カウンセリング |
| W03-HS | confirmed-good | 飲食、接客・料理・友人との時間 |
| G07-KL | confirmed-good | 飲食、knowledge販促漏入防止 |
| W04-LW | confirmed-good | 予約後の長時間待ち・説明不足 |
| W05-LA | confirmed-good | スタッフ対応への不満 |
| W06-LB | confirmed-good | 美容、仕上がり・カウンセリング不満 |
| W07-LF | confirmed-good | 飲食、味・量・価格への不満 |
| W08-LP | confirmed-good | 価格と内容の比較評価 |
| W09-LH | confirmed-good | 衛生上の指摘 |
| G01-MX | confirmed-good | 飲食、肯定と軽い不満の混合 |
| W10-HD | confirmed-good | 歯科、説明への高評価 |
| W11-HO | confirmed-good | 整骨院、効果の自己申告 |
| W12-HC | confirmed-good | クリニック、スタッフ対応 |
| G02-B2B | confirmed-good | BtoB、公開範囲を絞る高評価 |
| G03-FL | confirmed-good | 外国語、接客への低評価 |
| G04-DP | confirmed-good | 事実関係が未確認の低評価 |
| G05-MP | confirmed-good | 医療、診療情報を含む高評価 |

## 工程制御

### G06-RP — 返信済みレビュー

- 状態: `eval-only-workflow-control`
- 条件: 店舗返信がすでに投稿済みで、修正・追記依頼がない。
- 対応: `返信済みのため、新しい返信案は作成しません。`
- 禁止: 二重投稿案、既存返信の無断上書き、代替案の量産。

## 状態ガバナンス

- `candidate`をユーザー確認なしに`confirmed-good`または`active`へ昇格しない。
- `active-conditional-proposed`は条件付き利用の設計提案であり、本番適用前にユーザー確認を要する。
- historical / deprecated / eval-onlyは通常生成の参照対象にしない。
