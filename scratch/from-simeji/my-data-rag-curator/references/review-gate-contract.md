# レビューゲート契約

この資料は、RAG素材を `approved_verified` にする時の強制契約です。
目的は、本文整形スクリプト、旧レビュー、検索結果、固定本文リストだけで承認が成立しないようにすることです。

## 0. AI目視レビューの定義

この契約での目視レビューは、人間待ちではなく、このスキルを使うAIが `transcript` 本文と前後文脈を読んで、spanごとに判断することを指す。

最終状態を出せるのは `review_actor_type=skill_ai_visual_review` の判断だけにする。
`script_candidate_scan`、`script_prefilter`、`deterministic_source_scan_with_span_trace` は読む場所を集める補助であり、次を直接出してはならない。

- `approved_verified`
- `duplicate`
- `rejected_noise`
- `rejected_other_theme`
- `rejected_out_of_scope_sensitive`

スクリプト処理で判断が止まる場合は、必ず `needs_review` または `needs_revision` に戻す。

最終状態には次を必須にする。

- `review_actor_type=skill_ai_visual_review`
- `skill_paths_read`: この判断で読んだスキルと参照資料のpath。
- `pro_evidence_checked_at`: プロ事例証拠表を確認した日時。
- `human_review_packet_id`: どのレビュー束を読んだか。
- `span_decision_id`: どのspan判断から素材になったか。
- `reviewed_source_excerpt_hash`: 今回読んだ原文抜粋のhash。
- `generated_by_script_only=false`。

## 1. レビュー台帳ゲート

`approved_verified` は、今回の目視レビュー台帳にある `span_decisions[]` からだけ生成する。

承認spanには次を必須にする。

- `human_review_packet_id`: どのレビュー束を読んだか。
- `span_decision_id`: どのspan判断から素材になったか。
- `reviewed_source_excerpt_hash`: 今回読んだ原文抜粋のhash。
- `transcript_excerpt_read`: 今回読んだ原文抜粋。
- `source_read_evidence.transcript_path`。
- `source_read_evidence.range_read`。
- `span_evidence_quote`。
- `why_this_span_is_usable_or_not`。
- `generated_by_script_only=false`。
- `review_actor_type=skill_ai_visual_review`。
- `skill_paths_read`。
- `pro_evidence_checked_at`。

次の状態は承認根拠にしない。

- 旧レビュー集約からの変換。
- 既存Markdownからの復元。
- 検索スコア、クラスタ、正規表現だけの判断。
- 固定本文リストに存在すること。
- 本文整形スクリプトが作った下書きだけ。
- 既存対象素材の古い `clean_verbatim` を、今回の原文から作り直さず再承認すること。
- `review_actor_type=script_candidate_scan` の候補scan結果。
- `reviewed_at` が一括台帳の書き出し時刻で、AI目視レビューのspan別読了証跡がない結果。

## 2. 本文品質ゲート

`clean_verbatim` は本文1文ごとに原文対応を持つ。

`body_sentence_alignment[]` の各要素には次を必須にする。

- `clean_sentence`: 本文の1文。
- `source_quote`: 対応する原文または今回読んだ前後文脈。
- `timestamp_range`: `source_quote` の実timestamp。
- `source_type`: `claim`、`reason_or_context`、`example_or_action` のいずれか。
- `alignment_reason`: 主要語と意味がどう対応しているか。

`timestamp_range` は素材timestampの流用ではなく、実際に対応するquoteのtimestampにする。
対応quoteが素材timestamp外にある場合は、素材timestampを広げる、素材を分割する、または `needs_revision` に戻す。

本文品質フラグは自己申告で true にしない。
少なくとも次を検査結果から導出する。

- `grounded_in_raw`: 原文対応がない文が0件。
- `no_source_unbacked_addition`: 原文対応がない追加文が0件。
- `natural_length_not_threshold_padding`: 150字到達目的の水増しや未整形断片がない。
- `not_padded`: 原文にない理由、結論、具体例を足していない。

人間向けMarkdownに出した後の実本文も読む。
本文だけでなく、`文脈` 欄も人間向け表示として読む。
次のような誤変換、固有名詞、別論点、話し言葉断片が残る本文・文脈は `approved_verified` にしない。

- `日本を掲げ` のような明らかな誤変換。
- `各週間` のような意味が壊れた語。
- `高橋先生`、`4000万`、`本業で話し合う` のような、今回テーマの汎用素材ではなく個別文脈に寄る固有要素。
- `いるですが`、`全部やるです`、`でやるか、です`、`乗っけて` のような未整形の話し言葉断片。
- `なんだっけ`、`そのそうです`、`というふうには思いますね` のような、原文のつなぎをそのまま出した文脈欄。
- 複数の別論点をつなげただけの本文、または150字到達のために同じ主張を言い換えて重ねた本文。

## 3. 却下反証ゲート

`rejected_*` は最終判断なので、機械条件だけで確定しない。

特に次の語や文脈を含む候補は、反証レビューを必須にする。

- `PDCA`
- `行動量`
- `量をこな`
- `数をこな`
- `失敗`
- `改善`
- `経験値`
- `インプット`
- `アウトプット`
- `実践`
- `成長速度`

反証レビューの結果、使える余地があるが本文が未完成なら `needs_revision` に戻す。
重複なら既存素材IDと同じ主張または文脈の証拠を残して `duplicate` にする。
本当に使えない場合だけ、読んだ原文範囲と理由を残して `rejected_*` にする。
反証レビューには、`counter_review.usable_possibility_checked=true`、`counter_review.source_range_rechecked`、`counter_review.why_not_needs_revision` を残す。

## 4. importゲート

本番RAG投入前に、次を1件でも満たさない素材は拒否する。

- レビュー台帳に対応する `span_decision_id` がある。
- `generated_by_script_only=false` である。
- `human_review_packet_id` がある。
- `reviewed_source_excerpt_hash` がある。
- `review_actor_type=skill_ai_visual_review` である。
- `skill_paths_read` がある。
- `pro_evidence_checked_at` がある。
- `body_sentence_alignment` が本文文数と一致する。
- `body_sentence_alignment.timestamp_range` が空ではない。
- `completion_blockers` が空配列である。

importゲートは承認数を見ない。
承認数が少ない、多い、0件であることを品質根拠にしない。

## 5. 失敗fixture

次の実失敗は、同種テーマの再実行前にevalへ入れる。

- 未整形本文が `approved_verified` になる。
- 同一本文が別素材として残る。
- `source_quote` が素材timestamp外なのにtimestampが流用される。
- 150〜199字の短文理由がテンプレート化する。
- 強いテーマ語を含む却下候補が、反証レビューなしで `rejected_*` になる。
- スクリプト候補scanが `approved_verified`、`duplicate`、`rejected_*` を直接出す。
- batch source scan の `reviewed_at` をAI目視レビュー完了時刻として扱う。
- 本文品質未達や本文未完成を `rejected_*` で最終却下する。
- `assertions_total=0` のevalがpass扱いになる。
