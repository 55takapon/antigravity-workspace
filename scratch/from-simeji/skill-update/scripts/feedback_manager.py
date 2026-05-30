#!/usr/bin/env python3
"""skill-update の feedback 収集と候補化を補助する。"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


LOGGER = logging.getLogger(__name__)
UTC = timezone.utc
JST = timezone(timedelta(hours=9))

ISSUE_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (
        "runtime_failure",
        (
            "失敗",
            "止ま",
            "error",
            "failed",
            "timeout",
            "exception",
            "traceback",
            "authentication_failed",
            "permission denied",
            "gateway closed",
        ),
    ),
    (
        "not_triggered",
        (
            "発火しない",
            "発火しなかった",
            "動かない",
            "起動しない",
            "反応しない",
            "呼ばれない",
            "didn't trigger",
            "not triggered",
        ),
    ),
    (
        "repeat_manual_fix",
        (
            "毎回直",
            "また直",
            "何度も直",
            "手で直",
            "毎回修正",
            "same fix",
            "manual fix",
        ),
    ),
    (
        "low_quality_output",
        (
            "おかしい",
            "違う",
            "変だ",
            "微妙",
            "品質が低い",
            "ズレて",
            "期待と違う",
            "wrong",
            "bad output",
            "low quality",
        ),
    ),
]

def configure_logging() -> None:
    """標準出力向けロギング設定。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def skill_update_root() -> Path:
    """skill-update のルートを返す。"""
    return Path(__file__).resolve().parents[1]


def default_policy_path() -> Path:
    """自動修正ポリシーの既定パス。"""
    return skill_update_root() / "automation" / "auto-fix-policy.json"


def repo_root() -> Path:
    """リポジトリルートを返す。"""
    env_root = os.environ.get("SKILL_UPDATE_REPO_ROOT", "").strip()
    if env_root:
        candidate = Path(os.path.expandvars(env_root)).expanduser().resolve()
        if candidate.exists():
            return candidate
    markers = (
        ("common-skills", "hinata"),
        (".agent", ".agents"),
    )
    checked: list[Path] = []
    for start in (Path.cwd().resolve(), skill_update_root().resolve()):
        for candidate in (start, *start.parents):
            if candidate in checked:
                continue
            checked.append(candidate)
            if (candidate / ".git").exists():
                return candidate
            for left, right in markers:
                if (candidate / left).exists() and (candidate / right).exists():
                    return candidate
    raise RuntimeError("リポジトリルートを特定できませんでした")


def optional_repo_roots() -> list[Path]:
    """存在する場合だけリポジトリ系ルートを返す。"""
    try:
        return [repo_root()]
    except RuntimeError:
        return []


def codex_skill_roots() -> list[Path]:
    """Codex のスキル配置候補を返す。"""
    roots: list[Path] = []
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        roots.append(Path(os.path.expandvars(codex_home)).expanduser() / "skills")
    roots.append(Path.home() / ".codex" / "skills")
    return roots


def path_from_env(env_name: str, default_value: str) -> Path:
    """環境変数があればそれを優先し、なければ既定パスを返す。"""
    raw = os.environ.get(env_name, default_value)
    return Path(os.path.expandvars(raw)).expanduser()


def load_auto_fix_policy(path: Path) -> dict[str, Any]:
    """自動修正ポリシーを読み込む。"""
    if not path.is_file():
        return {
            "default_mode": "enabled",
            "denylist": [],
            "manual_only": [],
            "high_risk": [],
            "retain_fixed_evals": [],
        }
    payload = load_json(path)
    payload.setdefault("default_mode", "enabled")
    for key in ("denylist", "manual_only", "high_risk", "retain_fixed_evals"):
        value = payload.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"{key} は配列である必要があります")
        payload[key] = [str(item).strip() for item in value if str(item).strip()]
    return payload


def default_runtime_root() -> Path:
    """実行時保存ルートの既定パス。"""
    return skill_update_root() / ".runtime"


def feedback_root(runtime_root: Path) -> Path:
    """feedback 保存先を返す。"""
    return runtime_root / "feedback"


def events_path(runtime_root: Path) -> Path:
    return feedback_root(runtime_root) / "events.jsonl"


def candidates_path(runtime_root: Path) -> Path:
    return feedback_root(runtime_root) / "candidates.json"


def proposals_path(runtime_root: Path) -> Path:
    return feedback_root(runtime_root) / "proposals.json"


def offsets_path(runtime_root: Path) -> Path:
    return feedback_root(runtime_root) / "offsets.json"


def iso_now() -> str:
    return datetime.now(JST).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON の最上位は辞書である必要があります: {path}")
    return data


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False))
        handle.write("\n")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def load_offsets(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"sources": {}, "updated_at": ""}
    payload = load_json(path)
    payload.setdefault("sources", {})
    return payload


def save_offsets(path: Path, payload: dict[str, Any]) -> None:
    payload["updated_at"] = iso_now()
    write_json(path, payload)


def source_state(offsets: dict[str, Any], source_key: str) -> dict[str, Any]:
    sources = offsets.setdefault("sources", {})
    state = sources.get(source_key)
    if not isinstance(state, dict):
        state = {}
        sources[source_key] = state
    return state


def cursor_value(state: dict[str, Any], legacy_keys: tuple[str, ...] = ()) -> int:
    cursor = state.get("cursor")
    if isinstance(cursor, dict):
        value = cursor.get("value", 0)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    for key in legacy_keys:
        try:
            return int(state.get(key, 0))
        except (TypeError, ValueError):
            continue
    return 0


def set_cursor(
    offsets: dict[str, Any],
    source_key: str,
    *,
    kind: str,
    value: int,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "cursor": {
            "kind": kind,
            "value": value,
        },
        "checked_at": iso_now(),
    }
    if extra:
        payload["cursor"].update(extra)
    offsets.setdefault("sources", {})[source_key] = payload


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_issue(text: str) -> str | None:
    lowered = text.lower()
    for issue_kind, patterns in ISSUE_PATTERNS:
        if any(pattern in text or pattern in lowered for pattern in patterns):
            return issue_kind
    return None


def is_error_payload(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            '"status": "error"',
            '"status":"error"',
            "authentication_failed",
            "traceback",
            "permission denied",
            "gateway closed",
            "timeout",
            "failed",
            "exception",
        )
    )


def discover_skills() -> list[tuple[str, Path]]:
    """利用可能なスキル名とパスを返す。"""
    discovered: dict[str, Path] = {}
    roots: list[Path] = []
    for root in optional_repo_roots():
        roots.extend(
            [
                root / "common-skills",
                root / "hinata" / "skills",
                root / ".agent" / "skills",
                root / ".agents" / "skills",
            ]
        )
    roots.extend(codex_skill_roots())
    for base in roots:
        if not base.is_dir():
            continue
        for child in base.iterdir():
            if (child / "SKILL.md").is_file():
                discovered.setdefault(child.name, child.resolve())
    return sorted(discovered.items(), key=lambda item: len(item[0]), reverse=True)


def known_skill_names() -> list[str]:
    return [name for name, _ in discover_skills()]


def infer_skill_name(text: str, skills: list[str]) -> str:
    lowered = text.lower()
    for skill in skills:
        if skill.lower() in lowered:
            return skill
    return "unknown"


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root()))
    except (RuntimeError, ValueError):
        return str(path.resolve())


def parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def file_mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


def read_tail_lines(path: Path, max_lines: int) -> list[str]:
    buffer: deque[str] = deque(maxlen=max_lines)
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            buffer.append(line)
    return list(buffer)


def newest_paths(base: Path, pattern: str, limit: int) -> list[Path]:
    if not base.exists():
        return []
    paths = [path for path in base.glob(pattern) if path.is_file()]
    return sorted(paths, key=file_mtime_ns, reverse=True)[:limit]


def read_new_jsonl_rows(path: Path, start_offset: int) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    end_offset = start_offset
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        handle.seek(start_offset)
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
        end_offset = handle.tell()
    return rows, end_offset


def issue_label(issue_kind: str) -> str:
    return {
        "runtime_failure": "途中で止まる",
        "not_triggered": "呼ばれるはずの処理が動かない",
        "repeat_manual_fix": "同じ手直しが何度も起きる",
        "low_quality_output": "出力が分かりにくい",
    }.get(issue_kind, issue_kind or "不明")


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, str]:
    skill_name = str(candidate.get("skill_name", "unknown"))
    unknown_rank = 1 if skill_name == "unknown" else 0
    count = int(candidate.get("count", 0) or 0)
    return (unknown_rank, -count, skill_name)


def summarize_cause(candidate: dict[str, Any]) -> str:
    issue_kind = str(candidate.get("issue_kind", ""))
    evidence_items = candidate.get("evidence", [])
    evidence_text = " ".join(
        str(item.get("evidence_text", ""))
        for item in evidence_items
        if isinstance(item, dict)
    ).lower()

    if "guildid required" in evidence_text:
        return "通知を送る先の情報が足りず、送信のところで止まっていました。"
    if "cannot import name 'utc'" in evidence_text or "cannot import name \\\"utc\\\"" in evidence_text:
        return "今の実行環境では読めない書き方があり、途中で止まっていました。"
    if "permission denied" in evidence_text:
        return "必要な場所に触れず、途中で止まっていました。"
    if "timeout" in evidence_text:
        return "時間内に終わらず、途中で止まっていました。"
    if issue_kind == "runtime_failure":
        return "裏側の処理が途中で止まっていました。"
    if issue_kind == "not_triggered":
        return "呼ばれるはずの処理が動いていませんでした。"
    if issue_kind == "repeat_manual_fix":
        return "同じ直しを人が何回も入れていました。"
    if issue_kind == "low_quality_output":
        return "出力が分かりにくく、意図どおりに使いにくい状態でした。"
    return "原因の切り分けがまだ必要です。"


def summarize_impact(candidate: dict[str, Any]) -> str:
    issue_kind = str(candidate.get("issue_kind", ""))
    skill_name = str(candidate.get("skill_name", "unknown"))
    skill_label = "この仕組み" if skill_name == "unknown" else f"`{skill_name}`"

    if skill_name == "unknown":
        if issue_kind == "runtime_failure":
            return "この仕組みの自動見直しや確認が最後まで進まず、直した方がいい問題を見落としたり、改善が遅れたりすることがあります。"
        if issue_kind == "not_triggered":
            return "この仕組みが必要な時に動かず、確認や更新が抜けることがあります。"
        if issue_kind == "repeat_manual_fix":
            return "この仕組みで同じ手直しが何度も発生し、手間が増えます。"
        if issue_kind == "low_quality_output":
            return "この仕組みの出力が分かりにくく、判断ミスや手戻りが増えやすくなります。"
    if issue_kind == "runtime_failure":
        return f"{skill_label}の自動見直しや確認が最後まで進まず、直した方がいい問題を見落としたり、改善が遅れたりすることがあります。"
    if issue_kind == "not_triggered":
        return f"{skill_label}が必要な時に動かず、確認や更新が抜けることがあります。"
    if issue_kind == "repeat_manual_fix":
        return f"{skill_label}に同じ手直しが何度も発生し、手間が増えます。"
    if issue_kind == "low_quality_output":
        return f"{skill_label}の出力が分かりにくく、判断ミスや手戻りが増えやすくなります。"
    return "放置すると改善の優先順位が分かりにくくなります。"


def summarize_fix(candidate: dict[str, Any]) -> str:
    issue_kind = str(candidate.get("issue_kind", ""))
    evidence_items = candidate.get("evidence", [])
    evidence_text = " ".join(
        str(item.get("evidence_text", ""))
        for item in evidence_items
        if isinstance(item, dict)
    ).lower()

    if "guildid required" in evidence_text:
        return "通知先の設定を見直せば直せる可能性があります。必要ならこのまま原因確認に進めます。"
    if "cannot import name 'utc'" in evidence_text or "cannot import name \\\"utc\\\"" in evidence_text:
        return "今の実行環境で読める書き方にそろえれば直せます。必要ならこのまま修正に進めます。"
    if issue_kind == "runtime_failure":
        return "まず失敗した回のログを1件見て、止まった理由を特定すれば次の修正に進めます。"
    if issue_kind == "not_triggered":
        return "どの条件で動かなかったかを確認し、呼ばれ方か説明文を直せば改善できます。"
    if issue_kind == "repeat_manual_fix":
        return "毎回人が直している部分をルール化すれば、自動化しやすくなります。"
    if issue_kind == "low_quality_output":
        return "出力例や説明文を直すと、分かりやすさを上げられます。"
    return "まず原因を切り分けてから、軽い修正にするか判断します。"


def suggested_change_kinds(candidate: dict[str, Any]) -> list[str]:
    issue_kind = str(candidate.get("issue_kind", ""))
    evidence_text = " ".join(
        str(item.get("evidence_text", ""))
        for item in candidate.get("evidence", [])
        if isinstance(item, dict)
    ).lower()

    if issue_kind == "runtime_failure":
        if (
            "cannot import name 'utc'" in evidence_text
            or 'cannot import name "utc"' in evidence_text
            or "invalid choice: 'run-sweep'" in evidence_text
            or "file name too long" in evidence_text
            or "permission denied" in evidence_text and "skills/" in evidence_text
        ):
            return ["light_script"]
        return []
    if issue_kind == "not_triggered":
        return ["description", "examples"]
    if issue_kind == "repeat_manual_fix":
        return ["examples", "references"]
    if issue_kind == "low_quality_output":
        return ["description", "examples", "references"]
    return []


def policy_mode(skill_name: str, policy: dict[str, Any]) -> str:
    if skill_name in set(policy.get("denylist", [])):
        return "deny"
    if skill_name in set(policy.get("manual_only", [])):
        return "manual_only"
    if skill_name in set(policy.get("high_risk", [])):
        return "high_risk"
    return str(policy.get("default_mode", "enabled"))


def auto_fix_eligibility(candidate: dict[str, Any], policy: dict[str, Any]) -> tuple[bool, str, str]:
    skill_name = str(candidate.get("skill_name", "unknown")).strip() or "unknown"
    evidence_text = " ".join(
        str(item.get("evidence_text", ""))
        for item in candidate.get("evidence", [])
        if isinstance(item, dict)
    ).lower()

    if skill_name == "unknown":
        return False, "対象スキルを特定できていないため、自動修正はまだ行いません。", "unknown"
    mode = policy_mode(skill_name, policy)
    if mode == "deny":
        return False, "このスキルは自動修正しない設定です。", mode
    if mode == "manual_only":
        return False, "このスキルは通知までに止め、人の確認後だけ直す設定です。", mode
    if mode == "high_risk":
        return False, "このスキルは影響が大きいため、自動修正しません。", mode
    if "guildid required" in evidence_text:
        return False, "通知先の設定側の問題で、スキル修正だけでは直せないため自動修正しません。", mode
    if not suggested_change_kinds(candidate):
        return False, "まだ安全な軽い修正に絞れないため、自動修正は止めます。", mode
    return True, "軽い修正だけで直せる可能性が高いため、自動修正候補にできます。", mode


def scan_hermes_sessions(
    _runtime_root: Path,
    offsets: dict[str, Any],
    max_files: int,
    max_lines: int,
    skills: list[str],
) -> tuple[list[dict[str, Any]], str]:
    base = path_from_env("HERMES_HOME", "~/.hermes") / "profiles"
    source_key = "hermes_sessions"
    state = source_state(offsets, source_key)
    latest_seen = cursor_value(state, ("last_mtime_ns",))
    paths = newest_paths(base, "**/sessions/*.json", max_files)
    if not paths:
        return [], "保存場所がないためスキップ"
    fresh = [path for path in paths if file_mtime_ns(path) > latest_seen]
    if not fresh:
        return [], "新しい記録がないためスキップ"

    events: list[dict[str, Any]] = []
    latest_mtime = latest_seen
    for path in fresh:
        latest_mtime = max(latest_mtime, file_mtime_ns(path))
        try:
            payload = load_json(path)
        except Exception:
            continue
        messages = payload.get("messages", [])
        if not isinstance(messages, list):
            continue
        for index, message in enumerate(messages[-max_lines:]):
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = message.get("content", "")
            if isinstance(content, list):
                text = normalize_text(" ".join(str(item.get("text", item)) for item in content if isinstance(item, dict)))
            else:
                text = normalize_text(str(content))
            if not text or text.startswith("--- name:"):
                continue
            if role == "user":
                issue_kind = classify_issue(text)
            elif is_error_payload(text):
                issue_kind = "runtime_failure"
            else:
                issue_kind = None
            if issue_kind is None:
                continue
            skill_name = infer_skill_name(text, skills)
            session_id = str(payload.get("session_id") or path.stem)
            events.append(
                {
                    "event_id": f"hermes-session:{session_id}:{index}",
                    "source_tool": "hermes",
                    "source_type": "chat_feedback",
                    "session_id": session_id,
                    "skill_name": skill_name,
                    "issue_kind": issue_kind,
                    "event_time": str(payload.get("last_updated") or payload.get("session_start") or ""),
                    "evidence_text": text[:400],
                    "source_path": str(path),
                    "cluster_key": f"{skill_name}:{issue_kind}",
                    "role": role,
                }
            )
    set_cursor(offsets, source_key, kind="mtime_ns", value=latest_mtime)
    return events, f"{len(fresh)}件の新しいHermes sessionログを確認"


def scan_hermes_cron(
    _runtime_root: Path,
    offsets: dict[str, Any],
    max_files: int,
    max_lines: int,
    skills: list[str],
) -> tuple[list[dict[str, Any]], str]:
    base = path_from_env("HERMES_HOME", "~/.hermes") / "profiles"
    source_key = "hermes_cron"
    state = source_state(offsets, source_key)
    latest_seen = cursor_value(state, ("last_mtime_ns",))
    paths = newest_paths(base, "**/cron/output/**/*.md", max_files)
    if not paths:
        return [], "保存場所がないためスキップ"
    fresh = [path for path in paths if file_mtime_ns(path) > latest_seen]
    if not fresh:
        return [], "新しい記録がないためスキップ"

    events: list[dict[str, Any]] = []
    latest_mtime = latest_seen
    for path in fresh:
        latest_mtime = max(latest_mtime, file_mtime_ns(path))
        text = normalize_text("\n".join(read_tail_lines(path, max_lines)))
        if not text or "[SILENT]" in text or "HEARTBEAT_OK" in text:
            continue
        issue_kind = "runtime_failure" if is_error_payload(text) else classify_issue(text)
        if issue_kind is None:
            continue
        skill_name = infer_skill_name(text, skills)
        events.append(
            {
                "event_id": f"hermes-cron:{path.parent.name}:{path.stem}",
                "source_tool": "hermes",
                "source_type": "cron_output",
                "session_id": path.parent.name,
                "skill_name": skill_name,
                "issue_kind": issue_kind,
                "event_time": path.stem,
                "evidence_text": text[:400],
                "source_path": str(path),
                "cluster_key": f"{skill_name}:{issue_kind}",
                "role": "system",
            }
        )
    set_cursor(offsets, source_key, kind="mtime_ns", value=latest_mtime)
    return events, f"{len(fresh)}件の新しいHermes cron出力を確認"


def scan_codex_history(
    _runtime_root: Path,
    offsets: dict[str, Any],
    skills: list[str],
) -> tuple[list[dict[str, Any]], str]:
    history_path = path_from_env("CODEX_HOME", "~/.codex") / "history.jsonl"
    source_key = "codex_history"
    if not history_path.is_file():
        return [], "保存場所がないためスキップ"
    state = source_state(offsets, source_key)
    cursor = state.get("cursor", {})
    stat = history_path.stat()
    current_inode = int(stat.st_ino)
    last_offset = 0
    if isinstance(cursor, dict):
        try:
            last_offset = int(cursor.get("value", 0))
        except (TypeError, ValueError):
            last_offset = 0
        if cursor.get("inode") != current_inode:
            last_offset = 0
    elif stat.st_size < cursor_value(state, ("last_ts",)):
        last_offset = 0

    events: list[dict[str, Any]] = []
    rows, end_offset = read_new_jsonl_rows(history_path, last_offset)
    if not rows:
        return [], "新しい記録がないためスキップ"
    new_rows = 0
    for payload in rows:
        ts = int(payload.get("ts") or 0)
        new_rows += 1
        text = normalize_text(str(payload.get("text", "")))
        if not text:
            continue
        issue_kind = classify_issue(text)
        if issue_kind is None:
            continue
        skill_name = infer_skill_name(text, skills)
        event_time = datetime.fromtimestamp(ts, JST).isoformat()
        events.append(
            {
                "event_id": f"codex:{payload.get('session_id', '')}:{ts}",
                "source_tool": "codex",
                "source_type": "chat_feedback",
                "session_id": str(payload.get("session_id", "")),
                "skill_name": skill_name,
                "issue_kind": issue_kind,
                "event_time": event_time,
                "evidence_text": text[:400],
                "source_path": str(history_path),
                "cluster_key": f"{skill_name}:{issue_kind}",
                "role": "user",
            }
        )
    set_cursor(
        offsets,
        source_key,
        kind="file_offset",
        value=end_offset,
        extra={
            "path": str(history_path),
            "inode": current_inode,
            "mtime_ns": int(stat.st_mtime_ns),
        },
    )
    return events, f"{new_rows}件の新しい Codex 履歴を確認"


def scan_claude_projects(
    _runtime_root: Path,
    offsets: dict[str, Any],
    max_files: int,
    max_lines: int,
    skills: list[str],
) -> tuple[list[dict[str, Any]], str]:
    base = path_from_env("CLAUDE_HOME", "~/.claude") / "projects"
    source_key = "claude_projects"
    state = source_state(offsets, source_key)
    latest_seen = cursor_value(state, ("last_mtime_ns",))
    paths = newest_paths(base, "**/*.jsonl", max_files)
    if not paths:
        return [], "保存場所がないためスキップ"
    fresh = [path for path in paths if file_mtime_ns(path) > latest_seen]
    if not fresh:
        return [], "新しい記録がないためスキップ"

    events: list[dict[str, Any]] = []
    latest_mtime = latest_seen
    for path in fresh:
        latest_mtime = max(latest_mtime, file_mtime_ns(path))
        for line in read_tail_lines(path, max_lines):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = ""
            role = ""
            if payload.get("type") == "user":
                message = payload.get("message", {})
                if isinstance(message, dict):
                    text = normalize_text(str(message.get("content", "")))
                    role = "user"
            elif payload.get("type") == "assistant":
                message = payload.get("message", {})
                if isinstance(message, dict):
                    content = message.get("content", [])
                    if isinstance(content, list):
                        parts = [
                            str(item.get("text", ""))
                            for item in content
                            if isinstance(item, dict) and item.get("type") == "text"
                        ]
                        text = normalize_text(" ".join(parts))
                        role = "assistant"
            if not text:
                continue
            issue_kind = classify_issue(text)
            if issue_kind is None:
                continue
            skill_name = infer_skill_name(text, skills)
            events.append(
                {
                    "event_id": f"claude:{payload.get('uuid', '')}",
                    "source_tool": "claude_code",
                    "source_type": "chat_feedback",
                    "session_id": str(payload.get("sessionId", "")),
                    "skill_name": skill_name,
                    "issue_kind": issue_kind,
                    "event_time": str(payload.get("timestamp", "")),
                    "evidence_text": text[:400],
                    "source_path": str(path),
                    "cluster_key": f"{skill_name}:{issue_kind}",
                    "role": role,
                }
            )
    set_cursor(offsets, source_key, kind="mtime_ns", value=latest_mtime)
    return events, f"{len(fresh)}件の新しい Claude Code ログを確認"


def scan_antigravity_brain(
    _runtime_root: Path,
    offsets: dict[str, Any],
    max_files: int,
    skills: list[str],
) -> tuple[list[dict[str, Any]], str]:
    base = path_from_env("ANTIGRAVITY_HOME", "~/.gemini/antigravity") / "brain"
    source_key = "antigravity_brain"
    state = source_state(offsets, source_key)
    latest_seen = cursor_value(state, ("last_mtime_ns",))
    if not base.is_dir():
        return [], "保存場所がないためスキップ"

    candidates: list[Path] = []
    for brain_dir in base.iterdir():
        if not brain_dir.is_dir():
            continue
        for filename in ("task.md", "walkthrough.md"):
            path = brain_dir / filename
            if path.is_file():
                candidates.append(path)
    if not candidates:
        return [], "対象ファイルがないためスキップ"

    candidates = sorted(candidates, key=file_mtime_ns, reverse=True)[:max_files]
    fresh = [path for path in candidates if file_mtime_ns(path) > latest_seen]
    if not fresh:
        return [], "新しい記録がないためスキップ"

    events: list[dict[str, Any]] = []
    latest_mtime = latest_seen
    for path in fresh:
        latest_mtime = max(latest_mtime, file_mtime_ns(path))
        text = normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
        if not text:
            continue
        issue_kind = classify_issue(text)
        if issue_kind is None:
            continue
        skill_name = infer_skill_name(text, skills)
        events.append(
            {
                "event_id": f"antigravity:{path.parent.name}:{path.name}",
                "source_tool": "antigravity",
                "source_type": "artifact_feedback",
                "session_id": path.parent.name,
                "skill_name": skill_name,
                "issue_kind": issue_kind,
                "event_time": datetime.fromtimestamp(file_mtime_ns(path) / 1_000_000_000, JST).isoformat(),
                "evidence_text": text[:400],
                "source_path": str(path),
                "cluster_key": f"{skill_name}:{issue_kind}",
                "role": "system",
            }
        )
    set_cursor(offsets, source_key, kind="mtime_ns", value=latest_mtime)
    return events, f"{len(fresh)}件の新しい Antigravity artifact を確認"


def dedupe_new_events(existing_path: Path, new_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_ids: set[str] = set()
    if existing_path.is_file():
        for payload in iter_jsonl(existing_path):
            event_id = str(payload.get("event_id", "")).strip()
            if event_id:
                existing_ids.add(event_id)
    deduped: list[dict[str, Any]] = []
    for event in new_events:
        event_id = str(event.get("event_id", "")).strip()
        if not event_id or event_id in existing_ids:
            continue
        deduped.append(event)
        existing_ids.add(event_id)
    return deduped


def collect_feedback(args: argparse.Namespace) -> int:
    runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
    offsets = load_offsets(offsets_path(runtime_root))
    offsets.setdefault("sources", {})
    skills = known_skill_names()

    all_events: list[dict[str, Any]] = []
    scan_logs: list[str] = []

    for scanner in (
        scan_hermes_sessions,
        scan_hermes_cron,
        scan_codex_history,
        scan_claude_projects,
        scan_antigravity_brain,
    ):
        if scanner is scan_codex_history:
            events, note = scanner(runtime_root, offsets, skills)
        elif scanner is scan_antigravity_brain:
            events, note = scanner(runtime_root, offsets, args.max_files_per_tool, skills)
        else:
            events, note = scanner(
                runtime_root,
                offsets,
                args.max_files_per_tool,
                args.max_lines_per_file,
                skills,
            )
        scan_logs.append(note)
        all_events.extend(events)

    deduped = dedupe_new_events(events_path(runtime_root), all_events)
    for event in deduped:
        append_jsonl(events_path(runtime_root), event)

    save_offsets(offsets_path(runtime_root), offsets)
    LOGGER.info("feedback 収集を完了しました")
    for note in scan_logs:
        LOGGER.info("- %s", note)
    LOGGER.info("追加イベント: %d件", len(deduped))
    return 0


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return list(iter_jsonl(path))


def build_candidate_payload(
    key: str,
    grouped_events: list[dict[str, Any]],
    existing_status: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    ordered = sorted(grouped_events, key=lambda item: str(item.get("event_time", "")))
    first = ordered[0]
    last = ordered[-1]
    source_tools = sorted({str(item.get("source_tool", "")) for item in ordered if item.get("source_tool")})
    payload = {
        "cluster_key": key,
        "skill_name": first.get("skill_name", "unknown"),
        "issue_kind": first.get("issue_kind", ""),
        "count": len(ordered),
        "status": existing_status or "new",
        "first_event_time": first.get("event_time", ""),
        "last_event_time": last.get("event_time", ""),
        "source_tools": source_tools,
        "event_ids": [item.get("event_id", "") for item in ordered],
        "evidence": [
            {
                "event_id": item.get("event_id", ""),
                "source_tool": item.get("source_tool", ""),
                "event_time": item.get("event_time", ""),
                "evidence_text": item.get("evidence_text", ""),
            }
            for item in ordered[-3:]
        ],
    }
    allowed, reason, mode = auto_fix_eligibility(payload, policy)
    payload["suggested_change_kinds"] = suggested_change_kinds(payload)
    payload["auto_fix_allowed"] = allowed
    payload["auto_fix_reason"] = reason
    payload["policy_mode"] = mode
    payload["fixed_eval_available"] = str(payload.get("skill_name", "")) in set(policy.get("retain_fixed_evals", []))
    return payload


def proposal_statuses(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    payload = load_json(path)
    statuses: dict[str, str] = {}
    for item in payload.get("proposals", []):
        if isinstance(item, dict):
            statuses[str(item.get("cluster_key", ""))] = str(item.get("status", "pending"))
    return statuses


def build_proposal_payload(candidate: dict[str, Any], existing_status: str) -> dict[str, Any]:
    skill_name = str(candidate.get("skill_name", "unknown")).strip() or "unknown"
    issue_kind = str(candidate.get("issue_kind", ""))
    source_tools = candidate.get("source_tools", [])
    if not isinstance(source_tools, list):
        source_tools = []

    if skill_name == "unknown":
        approval_prompt = "まず対象スキルを特定してから進めるのが安全です。必要なら原因確認から進めますか？"
    else:
        approval_prompt = "この案で進めてよければ、次の修正に進めます。"

    return {
        "cluster_key": str(candidate.get("cluster_key", "")),
        "skill_name": skill_name,
        "issue_kind": issue_kind,
        "count": int(candidate.get("count", 0) or 0),
        "status": existing_status or "pending",
        "policy_mode": str(candidate.get("policy_mode", "")),
        "auto_fix_reason": str(candidate.get("auto_fix_reason", "")),
        "first_event_time": str(candidate.get("first_event_time", "")),
        "last_event_time": str(candidate.get("last_event_time", "")),
        "source_tools": [str(tool) for tool in source_tools if str(tool).strip()],
        "event_ids": candidate.get("event_ids", []),
        "evidence": candidate.get("evidence", []),
        "cause_summary": summarize_cause(candidate),
        "impact_summary": summarize_impact(candidate),
        "fix_summary": summarize_fix(candidate),
        "approval_prompt": approval_prompt,
    }


def build_feedback_candidates(args: argparse.Namespace) -> int:
    runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
    policy_path = Path(args.policy).resolve() if args.policy else default_policy_path()
    policy = load_auto_fix_policy(policy_path)
    events = load_events(events_path(runtime_root))
    now = datetime.now(UTC)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for event in events:
        event_time = parse_iso(str(event.get("event_time", "")))
        if event_time is None:
            continue
        issue_kind = str(event.get("issue_kind", ""))
        window = timedelta(hours=24) if issue_kind == "runtime_failure" else timedelta(days=7)
        if now - event_time.astimezone(UTC) > window:
            continue
        grouped[str(event.get("cluster_key", ""))].append(event)

    existing_statuses: dict[str, str] = {}
    candidate_path = candidates_path(runtime_root)
    if candidate_path.is_file():
        existing_payload = load_json(candidate_path)
        for item in existing_payload.get("candidates", []):
            if isinstance(item, dict):
                existing_statuses[str(item.get("cluster_key", ""))] = str(item.get("status", "new"))

    candidates: list[dict[str, Any]] = []
    for key, items in sorted(grouped.items()):
        if not key or len(items) < 2:
            continue
        candidates.append(build_candidate_payload(key, items, existing_statuses.get(key, "new"), policy))

    payload = {
        "generated_at": iso_now(),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    write_json(candidate_path, payload)
    LOGGER.info("feedback 候補を更新しました: %s", candidate_path)
    LOGGER.info("候補数: %d", len(candidates))
    return 0


def load_candidate_items(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    payload = load_json(path)
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        return []
    return [item for item in candidates if isinstance(item, dict)]


def build_feedback_proposals(args: argparse.Namespace) -> int:
    runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
    candidate_path = candidates_path(runtime_root)
    proposal_path = proposals_path(runtime_root)

    candidates = load_candidate_items(candidate_path)
    existing_statuses = proposal_statuses(proposal_path)
    proposals: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=candidate_sort_key):
        if bool(candidate.get("auto_fix_allowed")):
            continue
        proposals.append(
            build_proposal_payload(candidate, existing_statuses.get(str(candidate.get("cluster_key", "")), "pending"))
        )

    payload = {
        "generated_at": iso_now(),
        "proposal_count": len(proposals),
        "proposals": proposals,
    }
    write_json(proposal_path, payload)
    LOGGER.info("feedback 提案を更新しました: %s", proposal_path)
    LOGGER.info("提案数: %d", len(proposals))
    return 0


def render_feedback_announcement(args: argparse.Namespace) -> int:
    runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
    candidate_path = candidates_path(runtime_root)
    candidates = load_candidate_items(candidate_path)
    proposal_path = proposals_path(runtime_root)
    if proposal_path.is_file():
        proposal_payload = load_json(proposal_path)
        raw_proposals = proposal_payload.get("proposals", [])
        proposals = [item for item in raw_proposals if isinstance(item, dict)] if isinstance(raw_proposals, list) else []
    else:
        proposals = [build_proposal_payload(candidate, "pending") for candidate in candidates if not bool(candidate.get("auto_fix_allowed"))]

    auto_fix_candidates = [candidate for candidate in candidates if bool(candidate.get("auto_fix_allowed"))]
    if not auto_fix_candidates and not proposals:
        LOGGER.info("HEARTBEAT_OK")
        return 0

    ordered_candidates = sorted(auto_fix_candidates, key=candidate_sort_key)
    ordered_proposals = sorted(proposals, key=candidate_sort_key)
    top_proposals = ordered_proposals[:3]

    lines = [
        "# skill-update 改善レビュー",
        "",
        "## 結論",
        f"- 今日の通知自体は正常に送れています。",
        f"- 自動で直せる候補は {len(ordered_candidates)}件あります。",
        f"- 人の確認がほしい問題は {len(ordered_proposals)}件あります。",
    ]
    if top_proposals:
        first_skill = str(top_proposals[0].get("skill_name", "unknown"))
        first_label = "対象未特定の問題" if first_skill == "unknown" else f"`{first_skill}`"
        lines.append(f"- まず見るのは {first_label} です。")
    elif ordered_candidates:
        first_skill = str(ordered_candidates[0].get("skill_name", "unknown"))
        first_label = "対象未特定の問題" if first_skill == "unknown" else f"`{first_skill}`"
        lines.append(f"- 今夜の自動修正で最初に試すのは {first_label} です。")

    section_titles = ("まず見るもの", "次に見るもの", "あとで見るもの")

    if ordered_candidates:
        lines.extend(
            [
                "",
                "## 自動で直せる候補",
                f"- {len(ordered_candidates)}件あります。",
                "- 低リスクのものだけ、このあとの自動修正ジョブが1件ずつ試します。",
            ]
        )
        for candidate in ordered_candidates[:3]:
            skill_name = str(candidate.get("skill_name", "unknown")) or "unknown"
            issue_kind = issue_label(str(candidate.get("issue_kind", "")))
            count = int(candidate.get("count", 0) or 0)
            if skill_name == "unknown":
                skill_label = "対象未特定の問題"
            else:
                skill_label = f"`{skill_name}`"
            lines.append(f"- {skill_label}: {issue_kind}ことが {count}回ありました。軽い修正だけで直せる見込みです。")

    for index, proposal in enumerate(top_proposals, start=1):
        skill_name = str(proposal.get("skill_name", "unknown")) or "unknown"
        issue_kind = issue_label(str(proposal.get("issue_kind", "")))
        count = int(proposal.get("count", 0) or 0)
        tools = ", ".join(str(tool) for tool in proposal.get("source_tools", []) if tool) or "不明"
        if skill_name == "unknown":
            skill_label = "対象未特定の問題"
        else:
            skill_label = f"`{skill_name}`"
        lines.extend(
            [
                "",
                f"## {section_titles[index - 1]}",
                f"- 対象: {skill_label}",
                f"- 今起きていること: {issue_kind}ことが {count}回ありました。",
                f"- 原因: {str(proposal.get('cause_summary', '')).strip() or '原因の確認が必要です。'}",
                f"- このままだと: {str(proposal.get('impact_summary', '')).strip() or '改善が遅れる可能性があります。'}",
                f"- どう直せるか: {str(proposal.get('fix_summary', '')).strip() or 'まず原因を切り分けてから直し方を決めます。'}",
                f"- この内容で進めてよいか: {str(proposal.get('approval_prompt', '')).strip() or 'この案で進めてよいか確認できれば次に進めます。'}",
                f"- 発生元: {tools}",
            ]
        )

    if len(ordered_proposals) > len(top_proposals):
        lines.extend(
            [
                "",
                "## 補足",
                f"- ほかに {len(ordered_proposals) - len(top_proposals)}件ありますが、まずは上の問題から見るのが分かりやすいです。",
            ]
        )
    LOGGER.info("\n".join(lines))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Feedback helper for skill-update")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser("collect-feedback", help="各ツールの新しい記録から feedback を収集する")
    collect_parser.add_argument("--runtime-root", help="保存先 .runtime のルート")
    collect_parser.add_argument("--max-files-per-tool", type=int, default=5, help="各ツールで確認する最大ファイル数")
    collect_parser.add_argument("--max-lines-per-file", type=int, default=120, help="各ログファイルで読む最大行数")
    collect_parser.set_defaults(func=collect_feedback)

    candidates_parser = subparsers.add_parser("build-feedback-candidates", help="events.jsonl から候補を作る")
    candidates_parser.add_argument("--runtime-root", help="保存先 .runtime のルート")
    candidates_parser.add_argument("--policy", help="auto-fix-policy.json のパス")
    candidates_parser.set_defaults(func=build_feedback_candidates)

    proposals_parser = subparsers.add_parser("build-feedback-proposals", help="candidates.json から修正提案を作る")
    proposals_parser.add_argument("--runtime-root", help="保存先 .runtime のルート")
    proposals_parser.set_defaults(func=build_feedback_proposals)

    announcement_parser = subparsers.add_parser(
        "render-feedback-announcement",
        help="候補がある時だけ日次レビュー通知文を返す",
    )
    announcement_parser.add_argument("--runtime-root", help="保存先 .runtime のルート")
    announcement_parser.set_defaults(func=render_feedback_announcement)
    return parser


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        LOGGER.error("エラー: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
