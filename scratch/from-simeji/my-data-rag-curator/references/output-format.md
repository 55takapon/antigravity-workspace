# 出力フォーマット

## 進捗チェックリスト

作業を始めたら先に出し、完了した工程だけ更新する。

```markdown
## 進捗

- [x] 現状確認
- [ ] 既存承認済み素材の再監査
- [ ] 未確認候補の目視分類
- [ ] 使える発話の素材化
- [ ] RAG反映と検索確認
- [ ] 完成可否の報告
```

## 強制schema

再監査レポート、目視分類台帳、import対象素材には、次のブロックを必ず残す。
`approved_verified` の場合、`completion_blockers` は空配列でなければならない。
`duplicate` の場合、`duplicate_material_id` と `same_claim_or_context` は必須。
`rejected` の場合も、読んだ範囲と却下理由は必須。

```json
{
  "review_run_id": "fresh_review_YYYYMMDD_round001",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "human_review_packet_id": "review_run_id:bundle_id",
  "reviewed_source_excerpt_hash": "sha256",
  "generated_by_script_only": false,
  "review_actor_type": "skill_ai_visual_review",
  "skill_paths_read": [
    ".agents/skills/my-data-rag-curator/SKILL.md",
    ".agents/skills/my-data-rag-curator/references/review-gate-contract.md",
    ".agents/skills/my-data-rag-curator/references/pro-rag-quality-evidence.md"
  ],
  "pro_evidence_checked_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "review_basis": {
    "fresh_transcript_review": true,
    "legacy_review_used": false,
    "transcript_excerpt_read": "今回読んだ原文抜粋",
    "source_aggregate_reused": false,
    "fixed_approved_count_used": false
  },
  "source_read_evidence": {
    "transcript_path": "path",
    "range_read": "00:00:00-00:00:00",
    "range_extended": true,
    "read_basis": "候補前後を読み、主張・理由・具体例のつながりを確認"
  },
  "span_decisions": [
    {
      "span_id": "span_001",
      "span_decision_id": "review_run_id:bundle_id:span_001",
      "human_review_packet_id": "review_run_id:bundle_id",
      "reviewed_source_excerpt_hash": "sha256",
      "generated_by_script_only": false,
      "review_actor_type": "skill_ai_visual_review",
      "skill_paths_read": [
        ".agents/skills/my-data-rag-curator/SKILL.md",
        ".agents/skills/my-data-rag-curator/references/review-gate-contract.md",
        ".agents/skills/my-data-rag-curator/references/pro-rag-quality-evidence.md"
      ],
      "pro_evidence_checked_at": "YYYY-MM-DDTHH:MM:SS+09:00",
      "raw_range": "00:00:00-00:00:00",
      "decision": "approved_verified",
      "machine_prefilter_reason": "スコア、検索、クラスタなど候補化の理由。最終判断には使わない",
      "final_decision_reason": "今回読んだ原文と前後文脈に基づく最終理由",
      "decision_reason": "final_decision_reasonと同じ内容。旧ツール互換のため残す",
      "decision_basis_type": "fresh_transcript_review",
      "manual_source_evidence": {
        "quoted_or_summarized_basis": "判断根拠になった原文内容",
        "context_checked": "前後文脈で確認したこと",
        "why_this_decision": "なぜ承認/重複/却下か"
      },
      "decision_not_by_score": true,
      "template_reason_reuse_checked": true,
      "material_id": "material_id_or_null"
    }
  ],
  "usable_span_count": 1,
  "all_usable_spans_extracted": true,
  "body_quality_review": {
    "clean_verbatim_chars": 0,
    "length_status": "150-600",
    "not_padded": true,
    "not_summary_only": true,
    "grounded_in_raw": true,
    "one_point": true,
    "contains_claim": true,
    "contains_reason_or_context": true,
    "contains_example_or_actionable_detail": true,
    "missing_information_from_raw": "なし",
    "quality_reason": "原文にある主張・理由・具体例だけで本文化できている",
    "professional_body_reason": "原文のどの主張・背景・具体例・行動示唆が本文に残っているか",
    "body_sentence_alignment": [
      {
        "clean_sentence": "本文の1文",
        "source_type": "claim | reason_or_context | example_or_action",
        "source_quote": "対応する原文または今回読んだ前後文脈",
        "timestamp_range": "00:00:00-00:00:00",
        "alignment_reason": "この文の主要語と意味が原文のどこに対応しているか"
      }
    ],
    "clean_sentence_without_source_count": 0,
    "short_body_justification": null,
    "no_source_unbacked_addition": true,
    "natural_length_not_threshold_padding": true
  },
  "duplicate_evidence": {
    "duplicate_material_id": null,
    "same_claim_or_context": null,
    "evidence_reason": null,
    "duplicate_source_evidence": null
  },
  "completion_blockers": []
}
```

`review_basis` の注意:

- `legacy_review_used=true`、`source_aggregate_reused=true`、`fixed_approved_count_used=true` のどれかがある行は、完成扱いにしない。
- 旧レビューや旧承認集約を見た場合でも、今回の原文読了抜粋がなければ `approved_verified` にしない。
- `review_run_id` と `reviewed_at` がない行は、どのレビューで承認したか追えないため未完了に戻す。
- `human_review_packet_id`、`span_decision_id`、`reviewed_source_excerpt_hash`、`generated_by_script_only=false` がない承認は、レビュー台帳を通っていないため未完了に戻す。
- `review_actor_type=skill_ai_visual_review`、`skill_paths_read`、`pro_evidence_checked_at` がない最終状態は、AI目視レビューの実行証跡がないため未完了に戻す。
- `review_actor_type=script_candidate_scan` の行は候補scanであり、`needs_review` または `needs_revision` に止める。
- `body_sentence_alignment.timestamp_range` は対応quoteの実timestampにする。素材timestampの流用は不可。

## 再監査レポート

既存承認済み素材を見直した結果を残す。

```json
{
  "theme": "対象テーマ",
  "checked_count": 0,
  "approved_verified_count": 0,
  "legacy_approved_count": 0,
  "needs_revision_count": 0,
  "duplicate_count": 0,
  "rejected_count": 0,
  "missing_source_read_evidence_count": 0,
  "missing_body_quality_review_count": 0,
  "missing_span_decisions_count": 0,
  "missing_all_usable_spans_extracted_count": 0,
  "items": [
    {
      "material_id": "material_id",
      "source_id": "source_id",
      "status": "approved_verified",
      "raw_excerpt_found": true,
      "meaning_preserved": true,
      "context_ok": true,
      "clean_body_ok": true,
      "one_point_ok": true,
      "length_status": "150-600",
      "tags_ok": true,
      "safety_ok": true,
      "source_read_evidence": {
        "transcript_path": "transcripts/source.md",
        "range_read": "00:00:00-00:01:00",
        "range_extended": true,
        "read_basis": "候補前後を読み、原文一致と文脈を確認"
      },
      "review_run_id": "fresh_review_YYYYMMDD_round001",
      "reviewed_at": "YYYY-MM-DDTHH:MM:SS+09:00",
      "review_basis": {
        "fresh_transcript_review": true,
        "legacy_review_used": false,
        "transcript_excerpt_read": "今回読んだ原文抜粋",
        "source_aggregate_reused": false,
        "fixed_approved_count_used": false
      },
      "body_quality_review": {
        "clean_verbatim_chars": 220,
        "length_status": "150-600",
        "not_padded": true,
        "not_summary_only": true,
        "grounded_in_raw": true,
        "one_point": true,
        "contains_claim": true,
        "contains_reason_or_context": true,
        "contains_example_or_actionable_detail": true,
        "missing_information_from_raw": "なし",
        "quality_reason": "原文の主張、背景、行動示唆だけで本文化できている",
        "professional_body_reason": "原文の原因説明、背景、次の行動示唆を本文に残している",
        "short_body_justification": null,
        "no_source_unbacked_addition": true,
        "natural_length_not_threshold_padding": true
      },
      "span_decisions": [
        {
          "span_id": "span_001",
          "raw_range": "00:00:00-00:01:00",
          "decision": "approved_verified",
          "machine_prefilter_reason": "候補化された理由。最終判断には使わない",
          "final_decision_reason": "原文と前後文脈で1素材1論点として成立",
          "decision_reason": "原文と前後文脈で1素材1論点として成立",
          "decision_basis_type": "fresh_transcript_review",
          "manual_source_evidence": {
            "quoted_or_summarized_basis": "判断根拠になった原文内容",
            "context_checked": "前後文脈で確認したこと",
            "why_this_decision": "なぜこの状態にしたか"
          },
          "decision_not_by_score": true,
          "template_reason_reuse_checked": true,
          "material_id": "material_id"
        }
      ],
      "usable_span_count": 1,
      "all_usable_spans_extracted": true,
      "duplicate_evidence": {
        "duplicate_material_id": null,
        "same_claim_or_context": null,
        "evidence_reason": null
      },
      "completion_blockers": [],
      "decision_reason": "原文・文脈・本文品質・タグ・出典が揃っている"
    }
  ]
}
```

## 目視分類台帳

未確認候補の採否理由を残す。
束は読む単位であり、出力数の上限でもノルマでもない。
1束から承認0件、1件、複数件のどれになってもよい。
必要なのは、束内の候補spanを全て確認し、各spanの判断理由を残すこと。

```json
{
  "bundle_id": "bundle_id",
  "candidate_ids": ["candidate_id"],
  "source_id": "source_id",
  "timestamp_start": "00:00:00",
  "timestamp_end": "00:00:00",
  "theme_codes": ["内容タグ"],
  "review_status": "approved_verified",
  "decision_reason": "投稿や台本の材料として使える発話が原文にあり、前後文脈も成立している",
  "machine_prefilter_reason": "束を読む候補にした理由。最終判断には使わない",
  "final_decision_reason": "今回読んだ原文と前後文脈に基づく最終理由",
  "decision_basis_type": "fresh_transcript_review",
  "manual_source_evidence": {
    "quoted_or_summarized_basis": "判断根拠になった原文内容",
    "context_checked": "前後文脈で確認したこと",
    "why_this_decision": "なぜ承認/重複/却下か"
  },
  "decision_not_by_score": true,
  "template_reason_reuse_checked": true,
  "review_run_id": "fresh_review_YYYYMMDD_round001",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "review_basis": {
    "fresh_transcript_review": true,
    "legacy_review_used": false,
    "transcript_excerpt_read": "今回読んだ原文抜粋",
    "source_aggregate_reused": false,
    "fixed_approved_count_used": false
  },
  "source_read_evidence": {
    "transcript_path": "path/to/transcript.md",
    "range_read": "00:00:00-00:01:20",
    "range_extended": true,
    "read_basis": "候補範囲に加えて前後を読み、主張・理由・具体例のつながりを確認"
  },
  "span_decisions": [
    {
      "span_id": "span_001",
      "raw_range": "00:00:10-00:00:50",
      "decision": "approved_verified",
      "machine_prefilter_reason": "候補化された理由。最終判断には使わない",
      "final_decision_reason": "原文と前後文脈で1素材1論点として成立する",
      "decision_reason": "原文と前後文脈で1素材1論点として成立する",
      "decision_basis_type": "fresh_transcript_review",
      "manual_source_evidence": {
        "quoted_or_summarized_basis": "判断根拠になった原文内容",
        "context_checked": "前後文脈で確認したこと",
        "why_this_decision": "なぜ承認/重複/却下か"
      },
      "decision_not_by_score": true,
      "template_reason_reuse_checked": true,
      "material_id": "material_id_or_null"
    }
  ],
  "usable_span_count": 1,
  "all_usable_spans_extracted": true,
  "approved_material_count": 1,
  "duplicate_evidence": {
    "duplicate_material_id": null,
    "same_claim_or_context": null,
    "evidence_reason": null,
    "duplicate_source_evidence": null
  },
  "completion_blockers": []
}
```

`rejected_*` の必須欄:

```json
{
  "rejection_evidence_type": "not_theme | insufficient_density_after_context | noise | sensitive | duplicate_context",
  "machine_prefilter_reason": "候補化された機械的理由。最終理由ではない",
  "final_decision_reason": "原文を読んだ上で、なぜ素材化しないか",
  "decision_not_by_score": true,
  "manual_source_evidence": {
    "quoted_or_summarized_basis": "却下判断に使った原文内容",
    "context_checked": "前後文脈で確認したこと",
    "why_this_decision": "なぜ却下か"
  }
}
```

`needs_revision` の必須欄:

```json
{
  "decision": "needs_revision",
  "revision_reason_type": "body_required | body_alignment_missing | source_context_required",
  "machine_prefilter_reason": "候補化された機械的理由。最終理由ではない",
  "final_decision_reason": "原文と前後文脈を読んだうえで、なぜ未完成へ戻すか",
  "decision_not_by_score": true,
  "manual_source_evidence": {
    "quoted_or_summarized_basis": "再作業判断に使った原文内容",
    "context_checked": "前後文脈で確認したこと",
    "why_this_decision": "なぜ却下ではなく要修正か"
  },
  "completion_blockers": [
    "needs_revision が残るため本番投入不可"
  ]
}
```

本文未作成、固定本文リスト未登録、AI整形不足だけを理由に `rejected_*` にしてはならない。
使える余地が残る場合は `needs_revision` とし、完了報告では残件として扱う。
`body_sentence_alignment` は本文1文ごとに行い、広い原文範囲を貼るだけでは合格にしない。
本文の主要語が `source_quote` 側にない場合、または意味が推測でつながっているだけの場合は `needs_revision` に戻す。
`clean_verbatim` に未整形の話し言葉、文の切れ端、不自然な接続が残る場合も `approved_verified` にしない。

## 候補束台帳

候補を束ねた時点では、まだ承認ではない。
束は読む順番を整理するためのものなので、どこを読んだか、なぜ同じ束にしたかを残す。

```json
{
  "theme": "対象テーマ",
  "round_id": "round_001",
  "bundle_count_in_round": 12,
  "normal_limit_ok": true,
  "exception_reason": null,
  "bundles": [
    {
      "bundle_id": "bundle_id",
      "candidate_ids": ["candidate_id"],
      "source_id": "source_id",
      "timestamp_start": "00:00:00",
      "timestamp_end": "00:00:00",
      "topic_codes": ["内容タグ"],
      "representative_raw_excerpt": "候補の代表原文",
      "transcript_range_to_read": "00:00:00-00:00:00",
      "related_approved_material_ids": ["material_id"],
      "bundle_reason": "同じ動画の近い時間で、主張に対する理由と具体例が続いているため",
      "review_run_id": null,
      "reviewed_at": null,
      "review_basis": {
        "fresh_transcript_review": false,
        "legacy_review_used": false,
        "transcript_excerpt_read": null,
        "source_aggregate_reused": false,
        "fixed_approved_count_used": false
      },
      "all_usable_spans_extracted": false,
      "span_decisions": [],
      "approved_material_count": 0,
      "review_status": "candidate_unreviewed",
      "decision_reason": null
    }
  ]
}
```

束数の扱い:

- 8〜24束: 標準。
- 25〜30束: 通常上限内。
- 31〜40束: 例外理由を書く。
- 40束超: 分割し、採否確定しない。
- 80束以上、数百束一括: 無効扱いにし、再監査へ戻す。

## 承認素材

承認素材を作る場合は、素材ごとに次を追加する。
本文は改行や空白を除いた見える本文で150〜600字とし、主張、理由または背景、具体例または行動示唆が原文根拠内にある状態にする。

```json
{
  "material_id": "material_id",
  "review_status": "approved_verified",
  "clean_verbatim": "150〜600字の本文",
  "review_run_id": "fresh_review_YYYYMMDD_round001",
  "reviewed_at": "YYYY-MM-DDTHH:MM:SS+09:00",
  "review_basis": {
    "fresh_transcript_review": true,
    "legacy_review_used": false,
    "transcript_excerpt_read": "今回読んだ原文抜粋",
    "source_aggregate_reused": false,
    "fixed_approved_count_used": false
  },
  "source_read_evidence": {
    "transcript_path": "path/to/transcript.md",
    "range_read": "00:00:00-00:01:20",
    "range_extended": true,
    "read_basis": "候補前後を読み、原文一致と文脈を確認"
  },
  "body_quality_review": {
    "clean_verbatim_chars": 260,
    "length_status": "150-600",
    "not_padded": true,
    "not_summary_only": true,
    "grounded_in_raw": true,
    "one_point": true,
    "contains_claim": true,
    "contains_reason_or_context": true,
    "contains_example_or_actionable_detail": true,
    "missing_information_from_raw": "なし",
    "quality_reason": "原文にある主張・理由・具体例だけで本文化できている",
    "body_sentence_alignment": [
      {
        "clean_sentence": "本文の1文",
        "source_type": "claim | reason_or_context | example_or_action",
        "source_quote": "対応する原文または今回読んだ前後文脈",
        "timestamp_range": "00:00:00-00:00:00",
        "alignment_reason": "この文の主要語と意味が原文のどこに対応しているか"
      }
    ],
    "clean_sentence_without_source_count": 0
  },
  "duplicate_evidence": {
    "duplicate_material_id": null,
    "same_claim_or_context": null,
    "evidence_reason": null
  },
  "completion_blockers": []
}
```

`duplicate` の場合は、次を必須にする。

```json
{
  "decision": "duplicate",
  "duplicate_evidence": {
    "duplicate_material_id": "material_id",
    "same_claim_or_context": "same_claim",
    "evidence_reason": "既存素材と同じ主張を同じsource近辺で話している"
  }
}
```

## 未完了報告

完成と言えない時は、必ず未完了として報告する。

```markdown
## 結論

まだ完成ではありません。

## 確認できたこと

- 既存承認済み素材: 〇件再監査済み
- 未確認候補: 〇件中〇件分類済み
- 本番RAGへ入れた approved_verified 素材: 〇件
- 旧 approved のまま残っている素材: 〇件

## まだ残っていること

- 未確認候補: 〇件
- `needs_context`: 〇件
- `needs_revision`: 〇件
- `source_read_evidence` 欠落: 〇件
- `body_quality_review` 欠落: 〇件
- `span_decisions` 欠落: 〇件
- `all_usable_spans_extracted` 欠落: 〇件

## 残リスク

未確認候補の中に、本番級素材が残っている可能性があります。
そのため、網羅完了とは言えません。
旧 `approved` は再監査前なので、本番Knowledgeへは入れていません。
```

## 完成報告

完成と言える時だけ使う。

```markdown
## 結論

対象テーマのマイデータRAGは、現行基準で完成扱いにできます。

## 確認できたこと

- 既存承認済み素材の再監査完了
- 未確認候補の目視分類完了
- 全レビュー行に `span_decisions` がある
- 全レビュー行に `all_usable_spans_extracted` または `all_candidate_spans_checked` がある
- 承認素材に `source_read_evidence` と `body_quality_review` がある
- `invalid_missing_body_quality_review`、`invalid_missing_span_decisions`、`invalid_duplicate_evidence_missing` が0
- 承認数を目標にした出力制御がない
- 本番RAGへ入っているのは `approved_verified` のみ
- 対象外ID差分0
- 検索評価合格
- 代表検索で必要素材が返る

## 残リスク

残リスクなし、または残件と影響が説明済み。
```
