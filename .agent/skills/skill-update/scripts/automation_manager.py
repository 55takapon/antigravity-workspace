#!/usr/bin/env python3
"""skill-update の自動実行を補助する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import py_compile
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import run_iteration

LOGGER = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))
IGNORE_DIR_NAMES = {".runtime", "__pycache__"}
ALLOWED_AUTO_FIX_KINDS = {
    "description",
    "examples",
    "references",
    "light_script",
}


@dataclass(frozen=True)
class Target:
    """自動改善対象1件。"""

    skill_name: str
    skill_path: Path
    evals_path: Path
    enabled: bool


@dataclass(frozen=True)
class AutoFixPolicy:
    """自動修正ポリシー。"""

    default_mode: str
    denylist: set[str]
    manual_only: set[str]
    high_risk: set[str]
    retain_fixed_evals: set[str]
    retryable_error_markers: tuple[str, ...]
    fatal_error_markers: tuple[str, ...]


def configure_logging() -> None:
    """標準出力向けロギング設定。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def skill_update_root() -> Path:
    """skill-update のルートを返す。"""
    return Path(__file__).resolve().parents[1]


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


def default_targets_path() -> Path:
    """targets.json の既定パス。"""
    return skill_update_root() / "automation" / "targets.json"


def default_policy_path() -> Path:
    """自動修正ポリシーの既定パス。"""
    return skill_update_root() / "automation" / "auto-fix-policy.json"


def default_runtime_root() -> Path:
    """実行時保存ルートの既定パス。"""
    return skill_update_root() / ".runtime"


def discover_skill_paths() -> dict[str, Path]:
    """利用可能なスキル名とパスを返す。"""
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
    discovered: dict[str, Path] = {}
    for base in roots:
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            skill_md = child / "SKILL.md"
            if not skill_md.is_file():
                continue
            discovered.setdefault(child.name, child.resolve())
    return discovered


def feedback_candidates_path(runtime_root: Path) -> Path:
    """feedback 候補JSONの既定パス。"""
    return runtime_root / "feedback" / "candidates.json"


def fixes_root(runtime_root: Path) -> Path:
    """fix 実行の保存ルート。"""
    return runtime_root / "fixes"


def retry_state_path_for_rollback(rollback_path: Path) -> Path:
    """rollback.json と同じ run ディレクトリの retry_state.json を返す。"""
    return rollback_path.resolve().with_name("retry_state.json")


def iso_now() -> str:
    """JST の現在時刻を ISO8601 で返す。"""
    return datetime.now(JST).isoformat()


def run_id_now() -> str:
    """fix 実行用の短いIDを返す。"""
    return datetime.now(JST).strftime("%Y%m%d-%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    """JSON を辞書として読み込む。"""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON の最上位は辞書である必要があります: {path}")
    return data


def load_auto_fix_policy(policy_path: Path) -> AutoFixPolicy:
    """自動修正ポリシーを読み込む。"""
    payload = load_json(policy_path)
    default_mode = str(payload.get("default_mode", "enabled")).strip() or "enabled"
    if default_mode not in {"enabled", "manual_only", "high_risk", "deny"}:
        raise ValueError(f"default_mode が不正です: {default_mode}")

    def as_name_set(key: str) -> set[str]:
        raw = payload.get(key, [])
        if not isinstance(raw, list):
            raise ValueError(f"{key} は配列である必要があります")
        return {str(item).strip() for item in raw if str(item).strip()}

    def as_marker_tuple(key: str) -> tuple[str, ...]:
        raw = payload.get(key, [])
        if not isinstance(raw, list):
            raise ValueError(f"{key} は配列である必要があります")
        return tuple(str(item).strip().lower() for item in raw if str(item).strip())

    return AutoFixPolicy(
        default_mode=default_mode,
        denylist=as_name_set("denylist"),
        manual_only=as_name_set("manual_only"),
        high_risk=as_name_set("high_risk"),
        retain_fixed_evals=as_name_set("retain_fixed_evals"),
        retryable_error_markers=as_marker_tuple("retryable_error_markers"),
        fatal_error_markers=as_marker_tuple("fatal_error_markers"),
    )


def write_json(path: Path, data: dict[str, Any]) -> None:
    """JSON を保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    """JSON Lines に1行追記する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False))
        handle.write("\n")


def sha256_file(path: Path) -> str:
    """ファイル内容のSHA256を返す。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_ignored_relative(rel_path: Path) -> bool:
    """runtimeなどの除外対象かを返す。"""
    return any(part in IGNORE_DIR_NAMES for part in rel_path.parts)


def list_skill_files(base_dir: Path) -> list[Path]:
    """比較対象のファイル一覧を返す。"""
    files: list[Path] = []
    if not base_dir.exists():
        return files
    for path in sorted(base_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base_dir)
        if is_ignored_relative(rel):
            continue
        files.append(rel)
    return files


def build_file_manifest(base_dir: Path) -> dict[str, str]:
    """相対パス -> sha256 の辞書を作る。"""
    manifest: dict[str, str] = {}
    for rel_path in list_skill_files(base_dir):
        manifest[str(rel_path)] = sha256_file(base_dir / rel_path)
    return manifest


def diff_skill_files(before_dir: Path, after_dir: Path) -> list[str]:
    """修正前後で差分があるファイル一覧を返す。"""
    before_manifest = build_file_manifest(before_dir)
    after_manifest = build_file_manifest(after_dir)
    changed: list[str] = []
    for rel_path in sorted(set(before_manifest) | set(after_manifest)):
        if before_manifest.get(rel_path) != after_manifest.get(rel_path):
            changed.append(rel_path)
    return changed


def infer_change_kinds(files: list[str]) -> list[str]:
    """変更ファイルから change_kind を推定する。"""
    kinds: set[str] = set()
    for raw_path in files:
        rel_path = raw_path.replace("\\", "/")
        if rel_path == "SKILL.md":
            kinds.add("description")
        elif rel_path.startswith("examples/"):
            kinds.add("examples")
        elif rel_path.startswith("references/"):
            kinds.add("references")
        elif rel_path.startswith("scripts/"):
            kinds.add("light_script")
        else:
            kinds.add("structure")
    return sorted(kinds)


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, str]:
    """候補の並び順。"""
    skill_name = str(candidate.get("skill_name", "unknown"))
    unknown_rank = 1 if skill_name == "unknown" else 0
    count = int(candidate.get("count", 0) or 0)
    return (unknown_rank, -count, skill_name)


def candidate_evidence_text(candidate: dict[str, Any]) -> str:
    """候補内 evidence の本文をまとめる。"""
    evidence = candidate.get("evidence", [])
    if not isinstance(evidence, list):
        return ""
    return " ".join(
        str(item.get("evidence_text", ""))
        for item in evidence
        if isinstance(item, dict)
    ).lower()


def policy_mode(skill_name: str, policy: AutoFixPolicy) -> str:
    """スキルの自動修正モードを返す。"""
    if skill_name in policy.denylist:
        return "deny"
    if skill_name in policy.manual_only:
        return "manual_only"
    if skill_name in policy.high_risk:
        return "high_risk"
    return policy.default_mode


def failure_classification(message: str, policy: AutoFixPolicy) -> tuple[str, str]:
    """失敗文面から retryable/fatal を判定する。"""
    lowered = message.strip().lower()
    for marker in policy.fatal_error_markers:
        if marker and marker in lowered:
            return "fatal", f"致命扱いの文言 `{marker}` を検知"
    for marker in policy.retryable_error_markers:
        if marker and marker in lowered:
            return "retryable", f"再試行対象の文言 `{marker}` を検知"
    return "fatal", "再試行対象の文言がないため致命扱い"


def load_fixed_eval_targets(targets_path: Path) -> dict[str, Target]:
    """targets.json があれば固定eval対象だけ読み込む。"""
    if not targets_path.is_file():
        return {}
    payload = load_json(targets_path)
    raw_targets = payload.get("targets", [])
    if not isinstance(raw_targets, list):
        return {}

    results: dict[str, Target] = {}
    for item in raw_targets:
        if not isinstance(item, dict):
            continue
        skill_name = str(item.get("skill_name", "")).strip()
        skill_path_raw = str(item.get("skill_path", "")).strip()
        evals_path_raw = str(item.get("evals_path", "")).strip()
        enabled = bool(item.get("enabled"))
        if not enabled or not skill_name or not skill_path_raw or not evals_path_raw:
            continue
        try:
            skill_path = resolve_repo_path(skill_path_raw)
            evals_path = resolve_repo_path(evals_path_raw)
        except FileNotFoundError:
            continue
        if not skill_path.is_dir() or not evals_path.is_file():
            continue
        results[skill_name] = Target(
            skill_name=skill_name,
            skill_path=skill_path,
            evals_path=evals_path,
            enabled=True,
        )
    return results


def suggest_change_kinds(candidate: dict[str, Any]) -> list[str]:
    """候補から推奨 change_kind を返す。"""
    issue_kind = str(candidate.get("issue_kind", ""))
    evidence_text = candidate_evidence_text(candidate)

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


def auto_fix_decision(
    candidate: dict[str, Any],
    skills: dict[str, Path],
    fixed_eval_targets: dict[str, Target],
    policy: AutoFixPolicy,
) -> tuple[bool, str, list[str], str, str, str]:
    """候補を自動修正対象にしてよいか判定する。"""
    skill_name = str(candidate.get("skill_name", "unknown")).strip() or "unknown"
    if skill_name == "unknown":
        return False, "対象スキルを特定できていないため、自動修正しません。", [], "unknown", "common", ""
    if skill_name not in skills:
        return False, "このワークスペースで見つからないスキル名のため、自動修正しません。", [], "missing", "common", ""

    mode = policy_mode(skill_name, policy)
    if mode == "deny":
        return False, "このスキルは自動修正しない設定です。", [], mode, "common", ""
    if mode == "manual_only":
        return False, "このスキルは通知までに止め、人の確認後だけ直す設定です。", [], mode, "common", ""
    if mode == "high_risk":
        return False, "このスキルは影響が大きいため、自動修正しません。", [], mode, "common", ""

    evidence_text = candidate_evidence_text(candidate)
    if "guildid required" in evidence_text:
        return False, "通知先の設定側の問題で、スキル修正だけでは直せないため自動修正しません。", [], mode, "common", ""

    change_kinds = suggest_change_kinds(candidate)
    if not change_kinds:
        return False, "原因は見えていますが、まだ安全な軽い修正に絞れないため自動修正しません。", [], mode, "common", ""

    fixed_target = fixed_eval_targets.get(skill_name)
    eval_mode = "fixed" if fixed_target is not None and skill_name in policy.retain_fixed_evals else "common"
    evals_path = str(fixed_target.evals_path) if fixed_target is not None and eval_mode == "fixed" else ""
    return True, "軽い修正だけで直せる可能性が高いため、自動修正候補にします。", change_kinds, mode, eval_mode, evals_path


def load_candidates_payload(candidate_path: Path) -> dict[str, Any]:
    """候補JSONを読み込む。存在しなければ空を返す。"""
    if not candidate_path.is_file():
        return {"generated_at": "", "candidate_count": 0, "candidates": []}
    payload = load_json(candidate_path)
    payload.setdefault("candidates", [])
    return payload


def update_candidate_status(
    candidate_path: Path,
    cluster_key: str,
    status: str,
    extra: dict[str, Any] | None = None,
) -> None:
    """候補の状態を更新する。"""
    payload = load_candidates_payload(candidate_path)
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("candidates.json の candidates が不正です")
    for item in candidates:
        if not isinstance(item, dict):
            continue
        if str(item.get("cluster_key", "")) != cluster_key:
            continue
        item["status"] = status
        item["updated_at"] = iso_now()
        if extra:
            item.update(extra)
        break
    payload["generated_at"] = iso_now()
    write_json(candidate_path, payload)


def target_index(targets: list[Target]) -> dict[str, Target]:
    """skill_name -> Target の辞書を返す。"""
    return {item.skill_name: item for item in targets if item.enabled}


def sync_tree_from_backup(backup_dir: Path, target_dir: Path) -> None:
    """backup の内容で target を同期し、runtime は残す。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    backup_files = {Path(item) for item in build_file_manifest(backup_dir).keys()}
    target_files = {Path(item) for item in build_file_manifest(target_dir).keys()}

    for rel_path in sorted(target_files - backup_files, reverse=True):
        target_path = target_dir / rel_path
        if target_path.exists():
            target_path.unlink()

    for rel_path in sorted(backup_files):
        source = backup_dir / rel_path
        destination = target_dir / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for path in sorted(target_dir.rglob("*"), reverse=True):
        if not path.is_dir():
            continue
        rel = path.relative_to(target_dir)
        if is_ignored_relative(rel):
            continue
        try:
            next(path.iterdir())
        except StopIteration:
            path.rmdir()


def run_py_compile(skill_path: Path) -> tuple[bool, str]:
    """対象スキルの scripts/*.py を py_compile する。"""
    python_files = sorted((skill_path / "scripts").glob("*.py"))
    if not python_files:
        return True, "scripts 配下にPythonファイルがないため対象なし"
    command = [sys.executable, "-m", "py_compile", *[str(path) for path in python_files]]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode == 0:
        return True, "scripts/*.py の構文チェックを通過"
    message = completed.stderr.strip() or completed.stdout.strip() or "py_compile で失敗"
    return False, message


def repo_relative(path: Path) -> str:
    """リポジトリ相対パス文字列を返す。"""
    try:
        return str(path.resolve().relative_to(repo_root()))
    except (RuntimeError, ValueError):
        return str(path.resolve())


def resolve_repo_path(raw_path: str) -> Path:
    """repo root 基準でパスを解決する。"""
    candidate = Path(os.path.expandvars(raw_path)).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root() / candidate).resolve()


def ensure_skill_dir(path: Path) -> Path:
    """対象スキルの実在を確認する。"""
    skill_dir = path.resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_dir.is_dir() or not skill_md.is_file():
        raise FileNotFoundError(f"対象スキルが見つかりません: {skill_dir}")
    return skill_dir


def load_targets(targets_path: Path) -> list[Target]:
    """targets.json を検証付きで読み込む。"""
    payload = load_json(targets_path)
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list) or not raw_targets:
        raise ValueError("targets は1件以上の配列である必要があります")

    results: list[Target] = []
    seen_names: set[str] = set()
    for index, item in enumerate(raw_targets):
        if not isinstance(item, dict):
            raise ValueError(f"targets[{index}] は辞書である必要があります")

        skill_name = str(item.get("skill_name", "")).strip()
        skill_path_raw = str(item.get("skill_path", "")).strip()
        evals_path_raw = str(item.get("evals_path", "")).strip()
        enabled = bool(item.get("enabled", False))

        if not skill_name:
            raise ValueError(f"targets[{index}] の skill_name が空です")
        if skill_name in seen_names:
            raise ValueError(f"skill_name が重複しています: {skill_name}")
        if not skill_path_raw or not evals_path_raw:
            raise ValueError(f"targets[{index}] の skill_path または evals_path が空です")

        skill_path = ensure_skill_dir(resolve_repo_path(skill_path_raw))
        evals_path = resolve_repo_path(evals_path_raw)
        if not evals_path.is_file():
            raise FileNotFoundError(f"evals_path が見つかりません: {evals_path}")

        evals_payload = load_json(evals_path)
        eval_skill_name = str(evals_payload.get("skill_name", "")).strip()
        if eval_skill_name != skill_name:
            raise ValueError(
                f"evals の skill_name が targets と一致しません: {skill_name} != {eval_skill_name}"
            )

        seen_names.add(skill_name)
        results.append(
            Target(
                skill_name=skill_name,
                skill_path=skill_path,
                evals_path=evals_path,
                enabled=enabled,
            )
        )
    return results


def find_target(manifest: dict[str, Any], skill_name: str) -> dict[str, Any]:
    """manifest から対象スキルを探す。"""
    targets = manifest.get("targets", [])
    if not isinstance(targets, list):
        raise ValueError("manifest の targets が不正です")
    for item in targets:
        if isinstance(item, dict) and item.get("skill_name") == skill_name:
            return item
    raise ValueError(f"manifest に対象スキルがありません: {skill_name}")


def benchmark_metrics(benchmark_path: Path) -> tuple[float | None, float | None]:
    """benchmark から前後の pass率を返す。"""
    if not benchmark_path.is_file():
        return None, None
    payload = load_json(benchmark_path)
    configs = payload.get("configs", [])
    baseline_name = str(payload.get("baseline_name", "")).strip() or "old_skill"
    if not isinstance(configs, list):
        return None, None
    before = None
    after = None
    for config in configs:
        if not isinstance(config, dict):
            continue
        if config.get("name") == baseline_name:
            before = float(config.get("pass_rate") or 0.0)
        if config.get("name") == "with_skill":
            after = float(config.get("pass_rate") or 0.0)
    return before, after


def validate_targets(args: argparse.Namespace) -> int:
    """targets.json の検証。"""
    targets_path = Path(args.targets).resolve() if args.targets else default_targets_path()
    targets = load_targets(targets_path)
    enabled_count = sum(1 for item in targets if item.enabled)
    LOGGER.info("targets を検証しました: %s", targets_path)
    LOGGER.info("対象数: %d / 有効: %d", len(targets), enabled_count)
    return 0


def prepare_sweep(args: argparse.Namespace) -> int:
    """有効 targets の作業領域をまとめて作成する。"""
    targets_path = Path(args.targets).resolve() if args.targets else default_targets_path()
    runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
    targets = [item for item in load_targets(targets_path) if item.enabled]
    if not targets:
        raise ValueError("enabled=true の target がありません")

    runtime_root.mkdir(parents=True, exist_ok=True)
    manifest_targets: list[dict[str, Any]] = []

    for target in targets:
        workspace_dir = runtime_root / "workspaces" / target.skill_name
        namespace = argparse.Namespace(
            skill=str(target.skill_path),
            workspace=str(workspace_dir),
            evals_file=str(target.evals_path),
        )
        result = run_iteration.prepare_iteration(namespace)
        if result != 0:
            raise RuntimeError(f"prepare に失敗しました: {target.skill_name}")
        iteration_dir = run_iteration.latest_iteration_dir(workspace_dir)
        manifest_targets.append(
            {
                "skill_name": target.skill_name,
                "skill_path": str(target.skill_path),
                "evals_path": str(target.evals_path),
                "workspace_dir": str(workspace_dir),
                "iteration_dir": str(iteration_dir),
                "iteration_manifest_path": str(iteration_dir / "iteration_manifest.json"),
                "status": "pending",
                "summary_path": "",
            }
        )

    manifest = {
        "run_id": datetime.now(JST).strftime("%Y%m%d-%H%M%S"),
        "generated_at": iso_now(),
        "targets_path": str(targets_path),
        "runtime_root": str(runtime_root),
        "targets": manifest_targets,
    }
    output_path = Path(args.output).resolve() if args.output else runtime_root / "current_sweep.json"
    write_json(output_path, manifest)
    LOGGER.info("sweep manifest を出力しました: %s", output_path)
    return 0


def build_summary(
    skill_name: str,
    status: str,
    iteration_dir: Path,
    files_changed: int,
    benchmark_path: Path | None,
    gate_path: Path | None,
    error_summary: str,
) -> dict[str, Any]:
    """run_summary.json の内容を組み立てる。"""
    benchmark_before = None
    benchmark_after = None
    gate_allowed = None
    gate_reasons: list[str] = []

    if benchmark_path is not None and benchmark_path.is_file():
        benchmark_before, benchmark_after = benchmark_metrics(benchmark_path)
    if gate_path is not None and gate_path.is_file():
        gate_payload = load_json(gate_path)
        gate_allowed = bool(gate_payload.get("allowed"))
        raw_reasons = gate_payload.get("reasons", [])
        if isinstance(raw_reasons, list):
            gate_reasons = [str(item) for item in raw_reasons]

    review_html = iteration_dir / "review.html"
    benchmark_md = iteration_dir / "benchmark.md"

    return {
        "skill_name": skill_name,
        "run_at": iso_now(),
        "status": status,
        "auto_fix_allowed": gate_allowed,
        "files_changed": files_changed,
        "benchmark_before": benchmark_before,
        "benchmark_after": benchmark_after,
        "benchmark_path": str(benchmark_path) if benchmark_path is not None else "",
        "gate_path": str(gate_path) if gate_path is not None else "",
        "gate_reasons": gate_reasons,
        "iteration_dir": str(iteration_dir),
        "review_html": str(review_html) if review_html.is_file() else "",
        "benchmark_md": str(benchmark_md) if benchmark_md.is_file() else "",
        "error_summary": error_summary.strip(),
    }


def select_fix_candidate(args: argparse.Namespace) -> int:
    """自動修正対象を1件選ぶ。"""
    targets_path = Path(args.targets).resolve() if args.targets else default_targets_path()
    policy_path = Path(args.policy).resolve() if args.policy else default_policy_path()
    runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
    candidate_path = Path(args.candidates).resolve() if args.candidates else feedback_candidates_path(runtime_root)

    skills = discover_skill_paths()
    fixed_eval_targets = load_fixed_eval_targets(targets_path)
    policy = load_auto_fix_policy(policy_path)
    payload = load_candidates_payload(candidate_path)
    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise ValueError("candidates.json の candidates が不正です")

    ordered = sorted(
        (item for item in raw_candidates if isinstance(item, dict) and str(item.get("status", "new")) == "new"),
        key=candidate_sort_key,
    )

    chosen: dict[str, Any] | None = None
    for candidate in ordered:
        allowed, reason, change_kinds, mode, eval_mode, evals_path = auto_fix_decision(
            candidate,
            skills,
            fixed_eval_targets,
            policy,
        )
        if not allowed:
            continue
        skill_name = str(candidate.get("skill_name", "")).strip()
        skill_path = skills[skill_name]
        run_id = run_id_now()
        chosen = {
            "status": "selected",
            "run_id": run_id,
            "selected_at": iso_now(),
            "candidate_path": str(candidate_path),
            "policy_path": str(policy_path),
            "cluster_key": str(candidate.get("cluster_key", "")),
            "skill_name": skill_name,
            "skill_path": str(skill_path),
            "eval_mode": eval_mode,
            "evals_path": evals_path,
            "policy_mode": mode,
            "issue_kind": str(candidate.get("issue_kind", "")),
            "count": int(candidate.get("count", 0) or 0),
            "source_tools": candidate.get("source_tools", []),
            "evidence": candidate.get("evidence", []),
            "auto_fix_reason": reason,
            "suggested_change_kinds": change_kinds,
        }
        update_candidate_status(
            candidate_path,
            str(candidate.get("cluster_key", "")),
            "running",
            {"run_id": run_id, "selected_at": chosen["selected_at"]},
        )
        break

    if chosen is None:
        result = {
            "status": "none",
            "selected_at": iso_now(),
            "reason": "今すぐ安全に自動修正できる候補はありませんでした。",
        }
        output_path = Path(args.output).resolve() if args.output else fixes_root(runtime_root) / "current_selection.json"
        write_json(output_path, result)
        LOGGER.info("自動修正候補はありません: %s", output_path)
        return 0

    run_dir = fixes_root(runtime_root) / chosen["skill_name"] / chosen["run_id"]
    output_path = Path(args.output).resolve() if args.output else run_dir / "selection.json"
    write_json(output_path, chosen)
    LOGGER.info("自動修正候補を選びました: %s", output_path)
    return 0


def create_rollback_point(args: argparse.Namespace) -> int:
    """対象スキルの戻しポイントを作る。"""
    runtime_root = Path(args.runtime_root).resolve() if args.runtime_root else default_runtime_root()
    selection = load_json(Path(args.selection).resolve())
    if str(selection.get("status", "")) == "none":
        raise ValueError("候補なしの selection から戻しポイントは作れません")

    skill_name = str(selection.get("skill_name", "")).strip()
    skill_path = ensure_skill_dir(Path(str(selection.get("skill_path", ""))).resolve())
    run_id = str(selection.get("run_id", "")).strip() or run_id_now()
    run_dir = fixes_root(runtime_root) / skill_name / run_id
    backup_dir = run_dir / "before" / "skill"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(
        skill_path,
        backup_dir,
        ignore=shutil.ignore_patterns(".runtime", ".runtime*", "__pycache__"),
    )

    rollback_payload = {
        "run_id": run_id,
        "created_at": iso_now(),
        "skill_name": skill_name,
        "skill_path": str(skill_path),
        "cluster_key": str(selection.get("cluster_key", "")),
        "candidate_path": str(selection.get("candidate_path", "")),
        "backup_dir": str(backup_dir),
        "selection_path": str(Path(args.selection).resolve()),
        "suggested_change_kinds": selection.get("suggested_change_kinds", []),
        "files_before": build_file_manifest(backup_dir),
    }
    output_path = Path(args.output).resolve() if args.output else run_dir / "rollback.json"
    write_json(output_path, rollback_payload)
    LOGGER.info("戻しポイントを作成しました: %s", output_path)
    return 0


def apply_fix(args: argparse.Namespace) -> int:
    """修正後の変更範囲を記録する。"""
    rollback = load_json(Path(args.rollback).resolve())
    skill_path = ensure_skill_dir(Path(str(rollback.get("skill_path", ""))).resolve())
    backup_dir = Path(str(rollback.get("backup_dir", ""))).resolve()
    selection = load_json(Path(str(rollback.get("selection_path", ""))).resolve())

    changed_files = diff_skill_files(backup_dir, skill_path)
    if not changed_files:
        raise ValueError("変更ファイルがありません。修正が入っていない可能性があります")

    change_kinds = infer_change_kinds(changed_files)
    allowed_kinds = set(str(item) for item in selection.get("suggested_change_kinds", []))
    disallowed_kinds = [item for item in change_kinds if item not in allowed_kinds]
    if disallowed_kinds:
        raise ValueError(f"許可されていない変更種類があります: {', '.join(disallowed_kinds)}")

    payload = {
        "run_id": str(rollback.get("run_id", "")),
        "recorded_at": iso_now(),
        "skill_name": str(rollback.get("skill_name", "")),
        "skill_path": str(skill_path),
        "cluster_key": str(rollback.get("cluster_key", "")),
        "changed_files": changed_files,
        "change_kinds": change_kinds,
        "files_changed": len(changed_files),
        "allowed": True,
        "note": str(args.note or "").strip(),
    }
    output_path = Path(args.output).resolve() if args.output else Path(args.rollback).resolve().with_name("apply_result.json")
    write_json(output_path, payload)
    LOGGER.info("修正内容を記録しました: %s", output_path)
    return 0


def verify_fix(args: argparse.Namespace) -> int:
    """修正後の最低限の機械チェックを実行する。"""
    rollback = load_json(Path(args.rollback).resolve())
    skill_name = str(rollback.get("skill_name", ""))
    skill_path = ensure_skill_dir(Path(str(rollback.get("skill_path", ""))).resolve())
    backup_dir = Path(str(rollback.get("backup_dir", ""))).resolve()
    selection = load_json(Path(str(rollback.get("selection_path", ""))).resolve())

    changed_files = diff_skill_files(backup_dir, skill_path)
    change_kinds = infer_change_kinds(changed_files)
    allowed_kinds = set(str(item) for item in selection.get("suggested_change_kinds", []))
    disallowed_kinds = [item for item in change_kinds if item not in allowed_kinds]
    py_compile_ok, py_compile_note = run_py_compile(skill_path)

    benchmark_path = Path(args.benchmark).resolve() if args.benchmark else None
    gate_path = Path(args.gate).resolve() if args.gate else None
    benchmark_before = None
    benchmark_after = None
    gate_allowed = None
    gate_reasons: list[str] = []
    if benchmark_path is not None and benchmark_path.is_file():
        benchmark_before, benchmark_after = benchmark_metrics(benchmark_path)
    if gate_path is not None and gate_path.is_file():
        gate_payload = load_json(gate_path)
        gate_allowed = bool(gate_payload.get("allowed"))
        raw_reasons = gate_payload.get("reasons", [])
        if isinstance(raw_reasons, list):
            gate_reasons = [str(item) for item in raw_reasons]

    checks = {
        "changed_files_present": bool(changed_files),
        "change_kinds_allowed": not disallowed_kinds,
        "py_compile_passed": py_compile_ok,
        "gate_allowed": gate_allowed,
    }
    passed = checks["changed_files_present"] and checks["change_kinds_allowed"] and checks["py_compile_passed"]
    if gate_allowed is False:
        passed = False

    failure_mode = "none" if passed else "fatal"
    payload = {
        "run_id": str(rollback.get("run_id", "")),
        "verified_at": iso_now(),
        "skill_name": skill_name,
        "changed_files": changed_files,
        "change_kinds": change_kinds,
        "disallowed_change_kinds": disallowed_kinds,
        "checks": checks,
        "failure_mode": failure_mode,
        "py_compile_note": py_compile_note,
        "benchmark_before": benchmark_before,
        "benchmark_after": benchmark_after,
        "benchmark_path": str(benchmark_path) if benchmark_path is not None else "",
        "gate_path": str(gate_path) if gate_path is not None else "",
        "gate_reasons": gate_reasons,
        "passed": passed,
    }
    output_path = Path(args.output).resolve() if args.output else Path(args.rollback).resolve().with_name("verify_result.json")
    write_json(output_path, payload)
    LOGGER.info("修正後チェックを保存しました: %s", output_path)
    if not passed:
        LOGGER.error("検証失敗: %s", skill_name)
        return 1
    return 0


def classify_failure(args: argparse.Namespace) -> int:
    """失敗文面が再試行対象かを判定する。"""
    policy_path = Path(args.policy).resolve() if args.policy else default_policy_path()
    policy = load_auto_fix_policy(policy_path)
    classification, reason = failure_classification(str(args.message or ""), policy)
    payload = {
        "classification": classification,
        "reason": reason,
        "message": str(args.message or ""),
    }
    if args.output:
        write_json(Path(args.output).resolve(), payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))  # noqa: T201
    return 0


def decide_retry(args: argparse.Namespace) -> int:
    """失敗が再試行対象か、何回目かを判定する。"""
    rollback_path = Path(args.rollback).resolve() if args.rollback else None
    state_path = Path(args.state).resolve() if args.state else None
    if state_path is None:
        if rollback_path is None:
            raise ValueError("rollback か state のどちらかが必要です")
        state_path = retry_state_path_for_rollback(rollback_path)

    attempts = 0
    if state_path.is_file():
        existing = load_json(state_path)
        attempts = int(existing.get("attempts", 0) or 0)

    policy_path = Path(args.policy).resolve() if args.policy else default_policy_path()
    policy = load_auto_fix_policy(policy_path)
    classification, reason = failure_classification(str(args.message or ""), policy)

    attempts_after = attempts
    should_retry = False
    if classification == "retryable":
        attempts_after = attempts + 1
        should_retry = attempts_after <= 3
        if not should_retry:
            reason = "一時失敗として扱えますが、3回失敗したので戻すべき状態です。"

    payload = {
        "classification": classification,
        "reason": reason,
        "attempts": attempts_after,
        "max_attempts": 3,
        "should_retry": should_retry,
        "message": str(args.message or ""),
        "updated_at": iso_now(),
    }
    write_json(state_path, payload)
    if args.output:
        write_json(Path(args.output).resolve(), payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))  # noqa: T201
    return 0


def rollback_fix(args: argparse.Namespace) -> int:
    """対象スキルだけ戻しポイントから復元する。"""
    rollback = load_json(Path(args.rollback).resolve())
    backup_dir = Path(str(rollback.get("backup_dir", ""))).resolve()
    skill_path = ensure_skill_dir(Path(str(rollback.get("skill_path", ""))).resolve())

    sync_tree_from_backup(backup_dir, skill_path)
    payload = {
        "run_id": str(rollback.get("run_id", "")),
        "rolled_back_at": iso_now(),
        "skill_name": str(rollback.get("skill_name", "")),
        "skill_path": str(skill_path),
        "restored_from": str(backup_dir),
    }
    output_path = Path(args.output).resolve() if args.output else Path(args.rollback).resolve().with_name("rollback_result.json")
    write_json(output_path, payload)

    cluster_key = str(rollback.get("cluster_key", "")).strip()
    candidate_path_raw = str(rollback.get("candidate_path", "")).strip()
    if cluster_key and candidate_path_raw:
        update_candidate_status(Path(candidate_path_raw).resolve(), cluster_key, "rolled_back", {"rolled_back_at": payload["rolled_back_at"]})

    LOGGER.info("対象スキルを戻しました: %s", output_path)
    return 0


def render_fix_report(args: argparse.Namespace) -> int:
    """自動修正結果の報告文を出力する。"""
    selection = load_json(Path(args.selection).resolve())
    rollback = load_json(Path(args.rollback).resolve())
    verify = load_json(Path(args.verify).resolve()) if args.verify else {}
    apply_result = load_json(Path(args.apply).resolve()) if args.apply else {}
    rollback_result = load_json(Path(args.rollback_result).resolve()) if args.rollback_result else {}

    skill_name = str(selection.get("skill_name", "unknown"))
    issue_kind = str(selection.get("issue_kind", ""))
    changed_files = apply_result.get("changed_files", verify.get("changed_files", []))
    if not isinstance(changed_files, list):
        changed_files = []

    if rollback_result:
        conclusion = "自動修正を試しましたが、テストで問題が出たためそのスキルだけ元に戻しました。"
        now_state = "今は修正前の状態に戻してあります。"
    elif verify and bool(verify.get("passed")):
        conclusion = "軽い問題を自動で直し、確認まで通りました。"
        now_state = "今は修正後の状態で保存されています。"
    else:
        conclusion = "自動修正を試しましたが、まだ採用できる状態ではありません。"
        now_state = "今は追加確認が必要な状態です。"

    lines = [
        "# skill-update 自動修正結果",
        "",
        "## 結論",
        f"- {conclusion}",
        "",
        "## 何が起きていたか",
        f"- 対象は `{skill_name}` です。",
        f"- 問題の種類は `{issue_kind}` です。",
    ]
    evidence = selection.get("evidence", [])
    if isinstance(evidence, list) and evidence:
        latest_evidence = next((item for item in reversed(evidence) if isinstance(item, dict)), None)
        if latest_evidence is not None:
            lines.append(f"- 直近の根拠: {str(latest_evidence.get('evidence_text', ''))[:160]}")

    lines.extend(
        [
            "",
            "## 何を直したか",
            f"- 変更ファイル数: {len(changed_files)}件",
        ]
    )
    if changed_files:
        for file_path in changed_files[:5]:
            lines.append(f"- 変更: `{file_path}`")
    else:
        lines.append("- 変更はまだ採用していません。")

    lines.extend(
        [
            "",
            "## テスト結果",
        ]
    )
    if verify:
        checks = verify.get("checks", {})
        if isinstance(checks, dict):
            lines.append(f"- 構文チェック: {'OK' if checks.get('py_compile_passed') else 'NG'}")
            lines.append(f"- 変更範囲チェック: {'OK' if checks.get('change_kinds_allowed') else 'NG'}")
            if checks.get("gate_allowed") is not None:
                lines.append(f"- 自動修正ゲート: {'OK' if checks.get('gate_allowed') else 'NG'}")
        py_compile_note = str(verify.get("py_compile_note", "")).strip()
        if py_compile_note:
            lines.append(f"- 補足: {py_compile_note}")
    else:
        lines.append("- テスト結果はまだ記録されていません。")

    lines.extend(
        [
            "",
            "## 今どうなっているか",
            f"- {now_state}",
            "",
            "## 戻しポイント",
            f"- 保存先: `{Path(args.rollback).resolve()}`",
            f"- ここから `{skill_name}` だけ元に戻せます。",
        ]
    )

    if args.output:
        write_json(Path(args.output).resolve(), {"report_markdown": "\n".join(lines)})
    print("\n".join(lines))  # noqa: T201
    return 0


def record_run(args: argparse.Namespace) -> int:
    """結果サマリーを保存し、history と latest を更新する。"""
    manifest_path = Path(args.manifest).resolve()
    manifest = load_json(manifest_path)
    runtime_root = Path(str(manifest.get("runtime_root", ""))).resolve()
    target = find_target(manifest, args.skill_name)
    iteration_dir = Path(str(target.get("iteration_dir", ""))).resolve()
    benchmark_path = Path(args.benchmark).resolve() if args.benchmark else None
    gate_path = Path(args.gate).resolve() if args.gate else None

    summary = build_summary(
        skill_name=args.skill_name,
        status=args.status,
        iteration_dir=iteration_dir,
        files_changed=args.files_changed,
        benchmark_path=benchmark_path,
        gate_path=gate_path,
        error_summary=args.error_summary or "",
    )

    summary_path = iteration_dir / "run_summary.json"
    write_json(summary_path, summary)
    append_jsonl(runtime_root / "history.jsonl", summary)
    write_json(runtime_root / "latest" / f"{args.skill_name}.json", summary)

    target["status"] = args.status
    target["summary_path"] = str(summary_path)
    target["recorded_at"] = iso_now()
    write_json(manifest_path, manifest)

    LOGGER.info("run summary を保存しました: %s", summary_path)
    return 0


def render_status_line(summary: dict[str, Any]) -> str:
    """通知本文用の1件分要約。"""
    skill_name = str(summary.get("skill_name", "unknown"))
    benchmark_before = summary.get("benchmark_before")
    benchmark_after = summary.get("benchmark_after")
    files_changed = int(summary.get("files_changed") or 0)
    summary_path = repo_relative(Path(str(summary.get("iteration_dir", ""))) / "run_summary.json")

    if summary.get("status") == "updated":
        before_text = "不明" if benchmark_before is None else f"{benchmark_before:.1f}%"
        after_text = "不明" if benchmark_after is None else f"{benchmark_after:.1f}%"
        return (
            f"- {skill_name}: 更新あり "
            f"(benchmark {before_text} -> {after_text}, 変更ファイル {files_changed}件, 詳細 {summary_path})"
        )

    error_summary = str(summary.get("error_summary", "")).strip() or "詳細は run_summary.json を確認"
    return f"- {skill_name}: 失敗 ({error_summary}, 詳細 {summary_path})"


def render_announcement(args: argparse.Namespace) -> int:
    """manifest からHermes cron用の通知本文を出力する。"""
    manifest = load_json(Path(args.manifest).resolve())
    targets = manifest.get("targets", [])
    if not isinstance(targets, list) or not targets:
        raise ValueError("manifest の targets がありません")

    updated: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for item in targets:
        if not isinstance(item, dict):
            continue
        summary_path = str(item.get("summary_path", "")).strip()
        if not summary_path:
            continue
        summary = load_json(Path(summary_path).resolve())
        status = str(summary.get("status", ""))
        if status == "updated":
            updated.append(summary)
        elif status == "failed":
            failed.append(summary)

    if not updated and not failed:
        print("HEARTBEAT_OK")  # noqa: T201 - cron 応答仕様
        return 0

    lines = [
        "# skill-update 自動実行結果",
        "",
        f"- 実行時刻: {manifest.get('generated_at', '')}",
        f"- 更新あり: {len(updated)}件",
        f"- 失敗: {len(failed)}件",
    ]
    if updated:
        lines.extend(["", "## 更新あり"])
        lines.extend(render_status_line(summary) for summary in updated)
    if failed:
        lines.extend(["", "## 失敗"])
        lines.extend(render_status_line(summary) for summary in failed)

    print("\n".join(lines))  # noqa: T201 - cron 応答仕様
    return 0


def build_parser() -> argparse.ArgumentParser:
    """CLI パーサーを構築する。"""
    parser = argparse.ArgumentParser(description="Automation helper for skill-update")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-targets", help="targets.json を検証する")
    validate_parser.add_argument("--targets", help="targets.json のパス")
    validate_parser.set_defaults(func=validate_targets)

    prepare_parser = subparsers.add_parser("prepare-sweep", help="有効 targets を一括準備する")
    prepare_parser.add_argument("--targets", help="targets.json のパス")
    prepare_parser.add_argument("--runtime-root", help="保存先 .runtime のルート")
    prepare_parser.add_argument("--output", help="manifest の出力先")
    prepare_parser.set_defaults(func=prepare_sweep)

    select_fix_parser = subparsers.add_parser("select-fix-candidate", help="自動修正候補を1件選ぶ")
    select_fix_parser.add_argument("--targets", help="targets.json のパス")
    select_fix_parser.add_argument("--policy", help="auto-fix-policy.json のパス")
    select_fix_parser.add_argument("--runtime-root", help="保存先 .runtime のルート")
    select_fix_parser.add_argument("--candidates", help="feedback candidates.json のパス")
    select_fix_parser.add_argument("--output", help="selection.json の出力先")
    select_fix_parser.set_defaults(func=select_fix_candidate)

    rollback_parser = subparsers.add_parser("create-rollback-point", help="対象スキルの戻しポイントを作る")
    rollback_parser.add_argument("--selection", required=True, help="select-fix-candidate の selection.json")
    rollback_parser.add_argument("--runtime-root", help="保存先 .runtime のルート")
    rollback_parser.add_argument("--output", help="rollback.json の出力先")
    rollback_parser.set_defaults(func=create_rollback_point)

    apply_parser = subparsers.add_parser("apply-fix", help="修正後の変更範囲を記録する")
    apply_parser.add_argument("--rollback", required=True, help="rollback.json のパス")
    apply_parser.add_argument("--output", help="apply_result.json の出力先")
    apply_parser.add_argument("--note", help="修正内容の短い補足")
    apply_parser.set_defaults(func=apply_fix)

    verify_parser = subparsers.add_parser("verify-fix", help="修正後の機械チェックを行う")
    verify_parser.add_argument("--rollback", required=True, help="rollback.json のパス")
    verify_parser.add_argument("--benchmark", help="benchmark.json のパス")
    verify_parser.add_argument("--gate", help="auto_fix_gate.json のパス")
    verify_parser.add_argument("--output", help="verify_result.json の出力先")
    verify_parser.set_defaults(func=verify_fix)

    rollback_fix_parser = subparsers.add_parser("rollback-fix", help="対象スキルだけ戻す")
    rollback_fix_parser.add_argument("--rollback", required=True, help="rollback.json のパス")
    rollback_fix_parser.add_argument("--output", help="rollback_result.json の出力先")
    rollback_fix_parser.set_defaults(func=rollback_fix)

    classify_parser = subparsers.add_parser("classify-failure", help="失敗文面を再試行対象か判定する")
    classify_parser.add_argument("--message", required=True, help="失敗文面")
    classify_parser.add_argument("--policy", help="auto-fix-policy.json のパス")
    classify_parser.add_argument("--output", help="判定結果JSONの出力先")
    classify_parser.set_defaults(func=classify_failure)

    retry_parser = subparsers.add_parser("decide-retry", help="失敗を再試行すべきか判定する")
    retry_parser.add_argument("--message", required=True, help="失敗文面")
    retry_parser.add_argument("--rollback", help="rollback.json のパス")
    retry_parser.add_argument("--state", help="retry_state.json のパス")
    retry_parser.add_argument("--policy", help="auto-fix-policy.json のパス")
    retry_parser.add_argument("--output", help="判定結果JSONの出力先")
    retry_parser.set_defaults(func=decide_retry)

    report_parser = subparsers.add_parser("render-fix-report", help="自動修正結果の報告文を出力する")
    report_parser.add_argument("--selection", required=True, help="selection.json のパス")
    report_parser.add_argument("--rollback", required=True, help="rollback.json のパス")
    report_parser.add_argument("--apply", help="apply_result.json のパス")
    report_parser.add_argument("--verify", help="verify_result.json のパス")
    report_parser.add_argument("--rollback-result", help="rollback_result.json のパス")
    report_parser.add_argument("--output", help="出力JSONのパス")
    report_parser.set_defaults(func=render_fix_report)

    record_parser = subparsers.add_parser("record-run", help="対象1件の結果を記録する")
    record_parser.add_argument("--manifest", required=True, help="prepare-sweep の manifest")
    record_parser.add_argument("--skill-name", required=True, help="対象スキル名")
    record_parser.add_argument(
        "--status",
        required=True,
        choices=("no_change", "updated", "failed"),
        help="実行結果ステータス",
    )
    record_parser.add_argument("--benchmark", help="benchmark.json のパス")
    record_parser.add_argument("--gate", help="auto_fix_gate.json のパス")
    record_parser.add_argument("--files-changed", type=int, default=0, help="変更ファイル数")
    record_parser.add_argument("--error-summary", help="失敗理由の短い要約")
    record_parser.set_defaults(func=record_run)

    announce_parser = subparsers.add_parser("render-announcement", help="cron 通知文を出力する")
    announce_parser.add_argument("--manifest", required=True, help="prepare-sweep の manifest")
    announce_parser.set_defaults(func=render_announcement)
    return parser


def main() -> int:
    """CLI エントリポイント。"""
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
