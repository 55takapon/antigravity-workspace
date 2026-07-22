# iteration-4 評価生成記録（ID13〜23）

## 対象

- ID13〜23の11ケース
- `with_skill`: iteration-4 candidate-skillを適用
- `old_skill`: skill-snapshot/iteration-4を適用
- gradingは未作成
- timingは実測不能のため、全件で `measurement_status: unavailable_in_subagent_interface`、数値項目は `null`

## old_skillの機械再利用

iteration-3とiteration-4の `eval_metadata.json` がSHA-256一致し、かつiteration-3 candidate-skillとskill-snapshot/iteration-4が全8ファイル一致した次の9件のみ、iteration-3 `with_skill` のresponse/timingをiteration-4 `old_skill`へ機械コピーした。

- ID13 low-rating-confirmed-hygiene-safety-l3
- ID16 verified-remediation-may-be-stated
- ID17 reject-inward-apology-wording
- ID18 reject-empty-sincerity
- ID19 reject-time-spent-gratitude
- ID20 reject-courage-narrative
- ID21 reject-situation-detail-as-default-close
- ID22 allow-situation-detail-after-private-followup
- ID23 allow-valuable-opinion-standard-close

コピー元・先のresponse.mdとtiming.jsonは、9件すべてSHA-256一致を確認した。

## old_skillの新規生成

iteration-3との `eval_metadata.json` が一致しないため、次の2件は機械再利用せず、snapshot4を適用して新規生成した。

- ID14 low-rating-unverified-disputed-facts-l4
- ID15 one-star-no-text-no-cause-inference

## with_skillの新規生成

次の11件はすべてiteration-4 candidate-skillと各 `eval_metadata.json` を適用して新規生成した。

- ID13〜23

## 完了確認

- 11ケースすべてに `old_skill/outputs/response.md` あり
- 11ケースすべてに `old_skill/timing.json` あり
- 11ケースすべてに `with_skill/outputs/response.md` あり
- 11ケースすべてに `with_skill/timing.json` あり
- 出力本文へ内部説明・採点・スタイル分類を混入していない
- 編集範囲はID13〜23のold_skill/with_skillと本記録のみ
