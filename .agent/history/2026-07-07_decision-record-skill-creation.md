# 2026-07-07 decision-recordスキル新設（履歴記録の方式決定）

種別: 設計判断
関連: [2026-07-07 GBP/MEOスキル大整理](../skills-archive/2026-07-07-gbp-meo-retirement/HISTORY.md)

## 方針（なぜやったか）

GBP/MEOスキル大整理の履歴ファイルを残した流れで、ユーザーから「セッション終了時に履歴ファイルを作るスキルを作りたい」と相談を受けた。検討の結果、以下を判断した。

- **採用**: ADR（Architecture Decision Record）方式。破壊的変更・設計判断・インシデントの3類型に該当した時だけ発火するトリガー型
- **却下**: 全セッション一律で履歴を作る方式。理由は (1) 既存の記録システム（daily-report / 各スキルchangelog / git-backup / skill-snapshot）と重複し矛盾の温床になる (2) 成果物作成セッションでは成果物自体が履歴であり、別ファイルはノイズ (3) 誰も読まない書き捨て文書が量産され、重要な記録が埋もれる
- ファイル容量は懸念に当たらない（Markdownで年間数MB規模）。真のコストは検索性と注意力のため、1行索引（INDEX.md）を必須とした
- 記録の信頼性確保のため「検証済み事実のみ記録・未検証は分離」「作成後は不変」をルール化した

## 実施事項（何をしたか）

- 新規作成: `skills/decision-record/SKILL.md`（発火判定→事実収集→記録生成→既存記録連携→自己完了確認の5工程）
- 新規作成: `skills/decision-record/references/01-trigger-judgment.md`（3類型と除外条件の判定基準）
- 新規作成: `skills/decision-record/references/02-record-template.md`（記録テンプレート・命名・索引フォーマット）
- 新規作成: `skills/decision-record/references/changelog.md`、`skills/decision-record/examples/good-output.md`（正常系＝本日の実記録・異常系＝対象外セッション）
- 新規作成: `history/INDEX.md`（1行索引。既存の2026-07-07大整理の記録をシード登録）
- 追記: skill-management「現在のスキル一覧」と skills/README.md に decision-record の行を追加

## 検証結果

- 正常系: 本ファイル自体をテンプレート通りに作成し、INDEX.md への索引行追記まで実施（スキルの想定出力と一致）
- 異常系: 「投稿4本作成のみのセッション」を判定基準に照合し、除外条件1で記録対象外と判定されることを確認
- skill-checker の全項目チェックを実行（結果はセッション報告に記載）

## 未対応・未検証

- 実セッションでの自動発火（descriptionによるトリガー）は次回の破壊的変更セッションで初検証となる
