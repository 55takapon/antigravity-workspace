# skill-management 変更履歴

- 2026-04-12: 初版作成（スキル散在問題の解決・統一ルール化）
- 2026-04-30: Anthropic公式仕様に準拠したテンプレートに全面改訂（非公式フィールド排除・Progressive Disclosure明文化）
- 2026-05-02: 「タスク実行前のスキル確認フロー（STEP 0）」追加。スキル未読のままデイリーレポートを独自フォーマットで作成したインシデントを受け、構造的な歯止めとして追加
- 2026-05-05: `sales-copywriting`・`sales-copywriting-qa` を一覧に追加
- 2026-05-06: `gbp-post-quality-check` を一覧に追加（iami-kakogawa全件QAの知見から新規作成）
- 2026-05-09: `site-seo-launch` を一覧に追加（WordPress/SWELLサイト本番公開時のSEO設定スキル）
- 2026-05-09: `gbp-review-reply` を一覧に追加（GBP口コミ返信案自動生成スキル）
- 2026-07-07: GBP/MEOスキル大整理。業種別9スキル（beauty/bodywork/education/legal/medical/real-estate/restaurant/retail/service）とpost系3スキル（post-dental-occlusion/post-dental-preventive/post-jetproduce）を廃止し `skills-archive/2026-07-07-gbp-meo-retirement/` へ退避。法規制部分は `gbp-meo-core/references/industry-regulations.md` に、post系固有ルールは各クライアントの knowledge.md に移管。gbp-meo-core を新基準準拠にリファクタ（本体約1,100トークン化・R1〜R7を gbp-monthly-report へ移管・reports/templates を `gbp-clients\_monthly-reports|_report-templates` へ移動しスクリプトのパスを更新）
- 2026-06-13: 「憲法」へ縮小改訂。スキル作成は skill-creator、改善は skill-update、検査は skill-checker へ委譲。テンプレート・更新手順セクションを削除し、統一ルール（変更履歴のreferences分離・description 400字目安・2,000トークン上限・グランドファーザー方式）を裁定。一覧に未記載だった gbp-monthly-report / git-backup / idea-inbox / ops-pdca と、新規導入の skill-creator / skill-checker / skill-update を追加
