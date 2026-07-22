# A35履歴分離・U-R06確定反映

## 結果

- 投稿済みA35は、source上の`active`事実、元入力、元返信を`approved-replies.md`へhistorical sourceとして無改変で保持した。
- A35をruntime全文例から分離し、同じ入力に対する2026-07-22ユーザー確定稿を新ID U-R06=`confirmed-good`として登録した。
- runtime全文例は26件、通常router参照候補も26件である。
- U-R06は、口コミに明記された雰囲気・食事・接客だけを扱い、接客評価を「励みになります」へ自然に接続して、一般的な歓迎で完結する。
- 「嬉しく思います」は全面NGにせず、定型的な店側感情になりやすいため`limited-use`・連続使用非推奨としてQB20へ登録した。

## 同期したファイル

- `candidate-skill/gbp-review-reply/SKILL.md`
- `candidate-skill/gbp-review-reply/references/reply-rules.md`
- `candidate-skill/gbp-review-reply/references/feedback-loop.md`
- `candidate-skill/gbp-review-reply/references/changelog.md`
- `candidate-skill/gbp-review-reply/examples/positive-detailed.md`
- `candidate-skill/gbp-review-reply/examples/case-index.md`
- `candidate-skill/gbp-review-reply/examples/good-output.md`
- `candidate-skill/gbp-review-reply/examples/approved-replies.md`
- `candidate-skill/gbp-review-reply/examples/quality-boundaries.md`
- `pre-production-report.md`

本番、snapshot、iteration-4の評価入力・出力は変更していない。

## hash検査

| 対象 | SHA-256 | 結果 |
|:---|:---|:---|
| 旧A35返信 / historical source | `239b9aef8d4b3f6a8c8c44b0a7c65a8fc257acdfb1c9bf434e114c83a092e323` | 変更前後一致 |
| 旧A35元入力＋元返信 / historical source | `70fa65c47df61d76a031414cef6bef100e474f64064c2dc254e13ff545fb27ee` | 変更前後一致 |
| 新U-R06返信 | `413f7c265a38bc716af7d6e480dd45cb6b57ea93b05d141cbad49bd7f66b30fa` | ユーザー確定稿と完全一致 |
| runtime 26件corpus | `4584529033ac2afbb4c0fe5cbf336d719e64265ee848a106d561ead75804fa67` | 26件抽出 |

- U-R06以外のruntime 25件: 本文差分0件
- A35元入力: historical sourceと完全一致
- A35元返信: historical sourceと完全一致
- candidate内Markdownリンク切れ: 0件

## 状態検査

- A35: `historical（source active）`、posted、runtime非参照
- U-R06: `confirmed-good`、未投稿品質例、通常router参照可
- runtime全文例: 26件
- 通常router参照候補: 26件
- G06-RP: `eval-only-workflow-control`を維持

## QA境界

この変更では本文hash、件数、状態同期、リンクを検査した。A35確定反映後の独立QA、34ケース、skill-checkerの再実行は独立QA担当が行う。
