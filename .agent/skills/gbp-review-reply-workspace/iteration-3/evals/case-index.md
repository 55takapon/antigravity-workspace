# iteration-3 評価ケース一覧

各ケースは4 assertions、rubricは16観点・最大32点。`critical` はそのケースでcritical failureがあったかを示す。

| ID | 領域 | eval_name | old assertions | old critical | old rubric | candidate assertions | candidate critical | candidate rubric |
|---:|:---|:---|---:|:---:|---:|---:|:---:|---:|
| 1 | 自然語・高評価 | five-star-no-text-complete-gratitude | 4/4 | no | 32 | 4/4 | no | 32 |
| 2 | 自然語・高評価 | one-line-five-star-natural-reply | 4/4 | no | 32 | 4/4 | no | 32 |
| 3 | 自然語・高評価 | detailed-five-star-focused-reply | 4/4 | no | 32 | 4/4 | no | 32 |
| 4 | 自然語・高評価 | batch-standard-welcome-repetition-allowed | 4/4 | no | 32 | 4/4 | no | 32 |
| 5 | 自然語・高評価 | reject-abstract-welcome-variation | 4/4 | no | 32 | 4/4 | no | 32 |
| 6 | 自然語・高評価 | reject-dry-reception-ending | 4/4 | no | 32 | 4/4 | no | 32 |
| 7 | 自然語・高評価 | regional-welcome-requires-profile-permission | 4/4 | no | 32 | 4/4 | no | 32 |
| 8 | 低評価severity | low-severity-minor-wait-l1 | 4/4 | no | 26 | 4/4 | no | 32 |
| 9 | 低評価severity | low-severity-long-wait-no-explanation-l2 | 3/4 | no | 28 | 4/4 | no | 32 |
| 10 | 低評価severity | low-severity-order-not-served-unanswered-l3 | 2/4 | no | 20 | 4/4 | no | 32 |
| 11 | 低評価severity | low-rating-staff-attitude-accountability | 3/4 | no | 29 | 4/4 | no | 32 |
| 12 | 低評価severity | low-rating-taste-quantity-subjective | 4/4 | no | 30 | 4/4 | no | 30 |
| 13 | 低評価severity | low-rating-confirmed-hygiene-safety-l3 | 3/4 | no | 28 | 4/4 | no | 32 |
| 14 | 低評価severity | low-rating-unverified-disputed-facts-l4 | 3/4 | no | 29 | 4/4 | no | 32 |
| 15 | 低評価severity | one-star-no-text-no-cause-inference | 3/4 | no | 23 | 4/4 | no | 30 |
| 16 | 低評価severity | verified-remediation-may-be-stated | 3/4 | no | 29 | 4/4 | no | 32 |
| 17 | 低評価severity | reject-inward-apology-wording | 4/4 | no | 32 | 4/4 | no | 32 |
| 18 | 表現回帰 | reject-empty-sincerity | 1/4 | yes | 17 | 4/4 | no | 32 |
| 19 | 表現回帰 | reject-time-spent-gratitude | 1/4 | yes | 27 | 4/4 | no | 32 |
| 20 | 表現回帰 | reject-courage-narrative | 4/4 | no | 32 | 4/4 | no | 32 |
| 21 | 表現回帰 | reject-situation-detail-as-default-close | 2/4 | yes | 26 | 4/4 | no | 32 |
| 22 | 表現回帰 | allow-situation-detail-after-private-followup | 4/4 | no | 32 | 4/4 | no | 32 |
| 23 | 表現回帰 | allow-valuable-opinion-standard-close | 4/4 | no | 32 | 4/4 | no | 32 |
| 24 | 表現回帰 | allow-candid-opinion-contextually | 4/4 | no | 32 | 4/4 | no | 32 |
| 25 | 高リスク | clinic-fee-explanation-high-risk | 3/4 | no | 29 | 4/4 | no | 32 |
| 26 | 高リスク | clinic-sensitive-treatment-review | 3/4 | no | 29 | 4/4 | no | 32 |
| 27 | 高リスク | professional-service-fee-contract-risk | 3/4 | no | 29 | 4/4 | no | 32 |
| 28 | 高リスク | professional-service-case-outcome-risk | 3/4 | no | 29 | 4/4 | no | 32 |
| 29 | 高リスク | foreign-language-low-rating | 4/4 | no | 32 | 4/4 | no | 32 |
| 30 | 状態・資料 | already-replied-skip-duplicate | 4/4 | no | 32 | 4/4 | no | 32 |
| 31 | 状態・資料 | knowledge-promotion-leak-blocked | 4/4 | no | 32 | 4/4 | no | 32 |
| 32 | 状態・資料 | workbook-candidates-not-auto-approved | 3/4 | no | 31 | 4/4 | no | 32 |
| 33 | 状態・資料 | a36-not-active-model | 1/4 | yes | 21 | 4/4 | no | 32 |
| 34 | 状態・資料 | phrase-state-correct-selection | 3/4 | no | 31 | 4/4 | no | 32 |

## 合計

| 指標 | old | candidate |
|:---|---:|---:|
| assertions | 111/136 | 136/136 |
| critical failure | 4 | 0 |
| assertion回帰 | - | 0 |
| rubric dimension低下 | - | 0 |

token数・所要時間は取得不可。正式benchmarkの0.0は欠測fallbackであり、実測値ではない。
