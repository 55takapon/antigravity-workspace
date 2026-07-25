# skill-management 変更履歴

- 2026-04-12: 初版作成（スキル散在問題の解決・統一ルール化）
- 2026-04-30: Anthropic公式仕様に準拠したテンプレートに全面改訂（非公式フィールド排除・Progressive Disclosure明文化）
- 2026-05-02: 「タスク実行前のスキル確認フロー（STEP 0）」追加。スキル未読のままデイリーレポートを独自フォーマットで作成したインシデントを受け、構造的な歯止めとして追加
- 2026-05-05: `sales-copywriting`・`sales-copywriting-qa` を一覧に追加
- 2026-05-06: `gbp-post-quality-check` を一覧に追加（iami-kakogawa全件QAの知見から新規作成）
- 2026-05-09: `site-seo-launch` を一覧に追加（WordPress/SWELLサイト本番公開時のSEO設定スキル）
- 2026-05-09: `gbp-review-reply` を一覧に追加（GBP口コミ返信案自動生成スキル）
- 2026-07-07: GBP/MEOスキル大整理。業種別9スキル（beauty/bodywork/education/legal/medical/real-estate/restaurant/retail/service）とpost系3スキル（post-dental-occlusion/post-dental-preventive/post-jetproduce）を廃止し `skills-archive/2026-07-07-gbp-meo-retirement/` へ退避。法規制部分は `gbp-meo-core/references/industry-regulations.md` に、post系固有ルールは各クライアントの knowledge.md に移管。gbp-meo-core を新基準準拠にリファクタ（本体約1,100トークン化・R1〜R7を gbp-monthly-report へ移管・reports/templates を `gbp-clients\_monthly-reports|_report-templates` へ移動しスクリプトのパスを更新）
- 2026-07-17: `daily-report` をv3再建（データソースをAntigravity brain/からClaude Codeセッションへ移行。collector v3.0・新基準SKILL.md・quality-checkとの双方向連携化。詳細は daily-report/references/changelog.md）
- 2026-07-17: `ops-pdca` を廃止し同アーカイブ（`2026-07-17-contact-tools-retirement/`）へ退避。中身が廃止済みcontact-autoのスクリプト群（contact_auto.js / cf7_daily_report.js / skill_learner.js / known_errors.json）のみを前提としており、参照先が全滅していたため。daily-report側からの参照・タスクスケジューラの自動実行はなしを確認済み
- 2026-07-17: `contact-auto` / `form-automation` を廃止（中途半端で使用不可・開発ストップの裁定）し `skills-archive/2026-07-17-contact-tools-retirement/` へ退避。後継として `contact-form-assist` を一覧に追加（正本は `.agent\skills\contact-form-assist`、実行コードは `C:\Users\hangy\.cursor\test\contact-form-assist`、コード置き場側に同名ポインタSKILL.mdを設置）。営業NGキーワード90+は旧contact-autoから `config/ng-keywords.json` へ移植、ブラックリストは中身が空だったため移植せず廃棄
- 2026-06-13: 「憲法」へ縮小改訂。スキル作成は skill-creator、改善は skill-update、検査は skill-checker へ委譲。テンプレート・更新手順セクションを削除し、統一ルール（変更履歴のreferences分離・description 400字目安・2,000トークン上限・グランドファーザー方式）を裁定。一覧に未記載だった gbp-monthly-report / git-backup / idea-inbox / ops-pdca と、新規導入の skill-creator / skill-checker / skill-update を追加
- 2026-07-25: `sales-copywriting-qa` を廃止し `skills-archive/2026-07-25-sales-copywriting-qa-retirement/` へ退避。実行コード・自動化・外部依存がなく、主な役割が旧 `sales-copywriting` の7ブロック構成検査に限定されていたため。参照切れ防止と既決の廃版方針に基づき、`sales-copywriting` も同じ退避単位でアーカイブした。後継スキルはこの時点では未作成・未接続。
