# cron 登録ガイド

`skill-update` は Hermes cron の専用実行で定期実行できる形を前提にする。

---

## 基本方針

- 定期実行では毎回まず評価を行う
- 自動修正は `auto_fix_gate.json` が許可した場合のみ実行する
- 評価だけで終了した場合も、結果は必ず保存する
- 保存物は `common-skills/skill-update/.runtime/` に集約する
- feedback 収集では、使っていないツールを無理に読まない
- 自動修正は、対象スキルだけの戻しポイントを作ってから進める
- 自動修正の対象は `automation/auto-fix-policy.json` を優先する
- 通知は「更新あり」または「失敗」のときだけ行う
- 全対象が変更なしの場合は `HEARTBEAT_OK` を返して静かに終了する
- cron 実行時は、会話履歴や開いているファイルを対象選定に使わない
- 通常の週次 sweep だけは `automation/targets.json` の `enabled=true` に固定する
- 自動修正ジョブは原則すべてのスキルを候補にし、`denylist / manual_only / high_risk` だけ除外する

---

## 推奨メッセージ

cron の `payload.message` には、スキル内部の手順や引数を細かく埋め込まず、
次の形式を使う。

```text
必ず skill-update の全ステップを自動実行すること。
```

このメッセージを受けたら、`skill-update` は以下を必ず行う。

1. `automation/targets.json` を検証する
2. 有効対象の作業領域を `.runtime/workspaces/` に作る
3. 各対象を順番に評価し、必要時のみ自動修正する
4. 各結果を `.runtime/history.jsonl` と `.runtime/latest/` に残す
5. 最後に `HEARTBEAT_OK` または通知本文を返す

このとき、会話文脈から「たぶん今見ているスキル」などを推測してはならない。
対象スキルが本文中に明示されていなくても、`automation/targets.json` を唯一の対象一覧として扱う。

feedback 日次レビューでは、次も固定ルールとする。

1. `scripts/feedback_manager.py collect-feedback` で新しい記録だけを見る
2. 保存場所がない、直近ファイルがない、新しい記録がないツールは即スキップする
3. `.runtime/feedback/events.jsonl` と `.runtime/feedback/offsets.json` を更新する
4. `scripts/feedback_manager.py build-feedback-candidates` で `.runtime/feedback/candidates.json` を更新する
5. `scripts/feedback_manager.py build-feedback-proposals` で `.runtime/feedback/proposals.json` を更新する
6. `scripts/feedback_manager.py render-feedback-announcement` で候補がある時だけ通知文を返す
7. 候補がない時は `HEARTBEAT_OK` を返す
8. `automation/targets.json`、`prepare-sweep`、`iteration-N/` は触らない

自動修正ジョブでは、次も固定ルールとする。

1. `scripts/automation_manager.py select-fix-candidate --policy automation/auto-fix-policy.json` で候補を1件だけ選ぶ
2. 候補がなければ `HEARTBEAT_OK` を返して終わる
3. 候補がある時だけ `scripts/automation_manager.py create-rollback-point` を実行する
4. 軽い修正だけを行い、`scripts/automation_manager.py apply-fix` と `scripts/automation_manager.py verify-fix` を実行する
5. 補助コマンド失敗時は `scripts/automation_manager.py decide-retry --rollback <rollback.json> --policy automation/auto-fix-policy.json` で再試行可否を判定する
6. `timeout` や `gateway closed` などの一時失敗だけは同じ run 内で最大3回まで再試行する
7. 構文エラー、許可外変更、ゲート不許可、benchmark 悪化は1回で止め、`scripts/automation_manager.py rollback-fix` で対象スキルだけ戻す
8. 3回再試行しても失敗した場合も `rollback-fix` で対象スキルだけ戻す
9. 最後に `scripts/automation_manager.py render-fix-report` の出力を返す

---

## 登録例

```bash
hinata cron create "0 6 * * 1" "必ず skill-update の全ステップを自動実行すること。" \
  --name "Skill Update Review" \
  --workdir /Users/harry/Dropbox/Hermes/hinata \
  --deliver discord:1475803108918562878
```

```bash
hinata cron create "20 23 * * *" "skills/skill-update/SKILL.md を読み、feedback日次レビューモードだけを実行してください。helper script は python3 skills/skill-update/scripts/feedback_manager.py collect-feedback、build-feedback-candidates、build-feedback-proposals、render-feedback-announcement を使ってください。render-feedback-announcement の出力を一字一句そのまま返してください。どれかが失敗したら失敗として報告してください。" \
  --name "skill-update-review" \
  --workdir /Users/harry/Dropbox/Hermes/hinata \
  --deliver discord:1475803108918562878
```

```bash
hinata cron create "50 23 * * *" "skills/skill-update/SKILL.md を読み、自動修正モードだけを実行してください。helper script は python3 skills/skill-update/scripts/automation_manager.py select-fix-candidate、create-rollback-point、apply-fix、verify-fix、decide-retry、rollback-fix、render-fix-report を使ってください。候補がなければ HEARTBEAT_OK を返してください。対象スキル以外は戻してはならず、一時失敗だけは最大3回まで再試行し、致命失敗または3回失敗時はそのスキルだけ元に戻してください。" \
  --name "skill-update-apply" \
  --workdir /Users/harry/Dropbox/Hermes/hinata \
  --deliver discord:1475803108918562878
```

おすすめの順番は次です。

1. `23:20` に 日次レビュー
2. `23:50` に 自動修正

この順なら、1日1回でも
- その日の問題を集める
- まとめて見る
- 直せるものだけ直す

の流れを崩さずに回せる。

feedback 系の cron も、`skill-update` を直接呼ぶこと。
ただし、自然文ではなく、`skills/skill-update/SKILL.md` とモード名を一緒に書くこと。
似た名前の別スキルがあるため、モードなしのあいまいな文面は使ってはならない。

---

## 運用例

- 毎週1回、改善対象候補を見直す
- 発火不良や品質低下が起きたスキルだけ再評価する
- 大規模修正が必要な場合は自動修正せず、レポートだけ返す
- 通知先の設定は cron delivery 側で管理し、SKILL.md 側に埋め込まない

---

## 禁止

- payload に Python コードや細かな内部手順を直接書かない
- benchmark 前に自動修正を開始しない
- cron 実行だけを理由に `skill-checker` を省略しない
- 変更なしの回まで通知してノイズを増やしてはならない
