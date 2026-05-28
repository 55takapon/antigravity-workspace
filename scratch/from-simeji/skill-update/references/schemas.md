# 保存ファイルの形式

`skill-update` が扱う主要ファイルの最小スキーマを定義する。

---

## `evals/evals.json`

```json
{
  "skill_name": "target-skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "ユーザーが実際に言いそうな依頼文",
      "expected_output": "期待する結果の説明",
      "files": [],
      "assertions": [
        {
          "text": "期待条件の説明"
        }
      ]
    }
  ]
}
```

### 必須項目

- `skill_name`
- `evals`
- 各 eval の `id`, `prompt`, `expected_output`

---

## `eval_metadata.json`

```json
{
  "eval_id": 1,
  "eval_name": "description-fix-check",
  "prompt": "ユーザーが実際に言いそうな依頼文",
  "expected_output": "期待する結果の説明",
  "assertions": [
    {
      "text": "期待条件の説明"
    }
  ]
}
```

---

## `timing.json`

```json
{
  "total_tokens": 1200,
  "duration_ms": 5800,
  "total_duration_seconds": 5.8
}
```

---

## `grading.json`

```json
{
  "status": "pass",
  "summary": "主要条件を満たした",
  "expectations": [
    {
      "text": "期待条件の説明",
      "passed": true,
      "evidence": "根拠の要約"
    }
  ]
}
```

### 注意

- `expectations` の要素は必ず `text`, `passed`, `evidence` を使う
- 別名フィールドに変えない

---

## `benchmark.json`

```json
{
  "skill_name": "target-skill-name",
  "generated_at": "2026-03-30T10:00:00+09:00",
  "iteration_dir": "/abs/path/to/iteration-1",
  "baseline_name": "old_skill",
  "configs": [
    {
      "name": "with_skill",
      "label": "改善版",
      "eval_count": 3,
      "assertions_total": 6,
      "assertions_passed": 6,
      "pass_rate": 100.0,
      "mean_tokens": 1200.0,
      "mean_duration_seconds": 5.8,
      "output_files_total": 3
    }
  ],
  "comparisons": [
    {
      "name": "with_skill_vs_old_skill",
      "pass_rate_delta": 20.0,
      "mean_tokens_delta": -100.0,
      "mean_duration_seconds_delta": 0.8,
      "regression_detected": false,
      "output_collapse_detected": false
    }
  ]
}
```

---

## `auto_fix_gate.json`

```json
{
  "allowed": true,
  "change_kinds": ["structure", "description"],
  "pass_rate_before": 66.7,
  "pass_rate_after": 100.0,
  "regression_detected": false,
  "output_collapse_detected": false,
  "reasons": [
    "許可条件を全て満たした"
  ]
}
```

---

## `automation/targets.json`

この設定は cron 固定対象の一覧だけに使う。通常の手動改善では、対象スキルの兄弟ワークスペースにある `evals/evals.json` を使う。

```json
{
  "targets": [
    {
      "skill_name": "skill-creator",
      "skill_path": "common-skills/skill-creator",
      "evals_path": "common-skills/skill-update/automation/evals/skill-creator.json",
      "enabled": true
    }
  ]
}
```

### 必須項目

- `targets`
- 各 target の `skill_name`, `skill_path`, `evals_path`, `enabled`

---

## `automation/auto-fix-policy.json`

```json
{
  "default_mode": "enabled",
  "denylist": ["workspace-backup"],
  "manual_only": ["chat-quality-daily-report"],
  "high_risk": ["deep-researcher"],
  "retain_fixed_evals": ["skill-creator", "skill-checker", "skill-update"],
  "retryable_error_markers": ["timeout", "gateway closed"],
  "fatal_error_markers": ["syntaxerror", "permission denied"]
}
```

### 必須項目

- `default_mode`
- `denylist`
- `manual_only`
- `high_risk`
- `retain_fixed_evals`
- `retryable_error_markers`
- `fatal_error_markers`

---

## `run_summary.json`

```json
{
  "skill_name": "skill-creator",
  "run_at": "2026-03-30T20:30:00+09:00",
  "status": "updated",
  "auto_fix_allowed": true,
  "files_changed": 2,
  "benchmark_before": 66.7,
  "benchmark_after": 100.0,
  "iteration_dir": "/abs/path/to/iteration-1",
  "review_html": "/abs/path/to/review.html",
  "benchmark_md": "/abs/path/to/benchmark.md",
  "error_summary": ""
}
```

### `status` の値

- `no_change`
- `updated`
- `failed`

---

## `history.jsonl`

1行に `run_summary.json` と同じ形式の JSON を1件ずつ追記する。

```json
{"skill_name":"skill-creator","status":"updated","files_changed":2}
{"skill_name":"skill-checker","status":"no_change","files_changed":0}
```

---

## `fixes/<skill>/<run-id>/selection.json`

```json
{
  "status": "selected",
  "run_id": "20260401-120000",
  "skill_name": "skill-update",
  "skill_path": "/abs/path/to/common-skills/skill-update",
  "policy_mode": "enabled",
  "eval_mode": "fixed",
  "evals_path": "/abs/path/to/common-skills/skill-update/automation/evals/skill-update.json",
  "issue_kind": "runtime_failure",
  "suggested_change_kinds": ["light_script"],
  "auto_fix_reason": "軽い修正だけで直せる可能性が高いため、自動修正候補にします。"
}
```

---

## `fixes/<skill>/<run-id>/rollback.json`

```json
{
  "run_id": "20260401-120000",
  "skill_name": "skill-update",
  "skill_path": "/abs/path/to/common-skills/skill-update",
  "backup_dir": "/abs/path/to/common-skills/skill-update/.runtime/fixes/skill-update/20260401-120000/before/skill",
  "suggested_change_kinds": ["light_script"]
}
```

---

## `fixes/<skill>/<run-id>/apply_result.json`

```json
{
  "run_id": "20260401-120000",
  "skill_name": "skill-update",
  "changed_files": [
    "scripts/feedback_manager.py"
  ],
  "change_kinds": [
    "light_script"
  ],
  "files_changed": 1,
  "allowed": true
}
```

---

## `fixes/<skill>/<run-id>/verify_result.json`

```json
{
  "run_id": "20260401-120000",
  "skill_name": "skill-update",
  "changed_files": [
    "scripts/feedback_manager.py"
  ],
  "checks": {
    "changed_files_present": true,
    "change_kinds_allowed": true,
    "py_compile_passed": true,
    "gate_allowed": true
  },
  "passed": true
}
```

---

## `fixes/<skill>/<run-id>/retry_state.json`

```json
{
  "classification": "retryable",
  "reason": "再試行対象の文言 `timeout` を検知",
  "attempts": 2,
  "max_attempts": 3,
  "should_retry": true,
  "message": "helper script timed out",
  "updated_at": "2026-04-01T13:05:00+09:00"
}
```

### 主な項目

- `classification`
  - `retryable / fatal`
- `attempts`
  - 今回の run で何回目の失敗か
- `should_retry`
  - まだやり直してよいか

---

## `feedback/events.jsonl`

各ツールから拾った問題の種を1行ずつ追記する。

```json
{
  "event_id": "codex:session-1:1774677624",
  "source_tool": "codex",
  "source_type": "chat_feedback",
  "session_id": "session-1",
  "skill_name": "skill-update",
  "issue_kind": "low_quality_output",
  "event_time": "2026-03-31T09:00:00+09:00",
  "evidence_text": "このスキルおかしいです",
  "source_path": "~/.codex/history.jsonl",
  "cluster_key": "skill-update:low_quality_output",
  "role": "user"
}
```

### 必須項目

- `event_id`
- `source_tool`
- `source_type`
- `session_id`
- `skill_name`
- `issue_kind`
- `event_time`
- `evidence_text`
- `source_path`
- `cluster_key`

### `issue_kind` の初期値

- `not_triggered`
- `low_quality_output`
- `repeat_manual_fix`
- `runtime_failure`

---

## `feedback/candidates.json`

同じ問題が続いたときに作る改善候補の一覧。

```json
{
  "generated_at": "2026-03-31T09:15:00+09:00",
  "candidate_count": 1,
  "candidates": [
    {
      "cluster_key": "skill-update:runtime_failure",
      "skill_name": "skill-update",
      "issue_kind": "runtime_failure",
      "count": 2,
      "status": "new",
      "first_event_time": "2026-03-31T08:00:00+09:00",
      "last_event_time": "2026-03-31T09:00:00+09:00",
      "source_tools": ["hermes"],
      "event_ids": [
        "hermes-cron:job-1:1774884288892",
        "hermes-cron:job-1:1774884528132"
      ],
      "evidence": [
        {
          "event_id": "hermes-cron:job-1:1774884528132",
          "source_tool": "hermes",
          "event_time": "2026-03-31T09:00:00+09:00",
          "evidence_text": "skill-update が失敗した"
        }
      ]
    }
  ]
}
```

### `status` の初期値

- `new`

### 補足

- `auto_fix_allowed`
  - 今すぐ安全に自動修正してよいか
- `auto_fix_reason`
  - 今は自動修正するかしないかの理由
- `policy_mode`
  - `enabled / manual_only / high_risk / deny / unknown`

---

## `feedback/proposals.json`

自動では直さないが、次にどう直せばよいかをまとめる一覧。

```json
{
  "generated_at": "2026-04-01T23:20:00+09:00",
  "proposal_count": 1,
  "proposals": [
    {
      "cluster_key": "skill-update:runtime_failure",
      "skill_name": "skill-update",
      "issue_kind": "runtime_failure",
      "count": 2,
      "status": "pending",
      "policy_mode": "manual_only",
      "auto_fix_reason": "このスキルは通知までに止め、人の確認後だけ直す設定です。",
      "first_event_time": "2026-04-01T09:00:00+09:00",
      "last_event_time": "2026-04-01T19:00:00+09:00",
      "source_tools": ["hermes"],
      "event_ids": [
        "hermes-cron:job-1:1774884288892",
        "hermes-cron:job-1:1774884528132"
      ],
      "evidence": [
        {
          "event_id": "hermes-cron:job-1:1774884528132",
          "source_tool": "hermes",
          "event_time": "2026-04-01T19:00:00+09:00",
          "evidence_text": "skill-update が失敗した"
        }
      ],
      "cause_summary": "裏側の処理が途中で止まっていました。",
      "impact_summary": "`skill-update`の自動見直しや確認が最後まで進まず、直した方がいい問題を見落としたり、改善が遅れたりすることがあります。",
      "fix_summary": "まず失敗した回のログを1件見て、止まった理由を特定すれば次の修正に進めます。",
      "approval_prompt": "この案で進めてよければ、次の修正に進めます。"
    }
  ]
}
```

---

## `feedback/offsets.json`

各ツールをどこまで読んだかを保存する。

```json
{
  "updated_at": "2026-03-31T09:15:00+09:00",
  "sources": {
    "codex_history": {
      "cursor": {
        "kind": "file_offset",
        "value": 2048,
        "path": "~/.codex/history.jsonl",
        "inode": 123456,
        "mtime_ns": 1774884528132000000
      },
      "checked_at": "2026-03-31T09:15:00+09:00"
    },
    "antigravity_brain": {
      "cursor": {
        "kind": "mtime_ns",
        "value": 1774884528132000000
      },
      "checked_at": "2026-03-31T09:15:00+09:00"
    }
  }
}
```

### 注意

- 保存場所がない、直近ファイルがない、新しい記録がない場合はスキップしてよい
- 毎回フルスキャンせず、`sources` の `cursor` を使って新しい記録だけ読む
- ツールごとに内部の読み方は違ってよいが、外から見る運用ルールは「前回以降の新しい分だけ読む」で統一する
