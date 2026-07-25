# 2026-07-25 proposal-writingスキル新設

種別: 設計判断
関連: `skills-archive/2026-07-25-sales-copywriting-qa-retirement/`, `.agent/skills/proposal-writing/`

## 方針（なぜやったか）

旧 `sales-copywriting` 系を復元せず、新規スキル `proposal-writing` として問い合わせフォーム用パートナー提案文の作成範囲を再定義した。
第1弾はWeb制作会社向けGoogleビジネスプロフィール協業提案だけに限定し、Webマーケティング会社・広告代理店向けは未実装とした。
品質は長いランタイム品質ゲートではなく、対象コホート、固定情報順序、固定CTA、一変数A/Bの型で担保する方針にした。
独立QAスキル `proposal-writing-qa` は作らず、スキル作成時の検証はステージングレポートとSkill Checkerへ分離した。

## 実施事項（何をしたか）

- `.agent/skills/proposal-writing/SKILL.md` を新規配置
- `.agent/skills/proposal-writing/references/01-target-web-production-company.md` を新規配置
- `.agent/skills/proposal-writing/references/02-writing-modes.md` を新規配置
- `.agent/skills/proposal-writing/references/03-ab-testing.md` を新規配置
- `.agent/skills/proposal-writing/references/changelog.md` を新規配置
- `.agent/skills/proposal-writing/examples/good-output.md` を新規配置
- `.agent/skills/skill-management/SKILL.md` の現在のスキル一覧へ `proposal-writing/` を追加
- `.agent/skills/skill-management/references/changelog.md` へ追加履歴を追記
- `.agent/skills/README.md` の営業・クライアント対応系一覧へ `proposal-writing/` を追加

## 検証結果

- 配置前に `.agent/skills/proposal-writing` が存在しないことを確認
- ステージング版は品質検証サブエージェント Carver の2回目検証でPASS、正式配置可とされた
- `quality-gate.md`、`proposal-writing-qa`、未実装ターゲット空ファイルは作成していない
- 旧 `sales-copywriting`、`sales-copywriting-qa`、`sales-copywriting-workspace` は復元していない

## 未対応・未検証

- 正式配置後の独立検証は品質検証サブエージェントが行う
- Webマーケティング会社、広告代理店向けの設計は未実装
