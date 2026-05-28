---
name: my-data-rag-curator
description: >-
  マイデータRAG、RAG構築、話素材RAG、ナレッジRAG、目視分類、原文確認、候補台帳、承認済み素材、transcriptから素材化、未確認候補を分類して、RAGを完成させて等で必ず使う。原文目視確認で採否理由付きの素材台帳・再監査レポート・完成/未完了報告を出力する。
---

# マイデータRAGキュレーター

本人データを、検索で使える承認済みRAG素材へ整理するためのスキルです。
候補出しだけで終わらせず、必ず原文と前後文脈を目視確認して採否を決めます。

## 必須実行ルール

- 最初に進捗チェックリストを作り、各工程が終わるたびに更新する。
- 工程ごとに指定された参照資料を必ず読む。任意参照にしない。
- RAGテーマの再実行、既存素材の再監査、品質改善を行う前に、必ず [references/pro-rag-quality-evidence.md](references/pro-rag-quality-evidence.md) を読み、プロ事例から採用する型と採用しない型を確認する。
- `approved_verified` の生成経路を変更・実行する前に、必ず [references/review-gate-contract.md](references/review-gate-contract.md) を読み、レビュー台帳、span判断、本文対応、importゲートの契約を確認する。
- 原文と前後文脈を読まない限り、`approved_verified` にしない。
- `approved_verified` は、今回作成した目視レビュー台帳の `span_decisions` からだけ生成する。本文整形スクリプト、固定本文リスト、旧MD、旧レビュー集約、検索結果から直接生成してはならない。
- 本番RAGへ反映するのは `approved_verified` だけにする。
- 候補束の目視分類は、原則として1回8〜24束、通常上限30束で行う。
- 31〜40束を1回で扱う場合は、同じ動画、近い時間、同じ話題で続けて読める時だけにし、例外理由を記録する。
- 40束超は必ず分割する。80束以上、数百束一括の採否確定は無効扱いにし、再監査へ戻す。
- `duplicate` は、既存素材ID、source/timestamp、同じ主張または同じ文脈の証拠を残した時だけ確定する。
- 束レビューの目的は素材数を増やすことではなく、候補範囲の中に使える発話があるかを漏れなく確認すること。
- 1束から承認素材が0件、1件、複数件のどれになることもある。件数を先に決めてはならない。
- 承認数、束数、候補数を成果指標にしない。成果指標は、原文根拠、本文品質、重複証拠、候補span確認の完了で見る。
- `approved_verified` には、原文確認、前後文脈確認、本文品質確認、重複確認、候補span確認の証跡を残す。
- `approved_verified` には、`source_read_evidence`、`body_quality_review`、`span_decisions`、`all_usable_spans_extracted`、該当する場合の `duplicate_evidence` を必須にする。
- `source_read_evidence` は今回のレビューで実際に読んだ原文範囲から作る。旧レビュー、旧承認集約、検索結果、既存MD、別日レビューを変換・転記しただけの証跡は `approved_verified` の根拠にしてはならない。
- 全レビュー行には、今回読んだ `transcript_excerpt_read` または同等の原文抜粋、`review_basis.legacy_review_used=false`、読んだ時点の `review_run_id`、`reviewed_at` を残す。これが欠ける行は未完了に戻す。
- `span_decisions` の各spanにも、今回読んだ `transcript_excerpt_read`、`source_read_evidence.range_read`、`span_evidence_quote`、`why_this_span_is_usable_or_not` を必須にする。束行だけに原文抜粋があり、span側に読んだ証跡がないものは未読扱いで無効にする。
- `span_decisions` の各spanには、`human_review_packet_id`、`span_decision_id`、`reviewed_source_excerpt_hash`、`generated_by_script_only=false` を必須にする。これがない承認は、レビュー台帳を通っていないものとして無効にする。
- ここでいう目視レビューは、このスキルを使うAIが `transcript` 本文と前後文脈を実際に読んで判断すること。外部の人間待ちを前提にせず、スクリプトの一括処理だけを目視レビューと呼んではならない。
- `approved_verified`、`duplicate`、`rejected_*` の最終状態には、`review_actor_type=skill_ai_visual_review`、`skill_paths_read`、`pro_evidence_checked_at` を必須にする。これがないものはAI目視レビュー実行証跡なしとして無効にする。
- スクリプトが作れるのは `review_actor_type=script_candidate_scan` の候補scanまで。候補scanは `needs_review` または `needs_revision` に止め、`approved_verified`、`duplicate`、`rejected_*` を直接出してはならない。
- `all_usable_spans_extracted` や `all_candidate_spans_checked` は、全spanに原文証跡が揃っている時だけ true にする。スクリプトやAIが自己申告で true を書いただけのものは完了扱いにしない。
- 機械判定は `machine_prefilter_reason` にだけ記録し、最終採否理由は `final_decision_reason` に原文根拠つきで書く。
- `final_decision_reason` がスコア、検索順位、クラスタ名、テーマ語不足、既存と近い、だけで終わる行は無効にする。
- 中心語、score、クラスタ、検索順位、正規表現、`near_approved`、`overlaps_approved` は読む順番の補助であり、`approved_verified`、`duplicate`、`rejected_*` の最終状態を直接出してはならない。機械判定で判断が止まる場合は `needs_review` または `needs_revision` に戻す。
- 強いテーマ語や行動示唆を含む候補を `rejected_*` にする場合は、反証レビューを必須にする。反証レビューで使える余地が残るものは `needs_revision` へ戻し、機械条件だけで却下しない。
- `approved_verified`、`duplicate`、`rejected_*` の全状態に、今回読んだ原文範囲、前後文脈、判断理由を残す。
- 本文は改行や空白を除いた見える本文で150〜600字を必須帯とする。150字未満は `needs_revision` または却下、600字超は分割検討、1000字超は原則分割にする。
- 150字を満たすための水増し、原文にない結論・理由・具体例の追加、要約化を合格扱いにしない。
- 本文は150〜600字の範囲だけで合格にしない。原文にある主張、理由または背景、具体例または行動示唆が自然に残っている時だけ合格にする。
- 本文未作成は却下理由ではない。使える可能性が残るが人間向け本文が未完成なら `needs_revision` に戻し、`rejected_*` へ逃がしてはならない。
- `SOURCE_VERIFIED_BODY_OVERRIDES` のような固定本文リストの有無で採否を決めてはならない。固定本文は本文作成済みの補助データであり、承認リストではない。
- `clean_verbatim` の各文は、原文または今回読んだ前後文脈のどこに根拠があるかを `body_quality_review.body_sentence_alignment` に残す。
- `body_sentence_alignment` は本文1文ごとの対応でなければならない。広い原文範囲を貼るだけ、主要語が原文側にない対応、意味が推測でつながっているだけの対応は無効にする。
- `body_sentence_alignment.timestamp_range` は、対応する `source_quote` の実timestampを入れる。素材timestampを流用してはならない。対応quoteが素材timestamp外にある場合は、素材timestampを広げるか、素材を分割するか、`needs_revision` へ戻す。
- `body_sentence_alignment` がない本文、原文対応がない文、原文にない一般化・結論・理由・具体例・行動示唆を含む本文は `approved_verified` にしない。
- `clean_verbatim` に「そうです」「であとは」「でまぁ」「という形」「やってる」「されてる」「ですよです」「くださいね」など未整形の話し言葉、文の切れ端、不自然な接続が残る場合は `approved_verified` にしない。
- 150〜199字の本文は、原文に追加で残すべき情報がないことを `short_body_justification` に書かない限り再確認へ戻す。
- 機械チェック、検索スコア、クラスタ、AI判定は読む順番や不合格検出の補助であり、`approved_verified` の承認根拠にしない。
- evalの `assertions_total` が0の結果は、評価未実施として失敗にする。
- `manual_body_required` が1件でも残る監査結果、または `clean_sentence_without_source_count` が1件でもある監査結果は完了扱いにしない。
- 完了報告前に、全レビュー行の必須証跡欠落が0であることを確認する。欠落が1件でもあれば完成扱いにしない。
- 完了報告前に、大量束の `reviewed_at` が短時間へ集中していないか、同じ `final_decision_reason` が大量再利用されていないか、span側の原文証跡欠落が0かを確認する。どれか1件でも監査で検出されたら完成扱いにしない。
- 完了報告前に、承認素材の由来が今回のレビュー台帳から生成されていることを確認する。旧 `approved_material_spans` を再利用した件数、固定件数、古い集約ファイル由来の素材が1件でもあれば完成扱いにしない。
- 既存承認済み素材は、今回の承認リストに入らなかっただけで削除してはならない。削除する場合は、素材IDごとに `invalidation_decision`、読んだ原文範囲、無効理由、代替素材IDまたは代替なし理由を残す。
- ユーザーが承認したプランのうち「全束を目視レビューする」「元transcriptと前後文脈を読む」「使えるspanを全て確認する」などの完了条件を、実装計画で「既存レビュー変換」へ置き換えてはならない。
- 完了条件を満たせる作業は、途中で止めずにそのまま進める。
- 破壊的操作、削除、原本RAGの上書きなど高リスク操作だけは、事前に安全確認する。

進捗チェックリスト:

- [ ] 現状確認
- [ ] 既存承認済み素材の再監査
- [ ] 未確認候補の目視分類
- [ ] 使える発話の素材化
- [ ] RAG反映と検索確認
- [ ] 完成可否の報告

## 手順アウトライン

1. **対象と現状を確認する**
   必ず [references/pro-rag-quality-evidence.md](references/pro-rag-quality-evidence.md)、[references/review-gate-contract.md](references/review-gate-contract.md)、[references/workflow.md](references/workflow.md) の「1. 現状確認」を読む。
   入力: ユーザー依頼、対象テーマ、原本データ、候補台帳、既存承認済み素材。
   出力: 現状メモ。
   完了条件: 原本RAG、候補台帳、承認済み素材、人間向けMarkdown、検索用Markdownの場所と件数を確認していること。この完了条件を満たすまで、次に進んではならない。

2. **既存承認済み素材を再監査する**
   必ず [references/review-criteria.md](references/review-criteria.md) と [references/output-format.md](references/output-format.md) の「再監査レポート」を読む。
   入力: 既存の承認済み素材と元transcript。
   出力: 再監査レポート。
   完了条件: 原文一致、意味保持、本文品質、1素材1論点、前後文脈、使える理由、内容タグ、出典、安全性を必ず目視確認し、`approved_verified` または修正先を決めていること。この完了条件を満たすまで、次に進んではならない。

3. **未確認候補を目視分類する**
   必ず [references/workflow.md](references/workflow.md) の「候補の束ね方」、[references/review-gate-contract.md](references/review-gate-contract.md) の「レビュー台帳ゲート」、[references/review-criteria.md](references/review-criteria.md) の状態別基準を読む。
   入力: 候補台帳、重複候補、テーマ地図、元transcript。
   出力: 目視分類台帳。
   完了条件: 候補を原文と前後文脈で確認し、採否状態、理由、`all_candidate_spans_checked` または `all_usable_spans_extracted`、`span_decisions` を残していること。候補台帳やクラスタだけを見て分類済みとしてはならない。この完了条件を満たすまで、次に進んではならない。

4. **使える発話を素材化する**
   必ず [references/review-criteria.md](references/review-criteria.md) の採用基準とタグ基準、[references/review-gate-contract.md](references/review-gate-contract.md) の「本文品質ゲート」を読む。
   入力: `approved_verified` にする候補、元transcript、既存素材。
   出力: 承認済み素材台帳。
   完了条件: 原文にない補足を入れず、`raw_excerpt`、`clean_verbatim`、`source_context`、`why_useful`、`topic_tags`、`citation`、`review_status`、`source_read_evidence`、`body_quality_review` が揃っていること。この完了条件を満たすまで、本番RAGへ入れてはならない。

5. **RAGへ反映して検索確認する**
   必ず [references/workflow.md](references/workflow.md) の「RAG更新」と「完成判定」を読む。
   入力: 承認済み素材台帳。
   出力: 人間向けMarkdown、素材単位Markdown、検索評価結果。
   完了条件: 承認済み素材だけが反映され、素材単位で検索でき、代表検索で必要素材が返ること。この完了条件を満たすまで、完成報告してはならない。

6. **完成可否を報告する**
   必ず [references/output-format.md](references/output-format.md) と [examples/good-output.md](examples/good-output.md) を読み、完成/未完了を取り違えない。
   入力: 再監査レポート、目視分類台帳、検索評価、残件。
   出力: 完成報告または未完了報告。
   完了条件: 完成と言える根拠、まだ残る候補、残リスク、次にやることを分けて書いていること。この完了条件を満たすまで、完了報告してはならない。

## エッジケース

| 状況 | 対応 |
|:--|:--|
| 既存素材に承認済みと書かれているが確認記録が薄い | 最終承認扱いにせず、再監査へ戻す |
| 旧レビューや旧承認集約を現行schemaへ変換した | 新規レビュー完了扱いにしない。`converted_legacy_review` として監査し、元transcriptを今回読み直す |
| 候補数が多すぎる | source/timestamp近辺で束ねる。1回8〜24束を標準、30束を通常上限、40束超は分割。採否は必ず原文目視で決める |
| 使えそうだが文脈が足りない | `needs_context` にして前後を広げる |
| 既存素材とほぼ同じ | `duplicate` にして既存素材へ紐づける |
| 個人情報や固有事情が強い | 安全に汎用化できなければ `rejected_out_of_scope_sensitive` にする |
| 1束を読んだが承認素材が0件 | `approved_material_count: 0` としてよい。`all_candidate_spans_checked: true` と落とした理由を残す |
| 1束に使える発話が複数ある | 件数目的で増やさず、それぞれが独立して原文根拠・本文品質・1素材1論点を満たす時だけ複数素材化する |

## 禁止事項

- 特定テーマ名だけで発火する専用スキルにしてはならない。
- 指定された参照資料を読まずに工程を進めてはならない。
- 候補台帳を作っただけで完成と言ってはならない。
- 旧レビュー、旧承認集約、過去のMD、検索結果を現行schemaへ変換しただけで、今回の目視レビュー完了と言ってはならない。
- 完了検査で承認数を固定値にしてはならない。承認数は今回のレビュー結果から導出し、固定値一致を品質根拠にしてはならない。
- 数十〜数百束を一括で `duplicate`、`rejected`、`approved_verified` に確定してはならない。
- 1束1素材、1束複数素材など、承認件数のノルマを置いてはならない。
- 承認数を増やすために、薄い発話を無理に素材化したり、150字前後へ水増ししたりしてはならない。
- 検索結果やスコアだけで `approved_verified` にしてはならない。
- 原文を読まずに `clean_verbatim` を作ってはならない。
- 原文にない理由、具体例、補足を入れてはならない。
- 未確認候補、旧 `approved`、要修正素材、媒体名タグだけの素材を本番RAGへ入れてはならない。
- X投稿、LINE、Discordなど媒体別の書き方をこのスキル内で作ってはならない。

## 自己完了確認

完了報告前に必ず確認すること。

- 対象と現状を確認した。
- 既存承認済み素材を再監査した。
- 未確認候補を原文と前後文脈で目視分類した。
- 各束で `all_candidate_spans_checked` または `all_usable_spans_extracted` と `span_decisions` を残した。
- 各束の証跡が今回読んだ transcript 抜粋と `review_basis.legacy_review_used=false` を持ち、旧レビュー変換だけではないことを確認した。
- 承認素材一覧が旧 `approved_material_spans` からの再利用ではなく、今回のレビュー台帳の `span_decisions` から生成されていることを確認した。
- 採否理由を台帳に残した。
- 承認素材には `source_read_evidence` と `body_quality_review` を残した。
- 承認数を成果指標にしていない。
- 承認済み素材だけをRAGへ反映した。
- 検索品質と根拠性を確認した。
- 未完了なら、残件とリスクを完成扱いにせず報告した。
