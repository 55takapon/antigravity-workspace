# プロRAG品質の証拠表

このファイルは、RAG素材レビューの直し方と本文の書き方を、出典なしの自己流にしないための証拠表です。
RAGテーマを再実行する前に、ここで採用する型と採用しない型を確認します。
レビュー台帳とimportの強制契約は `review-gate-contract.md` を正本にします。

## 確認済みプロ事例

| ID | 種類 | 出典 | 確認日 | 実物として読んだ範囲 | 確認できたこと | 採用する点 | 採用しない点 |
|:---|:---|:---|:---|:---|:---|:---|:---|
| P1 | スキル作成基準 | Agent Skills Best Practices: https://agentskills.io/skill-creation/best-practices | 2026-05-20 | skill examples、progressive disclosure、templates、validation loops | スキルは実タスクから抽出し、詳細は参照資料へ分け、揺れる出力はテンプレートと検証で固定する | `SKILL.md` は入口、本文品質やschemaは `references/` に置く | 長大な手順を `AGENTS.md` や `SKILL.md` に全部入れない |
| P2 | スキル評価基準 | Agent Skills Evaluating Skills: https://agentskills.io/skill-creation/evaluating-skills | 2026-05-20 | evals/evals.json、expected output、assertions、with/without比較 | 現実的な入力、期待出力、assertion、比較評価でスキル品質を確認する | 評価ケースには必ずassertionを入れ、ゼロassertionを失敗扱いにする | eval名だけを並べて検証済み扱いにしない |
| P3 | 評価設計 | OpenAI Evaluation Best Practices: https://platform.openai.com/docs/guides/evaluation-best-practices | 2026-05-20 | objective、dataset、metrics、experiment、iteration | 評価は目的、データ、指標、比較、改善ループを分けて設計する | RAG品質の合否を、本文品質・根拠・検索・重複の指標へ分ける | 「良さそう」「件数が増えた」を品質指標にしない |
| P4 | transcriptレビュー運用 | Dovetail Highlights: https://docs.dovetail.com/help/highlights | 2026-05-20 | transcript highlight、tag、insight、AI suggestion review | transcript上の重要箇所を根拠へ戻せる形で扱い、AI提案もapprove/rejectで確認する | 候補出しと最終採否を分け、採否には原文箇所と判断理由を残す | AI候補やスコアを最終判断として扱わない |
| P5 | 動画QA運用事例 | AWS ReVIEW: https://aws.amazon.com/blogs/machine-learning/accelerate-video-qa-workflows-using-amazon-bedrock-knowledge-bases-amazon-transcribe-and-thoughtful-ux-design/ | 2026-05-20 | video transcript、timestamp citation、source video verification | 長尺動画からAIで候補を出しつつ、timestamp citationで元動画へ戻って確認する | `source_id`、timestamp、読んだ範囲、前後文脈を必須証跡にする | 動画由来なのに出典やtimestampなしで素材化しない |
| P6 | RAG評価 | Microsoft RAG Evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators | 2026-05-20 | retrieval、groundedness、relevance、completeness | RAG評価は検索品質、根拠性、関連性、完全性を分けて見る | 代表検索は全語ごとに確認し、1語ヒットだけでpassにしない | 検索が一部当たっただけで完了扱いにしない |
| P7 | retrieval設計 | Anthropic Contextual Retrieval: https://www.anthropic.com/engineering/contextual-retrieval | 2026-05-20 | contextual chunks、hybrid retrieval、reranking、eval | chunkや検索方式は評価とセットで設計し、検索失敗を測る | 束は意味ある読む単位にし、検索検証まで完了条件に入れる | 機械的な近接スコアだけで束や採否を確定しない |
| P8 | レビュー品質管理 | Label Studio Quality Review: https://docs.humansignal.com/guide/quality.html / Task Agreement: https://docs.humansignal.com/guide/stats.html | 2026-05-20 | review、agreement、ground truth、annotator performance | 品質は件数ではなく、レビュー可能な根拠、合意、ground truthとの差分で見る | `clean_verbatim` の各文に原文対応を残し、根拠なし文をfailにする | AI整形済みという自己申告だけで本文品質を合格にしない |
| P9 | 人間参加型AI設計 | Google People + AI Guidebook: https://pair.withgoogle.com/guidebook/ | 2026-05-21 | human-in-the-loop、AI confidence、failure handling | AI提案と判断責任を分け、重要判断は説明可能な確認ステップを置く | スクリプトは候補scanまでにし、AI目視レビューの主体・読んだ資料・判断根拠を必須にする | AI/スクリプト出力を無条件に最終判断として扱わない |
| P10 | RAG評価の失敗検出 | OpenAI Evals / evaluation patterns: https://platform.openai.com/docs/guides/evals | 2026-05-21 | grader、regression checks、failure cases | 評価は失敗fixtureを明示し、同じ失敗が再発したら落とす | `script_final_decision_count`、`batch_final_review_count`、`missing_ai_visual_review_trace_count` を監査項目にする | 監査項目を警告だけにしてpassさせない |
| P11 | annotation quality gate | HumanSignal / Label Studio review workflow: https://docs.humansignal.com/guide/quality.html | 2026-05-21 | review queue、ground truth、agreement | annotationはレビュー主体、判断理由、反証や合意を残して品質を担保する | 強いテーマ語を却下する時は `counter_review` を必須にする | 強い候補をスコアや薄さだけで最終却下しない |
| P12 | 生成本文の根拠性 | Microsoft groundedness/relevance evaluators: https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/rag-evaluators | 2026-05-21 | groundedness、relevance、completeness | 生成本文は根拠、関連性、完全性を別々に見る | 本文未完成や本文品質未達は `rejected_*` ではなく `needs_revision` に戻す | 本文を作れないことを素材価値なしと同一視しない |

## 中身の型

| 成果物 | 見出し構成 | 文量 | 命令の粒度 | 例の置き方 | 検証方法 | 失敗時の扱い | 真似しない点 |
|:---|:---|:---|:---|:---|:---|:---|:---|
| スキル本文 | 入口ルール、手順、禁止事項、自己確認 | 入口は短く、詳細は参照資料 | 必須、禁止、例外、完了条件を分ける | 自作の成功例ではなくschemaと合否条件を置く | eval、監査、Final Checker | 未確認は未完了へ戻す | 長文手順を入口に詰め込む |
| RAGレビュー台帳 | 束、原文証跡、span判断、本文品質、重複/却下証拠 | 1行で判断が追える密度 | 機械候補理由と最終判断理由を分ける | JSON schemaで必須欄を固定 | invalid countを0にする | 1件でも欠落したら完了不可 | スコアやクラスタを最終理由にする |
| 本文品質 | 原文、整形本文、使える理由、タグ、出典 | 150〜600字だが自然長 | 主張、理由/背景、具体例/行動示唆を原文内に限定 | 合格/不合格条件を置く | body_quality_review | 短文や水増しはneeds_revision | 150字スレスレの量産 |
| 検索評価 | 代表語、hit数、target id、invalid hit、例外理由 | 全語を短く一覧化 | 1語ごとのpass/failを分ける | 0ヒット語は根拠付き例外だけ許可 | material-rag search + report | search_gap_countが残れば未完了 | 1語でも当たればpass |

## 採用するルール

- `machine_prefilter_reason` と `final_decision_reason` を分ける。
- `final_decision_reason` には、今回読んだ原文と前後文脈に基づく理由だけを書く。
- `approved_verified`、`duplicate`、`rejected_*` の全状態で、読んだ範囲と判断理由を必須にする。
- 本文は150〜600字の範囲だけで合格にしない。原文にある主張、理由または背景、具体例または行動示唆が自然に残っていることを確認する。
- `clean_verbatim` の各文に `body_sentence_alignment` を残し、原文対応がない文を承認しない。
- `approved_verified` はレビュー台帳ゲートを通った `span_decisions` からだけ生成し、`human_review_packet_id`、`span_decision_id`、`reviewed_source_excerpt_hash`、`generated_by_script_only=false` を必須にする。
- `approved_verified`、`duplicate`、`rejected_*` は `review_actor_type=skill_ai_visual_review`、`skill_paths_read`、`pro_evidence_checked_at` があるAI目視レビューだけが出す。
- `script_candidate_scan`、`script_prefilter`、`deterministic_source_scan_with_span_trace` は候補整理だけにし、最終状態ではなく `needs_review` または `needs_revision` に戻す。
- batch source scan の一括 `reviewed_at` は目視完了証跡にしない。
- 強いテーマ語を含む候補を却下する時は `counter_review` を必須にし、使える余地があれば `needs_revision` へ戻す。
- 本文未作成、固定本文リスト未登録、AI整形不足だけを理由に `rejected_*` にせず、使える余地が残る場合は `needs_revision` に戻す。
- 150〜199字の本文は `short_body_justification` を必須にする。
- 代表検索は全代表語ごとに確認し、0ヒット語は原文レビューに基づく例外理由がある時だけ許可する。
- evalはassertionを必須にし、`assertions_total == 0` を評価未実施として失敗にする。

## 採用しないルール

- 承認数を先に決めない。
- 1束から複数素材を強制しない。
- スコア、検索順位、クラスタ、AI候補名だけで最終採否を決めない。
- 固定本文リストの有無で採否を決めない。
- 本文未作成を最終却下理由にしない。
- 本文品質未達を `rejected_*` の最終理由にしない。
- スクリプトが読んだ範囲を集めたことを、AI目視レビュー完了と呼ばない。
- 150字に届かせるための水増しをしない。
- URLだけ、要約だけ、自己作成例だけでプロ事例確認済みにしない。
- 検索が一部だけ当たった状態を完了扱いにしない。

## 今回のRAG品質へ変換したルール

| 監査項目 | 落とす条件 | 根拠 |
|:---|:---|:---|
| `pro_evidence_incomplete_count` | 証拠表に出典、確認日、読んだ範囲、採用/不採用がない | P1, P2 |
| `score_only_final_decision_count` | 最終理由がスコア、検索、クラスタだけ | P4, P5 |
| `machine_only_rejection_count` | 却下理由が機械候補理由だけ | P3, P4 |
| `template_final_reason_reuse_count` | 多数のspanに同じテンプレ最終理由を使い回す | P1, P4 |
| `short_body_without_justification_count` | 150〜199字の本文に短文採用理由がない | P3 |
| `search_gap_count` | 代表検索語が0ヒットで、原文根拠付き例外もない | P6, P7 |
| `zero_assertion_eval_count` | evalにassertionがない | P2, P3 |
| `manual_body_required_count` | 本文未作成や固定本文リスト未登録を理由に最終却下している | P4, P8 |
| `clean_sentence_without_source_count` | 本文の各文に原文対応がない | P3, P4, P8 |
| `approved_without_body_sentence_alignment_count` | 承認素材に文単位の原文対応表がない | P3, P4, P8 |
| `missing_review_gate_trace_count` | `human_review_packet_id`、`span_decision_id`、`reviewed_source_excerpt_hash`、`generated_by_script_only=false` がない | P1, P2, P4, P8 |
| `script_final_decision_count` | `script_candidate_scan` などのスクリプト処理が最終状態を直接出している | P4, P9, P10 |
| `batch_final_review_count` | batch source scan の一括書き出しを最終レビューとして扱っている | P4, P9, P10 |
| `missing_ai_visual_review_trace_count` | 最終状態に `review_actor_type=skill_ai_visual_review`、`skill_paths_read`、`pro_evidence_checked_at` がない | P1, P2, P9, P10 |
| `strong_rejected_without_counter_review_count` | 強いテーマ語を含む候補を反証レビューなしで却下している | P8, P11 |
| `body_issue_final_rejection_count` | 本文未完成や本文品質未達を `rejected_*` として最終却下している | P3, P8, P12 |
