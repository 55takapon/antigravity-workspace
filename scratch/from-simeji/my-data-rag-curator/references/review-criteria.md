# 目視レビュー基準

## 基本方針

採用判断は、原文と前後文脈を読んで決める。
ツール、検索結果、スコア、候補台帳は補助であり、最終判断ではない。
AIが作った候補名、要約、分類名は、読む場所を見つけるためだけに使う。
承認理由は、必ず原文、前後文脈、素材価値、出典に基づける。
承認素材の数は成果指標ではない。
束レビューでは、全候補spanを確認し、品質基準を満たしたものだけを承認する。
承認0件でも、全spanを読んで理由を残していれば有効なレビュー。
承認数を増やすための分割、薄い素材化、水増しは禁止。
旧レビュー、旧承認集約、既存Markdown、検索結果を現行schemaへ写しただけのものは、原文確認済みではない。
今回のレビューで読んだ transcript 抜粋、読んだ範囲、読んだ日時、`legacy_review_used=false` がないものは、`approved_verified` にできない。

## 採用できる素材

本番RAGへ入れられるのは `approved_verified` だけ。
`approved` は旧状態または仮承認として扱い、再監査が終わるまで本番へ入れない。

`approved_verified` にできるのは、以下をすべて満たす素材だけ。

- `raw_excerpt` が元transcriptに存在する。
- 今回のレビューで `transcript_range_to_read` と前後文脈を読み、`review_basis.transcript_excerpt_read` または同等の原文抜粋が残っている。
- `review_basis.legacy_review_used` が `false` であり、旧レビューや旧承認集約からの変換ではない。
- `review_run_id` と `reviewed_at` があり、どのレビューで承認したか追える。
- `clean_verbatim` が意味を変えていない。
- `clean_verbatim` は改行や空白を除いた見える本文で150〜600字で、単体で投稿・記事・台本・教材の材料になる密度を持つ。
- 口癖、不要反復、未整形語が大量に残っていない。
- 1素材1論点になっている。
- 見える本文が150字未満なら、前後文脈を読んで必要な根拠、理由、具体例を原文から補える場合だけ修正する。補えない場合は採用しない。
- 150字以上でも、抽象語だけ、水増し、原文にない補足、短文の言い換えだけなら不合格。
- 600字超は、主張、体験談、反論、具体例ごとに分割できるか確認する。1000字超は原則分割。
- raw_excerpt が長いのに clean_verbatim が短い場合は、重要情報の取りこぼしがないか `body_quality_review.missing_information_from_raw` に明記する。
- 本文は「主張」「理由または背景」「具体例または行動に落ちる示唆」のうち、原文に存在する要素で構成する。
- 原文に存在しない要素を補って文章を整えてはならない。
- 文字数を満たすために原文にない説明を足していない。
- 150字前後に寄せるのではなく、原文の話として自然な長さで、使える範囲を切り出している。
- 本文未作成は却下理由ではない。原文と前後文脈を読んで素材化できる余地があるなら `needs_revision` に戻す。
- 固定本文リストの有無を採否理由にしない。固定本文リストは本文作成済みの補助であり、採用可否の根拠ではない。
- 150〜199字で採用する場合は、原文と前後文脈を読んだうえで追加すべき有用情報がない理由を `body_quality_review.short_body_justification` に書く。
- 前後文脈を読んでも、話の意図が変わらない。
- 単体で投稿、記事、台本、教材の材料になる。
- `source_context` に前後の流れが残っている。
- `why_useful` に使える理由が具体的に書ける。
- `topic_tags` が内容タグになっている。
- 出典とtimestampで元発話へ戻れる。
- 個人情報、固有事情、危ない表現が安全に処理されている。
- `source_read_evidence` に読んだ範囲と原文一致確認がある。
- `body_quality_review` に `clean_verbatim_chars`、`length_status`、`not_padded`、`not_summary_only`、`grounded_in_raw`、`one_point`、`contains_claim`、`contains_reason_or_context`、`contains_example_or_actionable_detail`、`missing_information_from_raw`、`quality_reason` がある。
- 承認素材IDは今回のレビュー行の `span_decisions` から導出されている。古い `approved_material_spans` のIDリストを固定的に再投入していない。

## 状態ごとの判断基準

| 状態 | 判断基準 |
|:--|:--|
| `approved` | 旧状態または仮承認。現行基準では本番RAGへ入れない |
| `approved_verified` | 原文、前後文脈、本文品質、タグ、出典、安全性を再監査し、現行基準でも合格 |
| `candidate_unreviewed` | 候補化しただけで、まだ原文確認していない |
| `needs_context` | 使えそうだが前後文脈を広げないと判断できない |
| `needs_revision` | 素材価値はあるが、項目不足、整形不足、タグ不足がある |
| `duplicate` | 既存素材と実質同じ。既存素材ID、source/timestamp、同じ主張または同じ文脈の証拠を残し、新規追加せず既存へ紐づける |
| `rejected_noise` | 雑談、言い切り不足、素材価値不足 |
| `rejected_other_theme` | 今回テーマでは使わないが、別テーマ候補として残せる |
| `rejected_out_of_scope_sensitive` | 個人情報、固有事情、危ない事情が強く、素材化しない |

`approved_verified` は、必ず人間が読める採否理由を持つ。
理由が「検索で上に出た」「AIが重要と言った」だけなら不合格。

`duplicate` も、必ず人間が読める重複理由を持つ。
理由が「既存と近い」「スコアが近い」「クラスタが同じ」だけなら不合格。
既存素材IDと、どの発話・主張・文脈が重なるのかを残す。

## 不合格にする素材

- 要約になっている。
- 原文にない補足が混ざっている。
- 原文にない理由、背景、具体例、行動示唆で本文を補っている。
- 原文対応がない文を `clean_verbatim` に入れている。
- 本文未作成、固定本文リスト未登録、AI整形不足だけを理由に `rejected_*` にしている。
- 文脈が消えて、別の意味に見える。
- `raw_excerpt` に近い未整形文を、人間向け本文として出している。
- 1素材に複数テーマや複数主張が混ざっている。
- 80字未満で単体の意味が立たない。
- 150字未満で、前後を足しても単体素材として成立しない。
- 文字数を満たすために意味の薄い言い換えや重複文を足している。
- 150字以上でも、主張だけ、一般論だけ、または短文の言い換えだけで、素材として使える密度がない。
- 150〜199字で、短文のまま採用できる理由が `short_body_justification` にない。
- raw_excerpt が長いのに clean_verbatim が短く、重要情報の取りこぼし確認が `body_quality_review` にない。
- 1束から複数出すために、独立していない発話を無理に切り出している。
- 1000字超で分割検討がされていない。
- 「なんか」「えっと」「みたいな感じ」「なんだろう」などの未整形語が目立つ。
- タグが媒体名だけになっている。
- 使える理由が空、または抽象的すぎる。
- 出典、timestamp、source_id がない。
- 未確認なのに `approved_verified` と書かれている。
- 旧レビューや旧承認集約を現行schemaへ変換しただけで `approved_verified` と書かれている。
- 完了検査が承認数の固定値一致だけを根拠にしている。

## 束レビューで不合格にする状態

- 1回の目視分類が40束を超えているのに分割していない。
- 80束以上、または数百束を一括で採否確定している。
- 束の中に、別 `source_id`、離れたtimestamp、別文脈が混ざっている。
- `transcript_range_to_read` がなく、どこを読んだか分からない。
- `representative_raw_excerpt` だけで、前後文脈を読んだ証跡がない。
- `duplicate` に既存素材IDと重複理由がない。
- `rejected_other_theme` に、どの別テーマへ回すべきかの理由がない。
- 機械スコア、検索順位、クラスタ名だけで採否を決めている。
- `all_candidate_spans_checked` がなく、束内の候補spanを全て見たか分からない。
- `span_decisions` がなく、承認0件、1件、複数件の判断理由が追えない。
- `review_basis.transcript_excerpt_read` または同等の今回読んだ原文抜粋がない。
- `review_basis.legacy_review_used=false` がない、または旧レビュー変換を示している。
- `review_run_id` と `reviewed_at` がなく、いつのレビューで採否を決めたか分からない。
- 承認数の目標、複数承認の義務、1束1素材の義務がある。
- 承認素材に `source_read_evidence` または `body_quality_review` がない。
- 承認数を増やす目的で本文を水増ししている。

## 本文の役割

`raw_excerpt` は原文確認用。
読みづらくても、元発話に戻るために残す。

`clean_verbatim` は人間向け・RAG向け本文。
口癖や不要反復を落とし、意味を変えず、使える話素材として読める状態にする。
ただし、原文にない説明、結論、具体例を足してはならない。

`clean_verbatim` の合格は、文字数だけでは決めない。
`body_quality_review` では次を全て確認する。

- `clean_verbatim_chars` が改行や空白を除いた見える本文文字数と一致している。
- `length_status` が `150-600` である。
- `not_padded` が true である。
- `not_summary_only` が true である。
- `grounded_in_raw` が true である。
- `one_point` が true である。
- `contains_claim` が true である。
- `contains_reason_or_context` が true である。
- `contains_example_or_actionable_detail` が true である。
- `missing_information_from_raw` に「なし」または取りこぼしていない理由が書かれている。
- `quality_reason` に、原文にある要素だけで本文化できている理由が書かれている。
- `professional_body_reason` に、原文のどの主張、背景、具体例、行動示唆を本文に残したかが書かれている。
- `body_sentence_alignment` に、`clean_verbatim` の各文、対応する原文、timestamp、対応理由が文単位で書かれている。
- `body_sentence_alignment` は、本文1文と対応する原文1箇所または近接する前後文脈で照合する。広い原文範囲を貼って「対応している」と書くだけでは不合格。
- 本文の主要語、例: `PDCA`、`改善`、`行動量`、`時間短縮`、`アウトプット`、`失敗`、`経験値`、`成長速度` が、対応する `source_quote` にも確認できる。
- `no_source_unbacked_addition` が true である。
- `natural_length_not_threshold_padding` が true である。
- `clean_sentence_without_source_count` が0である。
- 150〜199字の場合は `short_body_justification` に、追加すべき情報がない理由が書かれている。
- `clean_verbatim` に「そうです」「であとは」「でまぁ」「という形」「やってる」「されてる」「ですよです」「くださいね」などの話し言葉残りや、不自然な文の切れ端が残っていない。

`body_sentence_alignment` は、本文1文ごとに次の形で残す。

```json
{
  "clean_sentence": "本文の1文",
  "source_type": "claim | reason_or_context | example_or_action",
  "source_quote": "対応する原文または今回読んだ前後文脈",
  "timestamp_range": "00:00:00-00:00:00",
  "alignment_reason": "この文が原文のどの意味を保っているか"
}
```

## 採否理由の役割

採否理由は、機械候補理由と最終判断理由を分ける。

- `machine_prefilter_reason`: スコア、検索、クラスタ、テーマ語など、読む順番を決める補助理由。
- `final_decision_reason`: 今回読んだ原文と前後文脈に基づく最終理由。

`final_decision_reason` は、次の形で書く。

- `approved_verified`: 原文のどの主張、理由、具体例、行動示唆が1素材1論点として成立したかを書く。
- `duplicate`: 既存素材ID、同じ主張または文脈、source/timestamp比較を書く。
- `rejected_noise`: 前後文脈まで読んでも、単体素材として使える主張や理由がないことを書く。
- `rejected_other_theme`: 今回テーマではなく、どの別テーマまたは文脈に寄っているかを書く。
- `rejected_out_of_scope_sensitive`: 安全に汎用化できない固有事情や危険表現を書く。

次の理由は最終判断理由として不合格にする。

- `scoreが18未満`
- `検索スコアが低い`
- `クラスタが近い`
- `既存と近い`
- `テーマ語には反応している`
- `AIが重要と言った`
- 同じ文章を多数のspanへ使い回しているテンプレート理由

## タグ基準

タグは媒体名ではなく内容で付ける。

良いタグ:

- `AI活用`
- `仕組み化`
- `差別化`
- `中長期`
- `反論`
- `体験談`
- `上流工程`

悪いタグ:

- `x_post`
- `article`
- `line`
- `discord`
- `video_script`

媒体ごとの文章化は、下流スキルで行う。
