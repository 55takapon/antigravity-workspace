---
name: skill-update
description: >-
  既存スキル改善専用。description・発火条件・references・examples・knowledge・品質基準・チェック項目の修正、skill-creator/skill-checker等の改善、「このスキル改善して」「精度上げて」「発火しない」、cron実行で必ず使用。旧版比較・再評価・修正済みスキルを出す。
metadata:
  hermes:
    requires:
      bins:
        - python3
---

# Skill Update

既存スキルを評価し、改善が有効な場合だけ安全に修正する。
cron 実行の保存物だけは `skill-update/.runtime/` に集約すること。

## 配置とパス解決

正式配置先は `C:\Users\hangy\.codex\skills\skill-update` とする。
コマンドを実行する時は、必ずこのスキルのルートディレクトリを作業ディレクトリにし、`python3 scripts/...` の相対パスで実行する。
`common-skills/skill-update/...` のような旧配置前提のパスを新規実行に使ってはならない。
対象スキルは `.codex/skills`、`CODEX_HOME/skills`、既存リポジトリ内の `common-skills`、`.agent/skills`、`.agents/skills` から探す。

クライアント案件、GBP、投稿、レビュー、Web制作、広告、提案文などクライアント固有のナレッジが改善判断に必要な場合は、[references/client-knowledge.md](references/client-knowledge.md) をこの工程で必ず読むこと。

cron の基本ルール:
- `[cron:` を含むメッセージ、または次の定型文を cron 実行として扱う
  - `必ず skill-update の全ステップを自動実行すること。`
  - `skills/skill-update/SKILL.md を読み、feedback日次レビューモードだけを実行してください。`
  - `skills/skill-update/SKILL.md を読み、自動修正モードだけを実行してください。`
- 対象スキルを会話から推測してはならない
- 通常の sweep は `automation/targets.json` の `enabled=true` だけを処理する
- `automation/evals/*.json` は通常の手動改善では使わず、cron 固定対象の評価ケースだけに使う
- 自動修正は `automation/auto-fix-policy.json` を読み、原則すべてのスキルを候補にしつつ、`denylist / manual_only / high_risk` を必ず優先する
- feedback 収集は、全ツール共通で「前回以降の新しい分だけ読む」
- 保存場所がない、最近の記録がない、新しい分がない場合は即スキップする

cron のモード分岐:
- `必ず skill-update の全ステップを自動実行すること。` の時だけ、通常の sweep を行う
- `feedback日次レビューモードだけ` の時は、`collect-feedback`、`build-feedback-candidates`、`build-feedback-proposals`、`render-feedback-announcement` を順番に行う
- `自動修正モードだけ` の時は、`select-fix-candidate`、`create-rollback-point`、修正、`apply-fix`、`verify-fix`、必要なら `rollback-fix`、最後に `render-fix-report` を行う
- 通常の sweep では、最初に `python3 scripts/automation_manager.py validate-targets` と `python3 scripts/automation_manager.py prepare-sweep` を必ず実行する
- 通常の sweep では、存在しない補助コマンド名を作ってはならない。`run-sweep` のような未定義コマンドは使用禁止
- feedback 系では `prepare-sweep`、`iteration-N/` 生成、自動修正を行ってはならない
- feedback日次レビューモードでは、`render-feedback-announcement` の出力をそのまま返し、要約や言い換えをしてはならない
- 自動修正モードでは、`python3 scripts/automation_manager.py select-fix-candidate --policy automation/auto-fix-policy.json` を最初に実行し、候補がなければ `HEARTBEAT_OK` を返して終わる
- 自動修正モードでは、`select-fix-candidate` は固定の `targets.json` だけを見て選んではならない。`auto-fix-policy.json` で許可されたスキル全体から1件を選ぶ
- 自動修正モードでは、候補がある時だけ `python3 scripts/automation_manager.py create-rollback-point --selection <selection.json>` を実行し、戻しポイントを作ってから修正に進む
- 自動修正モードでは、修正後に `python3 scripts/automation_manager.py apply-fix --rollback <rollback.json>` と `python3 scripts/automation_manager.py verify-fix --rollback <rollback.json>` を必ず実行する
- 自動修正モードでは、補助コマンドが失敗した時に `timeout`、`gateway closed` などの一時失敗だけは、`python3 scripts/automation_manager.py decide-retry --rollback <rollback.json> --message "<失敗文面>" --policy automation/auto-fix-policy.json` で判定し、同じ run 内で最大3回まで再試行してよい
- 自動修正モードでは、構文エラー、許可外変更、ゲート不許可、benchmark 悪化などの致命失敗は1回で止め、`python3 scripts/automation_manager.py rollback-fix --rollback <rollback.json>` でそのスキルだけ元に戻す
- 自動修正モードでは、3回再試行しても直らない場合は、そのスキルだけ元に戻す
- 自動修正モードでは、最後に `python3 scripts/automation_manager.py render-fix-report --selection <selection.json> --rollback <rollback.json> --apply <apply_result.json> --verify <verify_result.json>` を実行し、その出力をそのまま返す
- `skill-update/SKILL.md` を読んでいる時は、補助スクリプトを必ず `python3 scripts/...` で実行する
- 補助スクリプトが1つでも失敗した場合は、成功扱いにしてはならない。`HEARTBEAT_OK` を返して隠してはならない
- cron の feedback モードでは、上記の補助スクリプト実行にユーザー確認は不要。承認待ちの文章を返してはならない
- 自動修正モードでは、対象スキル以外を戻してはならない

実行前に必ず以下を読むこと:
- [references/workflow.md](references/workflow.md) — 改善ループ全体
- [references/auto-fix-gates.md](references/auto-fix-gates.md) — 自動修正ゲート
- [references/cron-setup.md](references/cron-setup.md) — cron登録方法
- [references/schemas.md](references/schemas.md) — evalとbenchmarkの保存形式
- [references/client-knowledge.md](references/client-knowledge.md) — クライアントナレッジの読み込み方
- [examples/good-output.md](examples/good-output.md) — 正常系と停止系の出力例

---

## ステップ1: 対象スキルと改善目的の確定

- [ ] 改善対象の既存スキルを必ず特定した
- [ ] 改善理由を必ず特定した
- [ ] 対象スキル配下だけを変更対象にする前提を必ず確認した
- [ ] クライアント案件の実例やナレッジが必要な場合は、`references/client-knowledge.md` に従って対象クライアントフォルダを確認した
- [ ] feedback日次レビューモード時は `python3 scripts/feedback_manager.py collect-feedback`、`python3 scripts/feedback_manager.py build-feedback-candidates`、`python3 scripts/feedback_manager.py build-feedback-proposals`、`python3 scripts/feedback_manager.py render-feedback-announcement` を必ず実行した
- [ ] 自動修正モード時は `python3 scripts/automation_manager.py select-fix-candidate --policy automation/auto-fix-policy.json` を必ず実行した
- [ ] 自動修正モード時は候補がある場合だけ `create-rollback-point` を必ず実行した
- [ ] 自動修正モード時は `automation/auto-fix-policy.json` を前提に、除外対象を避けたことを確認した
- [ ] cron 実行時は `python3 scripts/automation_manager.py validate-targets` と `python3 scripts/automation_manager.py prepare-sweep` を必ず実行した
- [ ] cron 実行時は `automation/targets.json` の有効対象だけを必ず使った
- [ ] cron 実行時以外は `automation/evals/*.json` を評価ケース置き場にしていないことを確認した

#### 完了条件
- 対象スキルと改善目的が明確であること
- 改善対象が既存スキルであること
- この完了条件を全て満たすまで、次のステップに進んではならない

---

## ステップ2: 評価ケースと作業領域の準備

- [ ] `scripts/run_iteration.py prepare` を必ず実行した
- [ ] 通常の手動改善では `<target-skill>-workspace/evals/evals.json` を使い、cron 固定対象だけ `automation/evals/*.json` を使った
- [ ] 旧版スナップショットと `iteration-N/` の作業領域を必ず生成した

#### 完了条件
- 評価ケースが2件以上あること
- 旧版比較に必要なディレクトリが生成済みであること
- この完了条件を全て満たすまで、次のステップに進んではならない

---

## ステップ3: 旧版比較つき評価の実行

- [ ] 改善版と旧版を同じ評価ケースで必ず比較した
- [ ] 各評価ケースごとに出力、時間、判定結果を必ず保存した
- [ ] 評価中に分かった主な失敗理由を必ず記録した

#### 完了条件
- 全評価ケースの改善版と旧版の結果が揃っていること
- 欠損ファイルや未評価ケースがないこと
- この完了条件を全て満たすまで、次のステップに進んではならない

---

## ステップ4: ベンチマークと自動修正ゲート判定

- [ ] `scripts/aggregate_benchmark.py` を必ず実行した
- [ ] `scripts/generate_review.py` を必ず実行した
- [ ] `scripts/run_iteration.py gate` で自動修正可否を必ず判定した
- [ ] 発火改善が必要な場合のみ `scripts/optimize_description.py` を必ず使った

#### 完了条件
- 改善の有効性が数値または比較結果で判断できること
- 自動修正の可否が明示されていること
- この完了条件を全て満たすまで、次のステップに進んではならない

---

## ステップ5: 条件付き自動修正

- [ ] 自動修正ゲートが許可した場合のみ、対象スキルを1回だけ修正した
- [ ] ゲートが不許可の場合、修正を止めて改善レポートだけを作成した
- [ ] 修正対象を単一スキル配下に必ず限定した
- [ ] 自動修正前に、対象スキルだけの戻しポイントを必ず作成した
- [ ] 自動修正後に `apply-fix` と `verify-fix` を必ず実行した
- [ ] 一時失敗だけは最大3回まで再試行し、致命失敗または3回失敗時は `rollback-fix` で対象スキルだけ元に戻した

#### 完了条件
- 許可条件に一致する場合のみ修正していること
- 対象外ディレクトリに変更を出していないこと
- この完了条件を全て満たすまで、次のステップに進んではならない

---

## ステップ6: 最終品質判定と報告

- [ ] `skill-checker` を必ず実行した
- [ ] `fact-guard` の手順で報告内容を必ず検証した
- [ ] 改善内容、残課題、再実行条件を必ず報告した
- [ ] cron 実行時は `scripts/automation_manager.py record-run` で結果を必ず記録した
- [ ] cron 実行時は最後に `scripts/automation_manager.py render-announcement` の結果を必ず返した
- [ ] 自動修正モード時は `render-fix-report` の結果を必ず返した

#### 完了条件
- `skill-checker` の結果が確認済みであること
- 推測なしの報告になっていること
- この完了条件を全て満たすまで、作業を完了してはならない

---

## 自己完了確認（省略禁止）

- [ ] 対象スキルと改善目的を確定したか
- [ ] 評価ケース準備、旧版比較、benchmark判定まで完了したか
- [ ] 許可時のみ自動修正し、不許可時は停止したか
- [ ] `skill-checker` と `fact-guard` を通したか
- [ ] 通常 cron なら `.runtime/history.jsonl` と `.runtime/latest/` を更新したか
- [ ] feedback 系なら `.runtime/feedback/` 配下を更新したか

---

## 禁止事項

- 新規スキル作成をこのスキルで行ってはならない
- 評価を飛ばして即修正してはならない
- 旧版比較なしに改善成功と判断してはならない
- 自動修正ゲート不許可のままファイルを修正してはならない
- 対象外ディレクトリを変更してはならない
- `skill-checker` と `fact-guard` を省略して完了報告してはならない

## エッジケース

| 状況 | 対応 |
|:-----|:-----|
| cron 固定対象の評価が不足している | `automation/evals/*.json` を補い、比較に必要な確認ケースが揃うまで次に進まない |
| 改善版のpass率が旧版より下がった | 自動修正を止め、原因と改善候補だけを報告する |
| 主観評価しかできない | 自動修正を止め、`review.html` と改善提案のみ返す |
| descriptionだけが弱い | `scripts/optimize_description.py` を先に使って再評価する |
| cronから自動実行された | `automation/targets.json` の有効対象だけを処理する |
| 自動修正で対象を選ぶ | `automation/auto-fix-policy.json` を優先し、除外されていないスキルを候補にする |
| 使っていないツールがある | 保存場所なし・新規記録なしなら即スキップする |
| feedback日次レビューモード | 候補がなければ `HEARTBEAT_OK` を返す |
| 自動修正モードで候補がない | `HEARTBEAT_OK` を返して終了する |
| 自動修正後の検証で失敗した | 戻しポイントから対象スキルだけ戻す |
| 一時失敗が出た | 3回までは同じ run 内で再試行し、それでも失敗したら対象スキルだけ戻す |
