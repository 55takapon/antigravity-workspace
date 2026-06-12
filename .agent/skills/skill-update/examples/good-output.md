# good-output

`skill-update` が返すべきレポートと cron 応答の例。

---

## 例1: 変更なしで静かに終わる

### 入力

```text
必ず skill-update の全ステップを自動実行すること。
```

### 出力

```text
HEARTBEAT_OK
```

---

## 例2: 自動修正まで進んだ通知系

### 入力

```text
必ず skill-update の全ステップを自動実行すること。
```

### 出力

```markdown
# skill-update 自動実行結果

- 実行時刻: 2026-03-30T20:30:00+09:00
- 更新あり: 1件
- 失敗: 0件

## 更新あり
- skill-creator: 更新あり (benchmark 66.7% -> 100.0%, 変更ファイル 2件, 詳細 skill-update/.runtime/workspaces/skill-creator/iteration-1/run_summary.json)
```

---

## 例3: 失敗を通知する

### 入力

```text
必ず skill-update の全ステップを自動実行すること。
```

### 出力

```markdown
# skill-update 自動実行結果

- 実行時刻: 2026-03-30T20:30:00+09:00
- 更新あり: 0件
- 失敗: 1件

## 失敗
- skill-checker: 失敗 (benchmark.json が作れなかった, 詳細 skill-update/.runtime/workspaces/skill-checker/iteration-2/run_summary.json)
```

---

## 例4: feedback 収集で使っていないツールをスキップする

### 入力

```text
scripts/feedback_manager.py collect-feedback
```

### 出力

```text
feedback 収集を完了しました
- 1件の新しい session ログを確認
- 新しい記録がないためスキップ
- 保存場所がないためスキップ
- 2件の新しい Antigravity artifact を確認
追加イベント: 1件
```

---

## 例5: 日次レビューで修正案つきの通知を返す

### 入力

```text
scripts/feedback_manager.py render-feedback-announcement
```

### 出力

```markdown
# skill-update 改善レビュー

## 結論
- 今日の通知自体は正常に送れています。
- 自動で直せる候補は 1件あります。
- 人の確認がほしい問題は 2件あります。
- まず見るのは `skill-update` です。

## 自動で直せる候補
- 1件あります。
- 低リスクのものだけ、このあとの自動修正ジョブが1件ずつ試します。
- `skill-checker`: 出力が分かりにくいことが 2回ありました。軽い修正だけで直せる見込みです。

## まず見るもの
- 対象: `skill-update`
- 今起きていること: 途中で止まることが 2回ありました。
- 原因: 今の実行環境では読めない書き方があり、途中で止まっていました。
- このままだと: `skill-update` の自動見直しや確認が最後まで進まず、直した方がいい問題を見落としたり、改善が遅れたりすることがあります。
- どう直せるか: 今の実行環境で読める書き方にそろえれば直せます。
- この内容で進めてよいか: この案で進めてよければ、次の修正に進めます。
- 発生元: hermes

## 次に見るもの
- 対象: 対象未特定の問題
- 今起きていること: 出力が分かりにくいことが 2回ありました。
- 原因: 出力が分かりにくく、意図どおりに使いにくい状態でした。
- このままだと: この処理の出力が分かりにくく、判断ミスや手戻りが増えやすくなります。
- どう直せるか: 出力例や説明文を直すと、分かりやすさを上げられます。
- この内容で進めてよいか: まず対象スキルを特定してから進めるのが安全です。必要なら原因確認から進めますか？
- 発生元: codex, claude_code
```

---

## 例6: 自動修正に成功した

### 入力

```text
skills/skill-update/SKILL.md を読み、自動修正モードだけを実行してください。
```

### 出力

```markdown
# skill-update 自動修正結果

## 結論
- 軽い問題を自動で直し、確認まで通りました。

## 何が起きていたか
- 対象は `skill-update` です。
- 問題の種類は `runtime_failure` です。

## 何を直したか
- 変更ファイル数: 1件
- 変更: `scripts/feedback_manager.py`

## テスト結果
- 構文チェック: OK
- 変更範囲チェック: OK
- 自動修正ゲート: OK

## 今どうなっているか
- 今は修正後の状態で保存されています。

## 戻しポイント
- 保存先: `/abs/path/to/skill-update/.runtime/fixes/skill-update/20260401-120000/rollback.json`
- ここから `skill-update` だけ元に戻せます。
```

---

## 例7: 一時失敗が出たが、やり直して通った

### 入力

```text
skills/skill-update/SKILL.md を読み、自動修正モードだけを実行してください。
```

### 出力

```markdown
# skill-update 自動修正結果

## 結論
- 一時的な失敗がありましたが、やり直しで通ったため修正を保存しました。

## 何が起きていたか
- 対象は `skill-checker` です。
- 途中で一時的に止まりましたが、同じ run のやり直しで成功しました。

## 原因
- 一時的な実行不調がありました。
- 恒久的に壊れていたわけではありません。

## 何を直したか
- 変更ファイル数: 1件
- 変更: `references/skill-quality-checklist.md`

## テスト結果
- 再試行回数: 2回
- 構文チェック: OK
- 変更範囲チェック: OK
- 自動修正ゲート: OK

## 今どうなっているか
- 今は修正後の状態で保存されています。

## 戻しポイント
- 保存先: `/abs/path/to/skill-update/.runtime/fixes/skill-checker/20260401-120300/rollback.json`
- ここから `skill-checker` だけ元に戻せます。
```

---

## 例8: 自動修正したが戻した

### 入力

```text
skills/skill-update/SKILL.md を読み、自動修正モードだけを実行してください。
```

### 出力

```markdown
# skill-update 自動修正結果

## 結論
- 自動修正を試しましたが、テストで問題が出たためそのスキルだけ元に戻しました。

## 何が起きていたか
- 対象は `skill-checker-test-fail` です。
- 問題の種類は `runtime_failure` です。

## 何を直したか
- 変更ファイル数: 1件
- 変更: `scripts/broken_case.py`

## テスト結果
- 構文チェック: NG
- 変更範囲チェック: OK

## 今どうなっているか
- 今は修正前の状態に戻してあります。

## 戻しポイント
- 保存先: `/abs/path/to/skill-update/.runtime/fixes/skill-checker-test-fail/20260401-120500/rollback.json`
- ここから `skill-checker-test-fail` だけ元に戻せます。
```
