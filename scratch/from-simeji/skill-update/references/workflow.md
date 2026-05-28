# Skill Update 改善ループ

`skill-update` は Anthropic 公開 `skill-creator` の改善ループをできる限り踏襲し、
「評価してから直す」を徹底する。
ただし、自動修正の対象管理は固定 allowlist を増やすより、
`automation/auto-fix-policy.json` で触ってはいけないものだけ除外する方針を取る。

---

## 基本方針

1. 先に評価する
   - 現状の問題を主観で決めつけず、評価ケースで確認する
- 実運用の違和感は `.runtime/feedback/` に先に集める
2. 必ず旧版と比較する
   - 改善版だけ見て「良くなった」と判断してはならない
3. 改善は1回ごとに小さく行う
   - 大きな修正を一度に入れず、再評価しやすい単位で進める
4. 発火精度も別途確認する
   - 出力品質だけでなく、description の弱さも改善対象に含める
5. 自動修正の前に必ず戻しポイントを作る
   - 問題が出たら、そのスキルだけ戻せる状態を先に作る

---

## 詳細フロー

### 1. 対象スキルの確認

- 既存スキルであることを確認する
- 改善理由を1行で言える形にする
- 変更範囲を対象スキル配下に限定する
- 日次レビューでは `scripts/feedback_manager.py collect-feedback` を最初に使う
- 保存場所がない、直近ファイルがない、新しい記録がないツールは即スキップする

### 1.5. 実運用の違和感を集める

- Hermes / Codex / Claude Code / Antigravity の新しい記録だけを見る
- 毎回フルスキャンしない
- 前回どこまで読んだかは `.runtime/feedback/offsets.json` に残す
- 問題らしいものだけ `.runtime/feedback/events.jsonl` に追記する
- `scripts/feedback_manager.py build-feedback-candidates` で同じ問題を候補化する
- `scripts/feedback_manager.py build-feedback-proposals` で自動では直さない問題の修正案をまとめる

### 2. 評価ケースの準備

- 単発実行では `scripts/run_iteration.py prepare` を使って作業領域を作る
- cron 実行では `scripts/automation_manager.py prepare-sweep` を使って一括準備する
- 通常の手動改善では `<target-skill>-workspace/evals/evals.json` を使う
- `automation/evals/*.json` は cron 固定対象だけに使う
- cron 固定対象以外のスキルは、対象スキルの兄弟ワークスペースに評価ケースを置く
- 各ケースには以下を含める
  - `id`
  - `prompt`
  - `expected_output`
  - `assertions`

### 3. 旧版比較の実行

- 旧版スナップショットを必ず保存する
- 改善版と旧版を同じケースで比較する
- 各ケースごとに以下を保存する
  - 生成物
  - `timing.json`
  - `grading.json`

### 4. ベンチマーク化

- `scripts/aggregate_benchmark.py` で以下を集計する
  - pass率
  - 総アサーション数
  - トークン数
  - 所要時間
  - 旧版との差分
- `scripts/generate_review.py` で静的 `review.html` を作る

### 5. 改善判断

- 出力崩壊やpass率悪化がある場合は自動修正を止める
- description 起因の問題なら `scripts/optimize_description.py` を優先する
- 構造・references・examples の問題なら、その範囲に限定して修正する
- 自動修正対象は `automation/auto-fix-policy.json` を優先し、原則すべてのスキルを候補にする
- `denylist / manual_only / high_risk` に入っているスキルは自動修正しない

### 5.5. 自動修正の戻しポイント

- 自動修正に進む前に `scripts/automation_manager.py create-rollback-point` を使う
- 戻しポイントは `.runtime/fixes/<skill>/<run-id>/` に保存する
- 一時失敗だけは最大3回まで再試行してよい
- 構文エラー、許可外変更、benchmark 悪化、ゲート不許可は即停止する
- 検証失敗時は `scripts/automation_manager.py rollback-fix` で対象スキルだけ戻す
- 他のスキルや他の変更は巻き戻してはならない

### 6. 最終判定

- 修正した場合も、しなかった場合も `skill-checker` を必ず実行する
- ユーザーへの報告前に `fact-guard` の手順を必ず通す

---

## 保存場所の原則

- 通常の手動改善の作業領域は、対象スキルの兄弟ディレクトリ `<target-skill>-workspace/` とする
- cron 実行の作業領域だけは `skill-update/.runtime/workspaces/<target-skill>/` とする
- 繰り返し実行時は `iteration-1/`, `iteration-2/` のように増やす
- 各評価ケースは `eval名/with_skill/` と `eval名/old_skill/` を持つ
- feedback の中央保存先は `skill-update/.runtime/feedback/` とする
- 自動では直さない問題の行き先は `.runtime/feedback/proposals.json` とする
- 実運用の違和感は `events.jsonl` に追記し、候補は `candidates.json` にまとめる
- 前回どこまで読んだかは `offsets.json` に保存する
- 自動修正ごとの戻しポイントは `fixes/<skill>/<run-id>/` に保存する
- 中央一覧ログは `skill-update/.runtime/history.jsonl` に追記する
- 各スキルの最新状態は `skill-update/.runtime/latest/<skill>.json` に保存する

---

## 実施順の原則

- 評価前に修正しない
- benchmark前に自動修正可否を決めない
- `skill-checker` 前に完了報告しない
- cron 実行時は最後に `render-announcement` を実行し、更新あり / 失敗時だけ通知する

---

## 主観評価スキルの扱い

文章・デザイン・発想支援のように、
機械的なアサーションだけでは良し悪しを決めにくいスキルでは、
以下を採用する。

- 自動修正は原則停止
- `review.html` に改善前後の見比べ材料をまとめる
- benchmark は補助指標として扱い、最終判断は慎重に行う
