# マイデータRAG構築ワークフロー

このファイルは任意の参考資料ではなく、作業手順の正本。
`SKILL.md` の各工程で指定された章を読み、完了条件を満たすまで次の工程へ進まない。

作業中は、少なくとも次の証跡を残す。

- どの原本データを見たか。
- どの候補を読んだか。
- 原文のどの前後文脈を確認したか。
- 採用、却下、重複、要修正、文脈不足の理由。
- RAGへ入れた素材と、入れなかった候補の境界。
- 束内の候補spanを全て確認した証跡。
- 承認素材ごとの本文品質確認と原文確認の証跡。
- 今回のレビューで実際に読んだ原文抜粋、読んだ日時、レビューrun ID。
- 束行だけでなく `span_decisions[]` 各要素に残した、今回読んだ原文抜粋、読んだ範囲、判断根拠。
- `approved_verified` がどの `human_review_packet_id` と `span_decision_id` から生成されたか。
- 今回読んだ原文抜粋の `reviewed_source_excerpt_hash`。
- 最終状態を出した主体が `review_actor_type=skill_ai_visual_review` であること。
- 判断時に読んだスキル資料 `skill_paths_read` と、プロ事例証拠表確認日時 `pro_evidence_checked_at`。

全工程は、次のブロッカー形式で扱う。
`入力`、`必須証跡`、`許可される補助`、`禁止される近道`、`完了条件` のどれかが欠けた工程は、完了扱いにしない。

旧レビュー、旧承認集約、既存Markdown、検索結果は、読む順番や比較対象としてだけ使える。
これらを現行schemaへ変換・転記しただけのものは、新規の目視レビュー証跡ではない。
`approved_verified` の根拠は、今回のレビュー中に元transcriptと前後文脈を読んだ記録だけにする。
本文整形スクリプトが作った本文は下書きであり、`span_decisions` の目視判断と import ゲートを通るまで本番承認ではない。
スクリプトの候補scanは `review_actor_type=script_candidate_scan` として扱い、`approved_verified`、`duplicate`、`rejected_*` の最終状態を直接出してはならない。
AI目視レビューに進む必要があるものは `needs_review`、本文品質や文単位対応を直す必要があるものは `needs_revision` に戻す。

## 1. 現状確認

### 入力

- ユーザー依頼。
- 対象テーマ。
- 原本データ。
- 候補台帳。
- 既存承認済み素材。
- 人間向けMarkdown。
- 素材単位Markdown。
- 検索RAGの状態。

### 必須証跡

- 原本データの場所と件数。
- 候補台帳の場所と件数。
- 既存承認済み素材の件数。
- 人間向けMarkdownの場所。
- 素材単位Markdownの場所。
- 検索RAGの状態。
- まだ候補台帳だけで、完成扱いにできない場合はその理由。
- 既存レビューや旧承認集約を使う場合は、それが補助資料か、未確認の旧データかを分けた記録。

### 許可される補助

- ファイル検索。
- 件数集計。
- 既存レポート確認。
- RAG status / eval / search の確認。

### 禁止される近道

- 候補台帳があるだけで完成扱いにする。
- 古い完成報告だけを見て現状確認済みにする。
- 旧承認集約の承認数を、今回のレビュー結果として扱う。
- 人間向けMarkdownと素材単位Markdownの片方だけを確認して両方確認済みにする。

### 完了条件

- 原本RAG、候補台帳、承認済み素材、人間向けMarkdown、検索用Markdown、検索RAG状態の場所と件数を確認している。
- 未確認や古い状態があれば、完成扱いではなく残件として分けている。

## 2. 既存承認済み素材の再監査

### 入力

- 既存の承認済み素材。
- 元transcript。
- 既存の再監査レポート。
- 既存の人間向けMarkdownと検索用Markdown。

### 必須証跡

- 元transcriptへ戻れるか。
- 今回の再監査で読んだ transcript 抜粋、`review_run_id`、`reviewed_at` があるか。
- `raw_excerpt` が原文に存在するか。
- `clean_verbatim` が意味を変えていないか。
- `clean_verbatim` が未整形の文字起こしに近いまま残っていないか。
- 1素材1論点になっているか。
- 本文が150〜600字の必須帯に収まっているか。
- 150字未満なら、前後文脈を原文から補って成立するか、落とすか。
- 600字超なら、主張、体験談、反論、具体例ごとに分割できるか。
- 1000字超なら、原則分割したか。
- 前後文脈が残っているか。
- `why_useful` が具体的か。
- `topic_tags` が内容タグか。
- 個人情報や固有事情が安全か。
- `source_read_evidence` と `body_quality_review` があるか。
- `source_read_evidence` が旧レビューや旧承認集約からの転記ではなく、今回読んだ範囲を示しているか。

### 許可される補助

- 文字数検査。
- schema検査。
- 重複候補検索。
- 既存素材ID検索。

### 禁止される近道

- 旧 `approved` をそのまま最終承認にする。
- 旧 `approved_verified`、旧レビュー、旧承認集約を現行schemaに変換して最終承認にする。
- `raw_excerpt` だけ、または `clean_verbatim` だけで合格にする。
- 150字を満たすために原文にない理由、結論、具体例を足す。
- 文字数が150字以上というだけで本文品質合格にする。
- 検索スコアやクラスタ名だけで重複確定する。

### 完了条件

- 1件ずつ原文、前後文脈、本文品質、1素材1論点、タグ、出典、安全性を確認している。
- 1件ずつ今回の `review_run_id` と読んだ transcript 抜粋があり、旧レビュー転記だけではない。
- 合格なら `approved_verified`、不足があれば `needs_revision`、`needs_context`、`duplicate`、`rejected_*` のどれかと理由を残している。
- 本番RAGへ入れられるのは、再監査後の `approved_verified` だけである。

## 3. 候補の束ね方

### 入力

- 候補台帳。
- source_id。
- timestamp。
- topic code。
- 既存承認済み素材ID。
- 元transcript。

### 必須証跡

- `bundle_id`。
- `round_id`。
- `candidate_ids`。
- `source_id`。
- `timestamp_start` と `timestamp_end`。
- `topic_codes`。
- `representative_raw_excerpt`。
- `transcript_range_to_read`。
- `related_approved_material_ids`。
- `bundle_reason`。
- `all_candidate_spans_checked` または `all_usable_spans_extracted`。
- `span_decisions`。
- `approved_material_count`。
- `review_run_id`。
- `reviewed_at`。
- `review_basis.legacy_review_used=false`。
- `review_basis.transcript_excerpt_read` または同等の今回読んだ原文抜粋。
- `span_decisions[]` 各要素の `transcript_excerpt_read`、`source_read_evidence.range_read`、`span_evidence_quote`、`why_this_span_is_usable_or_not`。
- `span_decisions[]` 各要素の `human_review_packet_id`、`span_decision_id`、`reviewed_source_excerpt_hash`、`generated_by_script_only=false`。
- `span_decisions[]` 各要素の `review_actor_type=skill_ai_visual_review`、`skill_paths_read`、`pro_evidence_checked_at`。

### 許可される補助

- 検索。
- クラスタ。
- 重複候補。
- 文字数検査。
- schema検査。
- eval。

### 禁止される近道

- 広いテーマ名だけで別動画や別文脈をまとめる。
- sourceが違う候補を、広いテーマ名だけで同じ束にする。
- timestamp が離れて話の流れが切れている候補を同じ束にする。
- `overlaps_approved`、`near_approved`、検索スコア、クラスタ名だけで重複確定する。
- `bundle_reason` を「同じsourceと近いtimestamp」だけで終わらせる。
- 旧レビューの `decision_reason` や `approved_material_span_ids` を今回の採否として転記する。
- 束行にだけ `transcript_excerpt_read` を残し、span判断側に原文証跡を残さない。
- `all_usable_spans_extracted` を、全span証跡なしの自己申告として使う。
- `script_candidate_scan` や `deterministic_source_scan_with_span_trace` を、AI目視レビュー完了として扱う。
- 一括書き出し時刻の `reviewed_at` を、spanごとの読了時刻として扱う。
- 1束から1素材だけに制限する。
- 1束から複数素材を出すことを義務にする。
- 承認数を成果指標にする。

### 完了条件

- 束は、同じ `source_id`、近いtimestamp、同じ話の流れ、同じ論点または連続する補足関係で作っている。
- `bundle_reason` には、主張、理由、具体例、反論、補足のどれが互いに補っているかを書いている。
- 読んだ結果、同じ束に別論点が混ざっていたら分割している。
- 1回の目視分類は標準8〜24束、通常上限30束。31〜40束は例外理由必須。40束超は分割。80束以上、数百束一括は無効扱い。

## 4. 未確認候補の目視分類

### 入力

- 候補または候補束。
- `raw_excerpt`。
- `transcript_range_to_read`。
- 元transcript。
- 既存素材。

### 必須証跡

- `source_read_evidence.transcript_path`。
- `source_read_evidence.range_read`。
- `source_read_evidence.range_extended`。
- `source_read_evidence.read_basis`。
- `span_decisions`。
- `usable_span_count`。
- `all_usable_spans_extracted`。
- 採用、却下、重複、要修正、文脈不足の理由。
- 入れた素材と入れなかった候補の境界。
- `review_run_id`。
- `reviewed_at`。
- 今回読んだ `transcript_excerpt_read`。
- `review_basis.legacy_review_used=false`。
- `review_basis.fresh_transcript_review=true`。
- `span_decisions[]` 各要素の `transcript_excerpt_read`、`source_read_evidence.range_read`、`span_evidence_quote`、`why_this_span_is_usable_or_not`。
- `span_decisions[]` 各要素の `review_actor_type=skill_ai_visual_review`、`skill_paths_read`、`pro_evidence_checked_at`。
- `all_usable_spans_extracted=true` の根拠になる全span証跡。束行だけの原文抜粋や、AI/スクリプトの自己申告だけでは不可。
- 強いテーマ語を含む却下候補を落とす場合は、反証レビューで使える余地がないことを確認した記録。

### 許可される補助

- 候補台帳。
- 重複候補検索。
- 文字数検査。
- schema検査。
- 既存素材検索。

### 禁止される近道

- representative_raw_excerpt だけで判断する。
- 本文整形スクリプトが本文を作れなかったことだけを理由に `rejected_*` へ落とす。
- 強いテーマ語、行動示唆、失敗から改善の文脈を含む候補を、反証レビューなしで最終却下する。
- 本文未完成、本文品質未達、固定本文リスト未登録を理由に `rejected_*` で最終却下する。
- `transcript_range_to_read` を読まずに採否を確定する。
- 旧レビュー、旧承認集約、既存MDの内容だけを読んで採否を確定する。
- 40束超を一括採否する。
- 検索スコアやクラスタ名だけで `approved_verified` にする。
- 中心語、score、クラスタ、検索順位、正規表現、`near_approved`、`overlaps_approved` だけで `duplicate` や `rejected_*` を確定する。
- 束行にだけ `transcript_excerpt_read` を残し、span判断側に原文証跡を残さない。
- 大量束の `reviewed_at` が短時間に集中したレビューを、目視完了として扱う。
- 同じ `final_decision_reason` を大量のspanに使い回す。
- 薄い発話を承認数目的で増やす。
- 150字前後へ水増しする。
- 原文にない説明を足す。
- 全span確認の証跡なしで完成扱いにする。

### 完了条件

- 候補の `raw_excerpt` と `transcript_range_to_read` の前後文脈を読んでいる。
- 旧レビューを見た場合でも、それとは別に今回の transcript 抜粋を読んだ証跡がある。
- 必要ならさらに前後へ広げ、実際に読んだ範囲を `range_read` に残している。
- 束内の候補spanを洗い出し、各spanの採否を `span_decisions` に残している。
- 各span判断に、今回読んだ原文抜粋、読んだ範囲、判断根拠、使える/使えない理由がある。
- 最終状態の各span判断に、AI目視レビュー主体、読んだスキル資料、プロ事例確認日時がある。
- 既存素材との重複なら、既存素材IDと、同じ主張・体験談・具体例・反論・文脈のどれに当たるかを書いている。
- 承認できるspanだけ、原文根拠、本文品質、1素材1論点、タグ、出典、安全性を確認している。
- 1束の結果は承認0件、1件、複数件のどれでもよいが、件数目的ではなく品質基準で決めている。

## 5. 承認済み素材への反映

### 入力

- `approved_verified` にする候補。
- 元transcript。
- 既存素材。
- 目視分類台帳。

### 必須証跡

- `material_id`。
- `source_id`。
- `timestamp_start`。
- `timestamp_end`。
- `raw_excerpt`。
- `clean_verbatim`。
- `source_context`。
- `why_useful`。
- `theme`。
- `narrative_role`。
- `topic_tags`。
- `sensitivity_status`。
- `citation`。
- `review_status`。
- `source_read_evidence`。
- `body_quality_review`。
- `review_contract_version`。
- `span_decisions`。
- `all_usable_spans_extracted`。
- `review_run_id`。
- `reviewed_at`。
- `review_basis`。

### 許可される補助

- `import_manual_material_review.py`。
- schema検査。
- 文字数検査。
- 重複ID検査。

### 禁止される近道

- 旧状態の `approved` を最終合格扱いにする。
- 旧レビューや旧承認集約から `approved_material_spans` をコピーして投入する。
- `source_read_evidence`、`body_quality_review`、`span_decisions`、`all_usable_spans_extracted` が欠けた素材を import する。
- `review_actor_type=skill_ai_visual_review`、`skill_paths_read`、`pro_evidence_checked_at` が欠けた素材を import する。
- 1束1素材制限を入れる。
- 複数spanが合格しているのに、1件だけ import する。

### 完了条件

- 本番RAGへ入る状態は `approved_verified` だけである。
- 承認素材ごとに `source_read_evidence` と `body_quality_review` がある。
- review単位で `span_decisions` と `all_usable_spans_extracted` がある。
- `approved_material_spans` が複数ある場合は、品質合格した全件を import 対象にしている。
- review単位で `review_basis.legacy_review_used=false` と今回読んだ transcript 抜粋がある。
- 承認素材一覧は、今回の `span_decisions` から導出され、古い承認集約の件数やIDリストを固定的に再利用していない。

## 6. RAG更新

### 入力

- 承認済み素材台帳。
- 動画別materials。
- `material_assets.jsonl`。
- 人間向けMarkdown。
- 素材単位Markdown。
- 検索RAG。

### 必須証跡

- 本番RAGへ反映した素材ID。
- 反映しなかった候補ID。
- 人間向けMarkdownの更新結果。
- 素材単位Markdownの更新結果。
- 検索RAGの索引化結果。
- 評価結果。
- 代表検索結果。
- 対象外素材IDの差分。

### 許可される補助

- build-material-knowledge。
- material-rag index-curated。
- material-eval。
- material-rag eval。
- 代表検索。
- git diff。

### 禁止される近道

- `approved_verified` 以外を反映する。
- `raw_excerpt` を人間向け本文として出す。
- 要約Markdownや独自まとめMarkdownを完成物として出す。
- 対象外RAGのIDを巻き込む。
- 検索評価なしで完成扱いにする。

### 完了条件

- 人間向けMarkdownには、見せる本文として `clean_verbatim` が出ている。
- 人間向けMarkdownと検索用Markdownは、各素材で次の順番を守る。
  1. 確認状態
  2. 内容タグ
  3. 出典とtimestamp
  4. 前後文脈
  5. 本文
  6. 使える理由
- 検索用Markdownには、根拠確認のため `raw_excerpt` を残してよい。
- 承認済み素材だけが反映され、素材単位で検索でき、代表検索で必要素材が返る。

## 7. 完成判定

### 入力

- 再監査レポート。
- 目視分類台帳。
- import結果。
- Markdown生成結果。
- 検索索引結果。
- eval結果。
- 代表検索結果。
- 差分。

### 必須証跡

- 既存承認済み素材の再監査完了。
- 未確認候補の目視分類完了、または残件とリスク。
- 本番RAGには `approved_verified` だけが入っていること。
- 全レビュー行の `span_decisions`。
- 全レビュー行の `all_usable_spans_extracted` または `all_candidate_spans_checked`。
- 全span判断の `transcript_excerpt_read`、`source_read_evidence.range_read`、`span_evidence_quote`、`why_this_span_is_usable_or_not`。
- レビュー時刻集中、同一理由大量再利用、span原文証跡欠落が0である監査結果。
- 承認素材の `source_read_evidence`。
- 承認素材の `body_quality_review`。
- 重複判定の証拠。
- 代表検索結果。
- 対象外ID差分。
- ユーザー承認プランの各完了条件と実行証跡の対応表。
- 実装計画が、ユーザー承認プランの必須工程を弱めていない確認。
- 全レビュー行の `review_run_id`、`reviewed_at`、`transcript_excerpt_read`、`legacy_review_used=false` の欠落0。
- 承認素材IDが今回レビュー行の `span_decisions` から全件導出されている確認。
- 旧 `approved_material_spans`、旧レビュー、旧MDから直接投入された素材数0。
- 固定承認数で合否判定していない確認。

### 許可される補助

- review audit。
- material-eval。
- material-rag eval。
- 代表検索。
- duplicate ID 検査。
- git diff --check。
- Final Checker。

### 禁止される近道

- 未確認候補が残るのに完成と言う。
- 証跡欠落があるのに完成と言う。
- 承認数や束数だけで完了判断する。
- 古いレポートだけで最新状態を確認済みにする。
- 実装計画の方がユーザー承認プランより狭いのに、狭い計画を正として Final Checker に渡す。
- 旧レビュー変換を fresh review と呼ぶ。
- `approved_material_span_count` を固定値にして合格判定する。
- 束行だけの原文証跡で、span判断まで読んだ扱いにする。
- 機械prefilterで出した理由を、最終採否理由として扱う。
- 既存素材を、今回の承認リストから外れたという理由だけで削除する。
- 評価失敗を警告扱いにして完成扱いにする。

### 完了条件

- 対象クラスター全件が、証拠付きで分類済み。
- `needs_context` と `needs_revision` が0、または残件とリスクを未完了として報告している。
- 必須証跡欠落が0。
- span原文証跡欠落、レビュー時刻集中、同一理由大量再利用、機械判定だけの最終採否が0。
- script最終判断、batch source scan最終判断、AI目視レビュー証跡欠落、反証なし強テーマ語却下、本文品質理由の最終却下が0。
- 旧データ転記、計画すり替え、固定件数合格、証跡ロンダリングが0。
- 本番RAGに入っている対象テーマ素材は、再レビュー後の `approved_verified` のみ。
- 人間向けMarkdownが既存形式と同じ順序で出ている。
- 対象外RAGのIDセットが作業前後で一致している。
- `material-eval` と `material-rag eval` がpass。
- 代表検索で対象素材が返り、無効IDが返らない。
- `git diff --check` と `Final Checker` が合格。

## 8. プロ手順との対応

- transcript から使える箇所を切り出す。
- タグで束ねる。
- 元データへ戻れる出典を残す。
- AI候補をそのまま採用せず、承認または却下する。
- 検索品質、根拠性、関連性、完全性を分けて見る。
- 最終出力だけでなく、途中traceを監査する。
- 新しい論点が増えなくなったかを見て、残リスクを説明する。
