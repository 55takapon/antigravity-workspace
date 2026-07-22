# 良好全文例インデックス

このindexへの登録全文例は26件で、26件全てが通常routerの参照候補である。投稿済みA35は [approved-replies.md](approved-replies.md) にhistorical sourceとして分離し、runtimeでは参照しない。G06-RPは返信済み生成停止の工程制御であり、全文例数に含めない。

## router

| カテゴリ | 選択条件 | ファイル | 収録数 |
|:---|:---|:---|---:|
| star-only | 本文なし | [star-only.md](star-only.md) | 5 |
| positive-short | 短い肯定本文 | [positive-short.md](positive-short.md) | 2 |
| positive-detailed | 情報量の多い肯定本文 | [positive-detailed.md](positive-detailed.md) | 5 |
| mixed-low-rating | 肯定と不満の混合、または低評価 | [mixed-low-rating.md](mixed-low-rating.md) | 7 |
| high-risk-special | 医療・施術、士業、BtoB、外国語、事実争い等 | [high-risk-special.md](high-risk-special.md) | 7 |

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
| C03-UR05 | confirmed-good | 飲食、料理と接客。店づくり方針文はprofileで同方針を確認できる時だけ |
| U-R06 | confirmed-good | 飲食、雰囲気・食事・接客。明記点だけを扱い、接客評価を「励みになります」へ接続して歓迎で完結 |
| W01-HF | confirmed-good | 飲食、料理・雰囲気・再訪意思 |
| W02-HB | confirmed-good | 美容、仕上がり・カウンセリング |
| W03-HS | confirmed-good | 飲食、接客・料理・友人との時間 |
| G07-KL | confirmed-good | 飲食、knowledge販促漏入防止 |
| W04-LW | confirmed-good | 予約後の長時間待ち・説明不足。対象を特定できる具体的不備のお詫び役割も参照可 |
| W05-LA | confirmed-good | 主観的なスタッフ対応への不満。質問遮断等の具体的不備へ単独適用しない |
| W06-LB | confirmed-good | 美容、仕上がり・カウンセリング不満 |
| W07-LF | confirmed-good | 飲食、味・量・価格への不満 |
| W08-LP | confirmed-good | 価格と内容の比較評価 |
| W09-LH | confirmed-good | 衛生上の具体的指摘。対象明示のお詫び＋確認の役割も参照可 |
| G01-MX | confirmed-good | 飲食、肯定と軽い不満の混合 |
| W10-HD | confirmed-good | 歯科。口コミ本人の一般語「治療」の範囲に留め、痛み・効果・具体的処置を拾わず、説明と落ち着いて受けられる環境へ焦点を絞る |
| W11-HO | confirmed-good | 整骨院。「かなり軽くなった」「一度の施術」「肩」を拾わず、本人が明記した継続意思と感謝・一般的歓迎へ焦点を絞る |
| W12-HC | confirmed-good | クリニック、スタッフ対応 |
| G02-B2B | confirmed-good | BtoB、公開範囲を絞る高評価。低評価では公開可能な主要懸念を過剰削除しない |
| G03-FL | confirmed-good | 外国語、接客への低評価 |
| G04-DP | confirmed-good | 事実関係が未確認の低評価 |
| G05-MP | confirmed-good | 医療、診療情報を含む高評価 |

## 履歴との分離

- **A35**: posted事実、source上の`active`、元入力・元返信を [approved-replies.md](approved-replies.md) に保持する。runtime IDではなく通常生成から参照しない。

## 工程制御

### G06-RP — 返信済みレビュー

- 状態: `eval-only-workflow-control`
- 条件: 店舗返信がすでに投稿済みで、修正・追記依頼がない。
- 対応: `返信済みのため、新しい返信案は作成しません。`
- 禁止: 二重投稿案、既存返信の無断上書き、代替案の量産。

## 状態ガバナンス

- `candidate`をユーザー確認なしに`confirmed-good`または`active`へ昇格しない。
- historical / deprecated / eval-onlyは通常生成の参照対象にしない。
