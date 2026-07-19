# 鰻の神楽 京都店 口コミ返信log

## 原資料と移行方針

- 既存原資料: review-replies/2026-05_review_replies.md
- 原資料36件は削除・移動・要約上書きせず、口コミ原文、初稿・代替案、確定稿、修正履歴、投稿者名の監査証跡として保持する。
- 本ファイルは状態、返信日、頻度集計可否、再利用境界を正規化した索引である。原資料にない初稿全文、承認理由、投稿日を作らない。
- 今後の新規案件は references/feedback-loop.md の完全形式で、口コミ原文・初稿・最終投稿文・差分・理由を本ファイルへ直接記録する。

## 状態と頻度の定義

| 状態 | 意味 | 頻度対象 |
|:---|:---|:---|
| final_approved | 確定の表示はあるが投稿日は未確認 | yes |
| posted | 返信日または返信済み表示を確認 | yes |
| source_conflict | 採用案が空欄、または確定稿を一意に決められない | no |

draft、不採用案、別案、翻訳、参考訳、修正前文章は頻度へ含めない。

## iteration-3 profile decision（本番反映済み）

この節は口コミ投稿記録ではなく、2026-07-19にユーザー承認後、本番へ反映したprofile・再利用境界の判断である。投稿日、投稿済み、採用結果を新たに表すものではない。

| 判断対象 | 現行状態 | 扱い |
|:---|:---|:---|
| 京都駅付き締め | pending-user-reapproval | 一般歓迎からregional/promotional CTAへ分離し、再承認までは生成しない |
| #36の現行再利用 | historical | 本文とposted 2026-07-14、frequency yesを保持し、最新低評価基準の模倣元から外す |
| quality-boundaries.md | active | phrase-level品質境界台帳。ユーザー承認後、2026-07-19に本番新設済み |

## 旧36件の正規化索引

| # | 星 | 状態 | 返信日 | frequency | 現行再利用 | 理由タグ・注記 |
|---:|:---:|:---|:---|:---:|:---|:---|
| 1 | 5 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 2 | 5 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 3 | 5 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 4 | 5 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 5 | 5 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 6 | 3 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 7 | 3 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 8 | 1 | final_approved | 未確認 | yes | historical | 採用案1。投稿日未確認 |
| 9 | 5 | source_conflict | 未確認 | no | deprecated | trackerの採用案が空欄。source-conflict |
| 10 | 1 | source_conflict | 未確認 | no | deprecated | trackerの採用案が空欄。source-conflict |
| 11 | 4 | final_approved | 未確認 | yes | historical | 案1確定。投稿日未確認 |
| 12 | 5 | final_approved | 未確認 | yes | deprecated | 星だけ旧例。現行profileと再審査が必要 |
| 13 | 5 | final_approved | 未確認 | yes | historical | 案1確定。投稿日未確認 |
| 14 | 5 | final_approved | 未確認 | yes | historical | 案1確定。投稿日未確認 |
| 15 | 5 | final_approved | 未確認 | yes | historical | 案1確定。投稿日未確認 |
| 16 | 5 | final_approved | 未確認 | yes | historical | 案1確定。投稿日未確認 |
| 17 | 1 | final_approved | 未確認 | yes | historical | 英語確定。投稿日未確認 |
| 18 | 2 | final_approved | 未確認 | yes | historical | 案1確定。投稿日未確認 |
| 19 | 4 | final_approved | 未確認 | yes | historical | 案1確定。投稿日未確認 |
| 20 | 5 | posted | 2026-07-05 | yes | historical | unsupported-inferenceを修正した確定稿 |
| 21 | 5 | posted | 2026-07-05 | yes | historical | 一言口コミにCTA・感情文あり。現行では再審査 |
| 22 | 5 | posted | 2026-07-05 | yes | historical | unsupported-inferenceを修正した確定稿 |
| 23 | 4 | posted | 2026-07-05 | yes | historical | 現行profileで再審査が必要 |
| 24 | 5 | posted | 2026-07-05 | yes | historical | 再来店意思へCTAを重ねるため再審査 |
| 25 | 4 | posted | 2026-07-05 | yes | deprecated | empty-sentenceを含む旧例 |
| 26 | 5 | posted | 2026-07-05 | yes | historical | メニュー説明・CTAは条件付き |
| 27 | 5 | posted | 2026-07-05 | yes | historical | 全要素反復とCTAを再審査 |
| 28 | 5 | posted | 2026-07-05 | yes | deprecated | cta-pressure。同行形態を指定 |
| 29 | 5 | posted | 2026-07-08 | yes | active-conditional | unsupported-inference、patch-regressionをユーザー修正 |
| 30 | 5 | posted | 2026-07-10 | yes | historical | 事業者感情・CTAは条件付き |
| 31 | 5 | posted | 2026-07-12 | yes | historical | semantic-inflation修正済み。地域CTAは現行既定OFF |
| 32 | 5 | posted | 2026-07-12 | yes | historical | 再来店意思へCTAを重ねるため再審査 |
| 33 | 5 | posted | 2026-07-14 | yes | deprecated | 星だけへの感情、地域・店名、CTA補充 |
| 34 | 5 | posted | 2026-07-14 | yes | deprecated | semantic-inflation。曖昧な量を肯定変換 |
| 35 | 5 | posted | 2026-07-14 | yes | active-conditional | focus-selection、construction-repetitionをユーザー修正 |
| 36 | 1 | posted | 2026-07-14 | yes | historical | 本文・posted事実を保持。最新基準では直接謝罪と意見への感謝が不足し、現役模倣元にしない。共有・確認文は実行可能性確認が必要 |

## 再審査済み詳細記録

### #29 — 2026-07-08

| 項目 | 内容 |
|:---|:---|
| 星評価 | 5 |
| 状態 | posted |
| 結果 | ユーザー修正採用 |
| 理由タグ | unsupported-inference, patch-regression |
| 適用範囲 | C |

**口コミ原文**

> とても美味しくリーズナブルに鰻を食べられました！う巻きや天ぷらがセットで、こんなにお手頃だと、また気軽に来れそうです！！

**初稿**

> 原資料に初稿全文なし。修正履歴では、口コミにない「お腹いっぱい」を追加したと確認できる。

**最終投稿文**

> 「また気軽に来れそう」との温かいお言葉をありがとうございます。
>
> う巻きや天ぷらとともに鰻をお楽しみいただけたとのこと、スタッフ一同、とても嬉しく思います。京都駅近くへお越しの際は、いつでもお気軽にお立ち寄りください。

**修正理由**

- 口コミにない満腹表現を削除し、ユーザー提示版で主語と締めを確定した。
- 現行運用では地域CTAと「スタッフ一同」を自動流用しない。

### #35 — 2026-07-14

| 項目 | 内容 |
|:---|:---|
| 星評価 | 5 |
| 状態 | posted |
| 結果 | ユーザー修正採用 |
| 理由タグ | focus-selection, construction-repetition |
| 適用範囲 | C |

**口コミ原文**

> おいしかったです。お店の雰囲気が落ち着いていてゆっくり食事できました。丁寧に接客していただきありがとうございました。

**初稿**

> 原資料に初稿全文なし。修正履歴では「いただき」の反復と、3点すべてを返す過剰反復を確認できる。

**最終投稿文**

> 温かい口コミをありがとうございます。落ち着いた雰囲気の中でゆっくりお過ごしいただけたようで、また接客も丁寧とお褒めくださり、嬉しく思います。またのご来店をお待ちしております。

**修正理由**

- 味の一文を削り、雰囲気と接客の2点へ絞った。
- 現行運用では感情表現とCTAをprofile条件に照らして再判断する。

### #36 — 2026-07-14

| 項目 | 内容 |
|:---|:---|
| 星評価 | 1 |
| 状態 | posted |
| 結果 | 確定・返信済み |
| 理由タグ | なし |
| 適用範囲 | C |

**口コミ原文**

> 色々と食べてきたが、がっかりです。特上を頼んだけど、タレがイマイチ、焼き具合もイマイチ、全てダメです。うなぎもゴムみたいでした。日本人は行かない方が良いです。お金のムダです。

**初稿**

> 原資料では確定稿のみ。別の初稿は確認できない。

**最終投稿文**

> このたびは、ご意見をお寄せいただきありがとうございます。
>
> タレや焼き具合、うなぎの食感について、ご期待に沿えなかったとのこと、真摯に受け止めております。
>
> いただいたご指摘は調理担当と共有し、タレの状態や焼き上がり、提供時の品質をあらためて確認してまいります。

**修正理由**

- 原因を推測せず、本文にある論点へ限定した。
- 共有・品質確認を実行できることと実施意向を、再利用前に確認する。
