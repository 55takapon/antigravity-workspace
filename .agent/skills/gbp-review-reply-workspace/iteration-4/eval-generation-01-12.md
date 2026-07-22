# iteration-4 評価生成記録（ID 1〜12）

## 実施範囲

- `with_skill`: ID 1〜12をiteration-4候補スキルに基づき新規生成。
- `old_skill`: ID 2、3、4、6、7、10、11はiteration-3結果を機械的に再利用。ID 1、5、8、9、12はiteration-4旧版スナップショットに基づき新規生成。
- `timing.json`: サブエージェント環境では計測不能のため、全件を `measurement_status: unavailable_in_subagent_interface` として記録。
- `grading.json`: 作成していない。

## 旧版再利用の判定

iteration-3候補スキルと`skill-snapshot/iteration-4/gbp-review-reply`は、相対パスごとのSHA-256比較で8ファイルすべて一致した。加えて各ケースの`eval_metadata.json`が一致した場合に限り再利用した。

| ID | ケース | metadata一致 | old_skill処理 |
|---:|---|:---:|---|
| 1 | five-star-no-text-complete-gratitude | No | 新規生成 |
| 2 | one-line-five-star-natural-reply | Yes | iteration-3から再利用 |
| 3 | detailed-five-star-focused-reply | Yes | iteration-3から再利用 |
| 4 | batch-standard-welcome-repetition-allowed | Yes | iteration-3から再利用 |
| 5 | reject-abstract-welcome-variation | No | 新規生成 |
| 6 | reject-dry-reception-ending | Yes | iteration-3から再利用 |
| 7 | regional-welcome-requires-profile-permission | Yes | iteration-3から再利用 |
| 8 | low-severity-minor-wait-l1 | No | 新規生成 |
| 9 | low-severity-long-wait-no-explanation-l2 | No | 新規生成 |
| 10 | low-severity-order-not-served-unanswered-l3 | Yes | iteration-3から再利用 |
| 11 | low-rating-staff-attitude-accountability | Yes | iteration-3から再利用 |
| 12 | low-rating-taste-quantity-subjective | No | 新規生成 |

## 完了確認

- ID 1〜12の`old_skill/outputs/response.md`、`with_skill/outputs/response.md`、双方の`timing.json`が存在する。
- 再利用7件の旧版返信はiteration-3原本とSHA-256が一致する。
- 返信ファイルには公開返信文のみを記録した。
