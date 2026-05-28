# 出力例

このファイルは、出力形式の確認用サンプルです。
自作サンプルを「プロ事例」や「成功事例」として扱わない。
実作業では必ず元transcript、既存素材、レビュー台帳の実物で確認する。
品質比較の正本は、既存の高品質テーマ実素材とする。

## 実データ例1: approved_verified の完全例

### 確認した実物

- 素材台帳: `hinata/marketing_workspace/元データ/loom/material_assets/material_assets.jsonl`
- material_id: `loom_0023455fd2394649aa1988c61e87cd79_1772440237_choose_centerpin_before_running_pdca_0001`
- review_run_id: `fresh_improvement_current_pass_redo_20260519`
- 出典: `transcripts/loom_0023455fd2394649aa1988c61e87cd79_1772440237.md / 00:05:51-00:07:58`

### 出力

```json
{
  "material_id": "loom_0023455fd2394649aa1988c61e87cd79_1772440237_choose_centerpin_before_running_pdca_0001",
  "review_status": "approved_verified",
  "clean_verbatim": "課題がたくさん出ている時は、全部を並べるよりも、自分はいま何をするのが一番センターピンなのか、何を変えれば状況が改善するのかを2つ3つに絞った方がいいです。\n\n今後どうなりたいのかを考えたうえで、今やるべきことを決める。そこに対してPDCAが回っているかが一番大事です。細かいPDCAも必要ですが、最初は大枠から始めて、どれが優先順位が高くて、どれがすぐ結果につながりそうかを見て進めると、タスクが雑になりにくくなります。",
  "review_basis": {
    "fresh_transcript_review": true,
    "legacy_review_used": false,
    "source_aggregate_reused": false,
    "fixed_approved_count_used": false
  },
  "source_read_evidence": {
    "range_read": "00:05:47-00:08:07",
    "range_extended": true,
    "read_basis": "current_passレビューで元transcript範囲と前後文脈を読み、今回のstrict再投入で同じ読了抜粋を再照合した。"
  },
  "body_quality_review": {
    "clean_verbatim_chars": 209,
    "length_status": "150-600",
    "grounded_in_raw": true,
    "not_padded": true,
    "not_summary_only": true,
    "one_point": true,
    "contains_claim": true,
    "contains_reason_or_context": true,
    "contains_example_or_actionable_detail": true,
    "missing_information_from_raw": "なし"
  },
  "completion_blockers": []
}
```

## 実データ例2: 旧レビュー変換を止める例

### 確認した実物

- コマンド: `python3 hinata/skills/reverse-knowledge-builder/scripts/strict_improvement_rag_redo.py build-strict-reviews`
- 結果: exit code 1
- 理由: 旧レビューと旧 `approved_material_spans` の現行schema変換は、fresh transcript review 条件を満たさない。

### 出力

```json
{
  "legacy_source_conversion_blocked": {
    "reason": "旧レビュー/旧approved_material_spansを現行schemaへ変換するだけでは、my-data-rag-curatorのfresh transcript review条件を満たさない。",
    "source_aggregate_path": "改善_振り返り_行動修正.redo_approved_material_spans_20260517.json",
    "source_review_glob": "改善_振り返り_行動修正.formal_redo_manual_review_20260517_round*.json",
    "required_next_step": "full_redo_review_queueから今回のreview_run_idで元transcriptを読み直す。"
  }
}
```

## 補足

schemaだけを確認する場合は、`references/output-format.md` を正本にする。
このファイルには、実データで確認した出力例だけを置く。
