#!/usr/bin/env python3
"""skill-update の反復実行を補助する。"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
ALLOWED_CHANGE_KINDS = {
    "structure",
    "description",
    "examples",
    "references",
    "light_script",
}
DEFAULT_OUTPUT_DIRS = ("with_skill", "old_skill")


@dataclass(frozen=True)
class EvalCase:
    """1件分の評価ケース。"""

    eval_id: int
    prompt: str
    expected_output: str
    files: list[str]
    assertions: list[dict[str, Any]]
    eval_name: str


def configure_logging() -> None:
    """標準出力向けの簡易ロガーを設定する。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def load_json(path: Path) -> dict[str, Any]:
    """JSON ファイルを読み込む。"""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSONの最上位は辞書である必要があります: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    """JSON を UTF-8 で保存する。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def ensure_skill_path(skill_path: Path) -> Path:
    """対象スキルの SKILL.md 存在を確認する。"""
    resolved = skill_path.resolve()
    skill_md = resolved / "SKILL.md"
    if not resolved.is_dir() or not skill_md.is_file():
        raise FileNotFoundError(f"対象スキルが見つかりません: {resolved}")
    return resolved


def skill_update_root() -> Path:
    """skill-update スキルのルートを返す。"""
    return Path(__file__).resolve().parents[1]


def default_workspace_dir(skill_path: Path) -> Path:
    """既定の作業領域を返す。"""
    return skill_path.parent / f"{skill_path.name}-workspace"


def latest_iteration_dir(workspace_dir: Path) -> Path:
    """最新の iteration ディレクトリを返す。"""
    existing: list[tuple[int, Path]] = []
    if workspace_dir.exists():
        for child in workspace_dir.iterdir():
            match = re.fullmatch(r"iteration-(\d+)", child.name)
            if match:
                existing.append((int(match.group(1)), child))
    if not existing:
        raise FileNotFoundError(f"iteration ディレクトリが見つかりません: {workspace_dir}")
    return sorted(existing, key=lambda item: item[0])[-1][1]


def sanitize_eval_name(raw_name: str, fallback: str) -> str:
    """評価ケース名を安全なディレクトリ名に変換する。"""
    compact = re.sub(r"\s+", "-", raw_name.strip().lower())
    compact = re.sub(r"[^a-z0-9_-]+", "-", compact)
    compact = re.sub(r"-{2,}", "-", compact).strip("-")
    return compact or fallback


def build_eval_case(index: int, raw_eval: dict[str, Any]) -> EvalCase:
    """辞書から EvalCase を生成する。"""
    prompt = str(raw_eval.get("prompt", "")).strip()
    expected_output = str(raw_eval.get("expected_output", "")).strip()
    if not prompt:
        raise ValueError(f"evals[{index}] の prompt が空です")
    if not expected_output:
        raise ValueError(f"evals[{index}] の expected_output が空です")

    eval_id = int(raw_eval.get("id", index + 1))
    files = raw_eval.get("files", [])
    if not isinstance(files, list):
        raise ValueError(f"evals[{index}] の files は配列である必要があります")

    assertions = raw_eval.get("assertions", [])
    if not isinstance(assertions, list):
        raise ValueError(f"evals[{index}] の assertions は配列である必要があります")

    raw_name = str(raw_eval.get("eval_name", "")).strip()
    fallback_name = f"eval-{eval_id}"
    eval_name = sanitize_eval_name(raw_name or prompt[:40], fallback_name)
    return EvalCase(
        eval_id=eval_id,
        prompt=prompt,
        expected_output=expected_output,
        files=[str(item) for item in files],
        assertions=[item for item in assertions if isinstance(item, dict)],
        eval_name=eval_name,
    )


def load_evals(evals_path: Path) -> tuple[str, list[EvalCase]]:
    """評価ケース一覧を読み込む。"""
    payload = load_json(evals_path)
    skill_name = str(payload.get("skill_name", "")).strip()
    raw_evals = payload.get("evals")
    if not skill_name:
        raise ValueError(f"skill_name が空です: {evals_path}")
    if not isinstance(raw_evals, list) or len(raw_evals) < 2:
        raise ValueError("評価ケースは最低2件必要です")

    evals = [build_eval_case(index, item) for index, item in enumerate(raw_evals)]
    return skill_name, evals


def copy_evals_file(source: Path, destination: Path) -> None:
    """evals.json を作業領域へコピーする。"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def next_iteration_dir(workspace_dir: Path) -> Path:
    """次の iteration ディレクトリを返す。"""
    existing: list[int] = []
    if workspace_dir.exists():
        for child in workspace_dir.iterdir():
            match = re.fullmatch(r"iteration-(\d+)", child.name)
            if match:
                existing.append(int(match.group(1)))
    next_index = max(existing, default=0) + 1
    return workspace_dir / f"iteration-{next_index}"


def snapshot_skill(skill_path: Path, snapshot_root: Path) -> Path:
    """対象スキルを旧版スナップショットとして保存する。"""
    snapshot_dir = snapshot_root / skill_path.name
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    shutil.copytree(
        skill_path,
        snapshot_dir,
        ignore=shutil.ignore_patterns(".runtime", ".runtime*", "__pycache__"),
    )
    return snapshot_dir


def prepare_iteration(args: argparse.Namespace) -> int:
    """prepare サブコマンド本体。"""
    skill_path = ensure_skill_path(Path(args.skill))
    workspace_dir = Path(args.workspace).resolve() if args.workspace else default_workspace_dir(skill_path)
    evals_source = Path(args.evals_file).resolve() if args.evals_file else workspace_dir / "evals" / "evals.json"

    if not evals_source.is_file():
        raise FileNotFoundError(f"evals.json が見つかりません: {evals_source}")

    workspace_dir.mkdir(parents=True, exist_ok=True)
    evals_destination = workspace_dir / "evals" / "evals.json"
    if evals_source != evals_destination:
        copy_evals_file(evals_source, evals_destination)
    elif not evals_destination.exists():
        copy_evals_file(evals_source, evals_destination)

    skill_name, evals = load_evals(evals_destination)
    iteration_dir = next_iteration_dir(workspace_dir)
    iteration_dir.mkdir(parents=True, exist_ok=False)

    snapshot_root = workspace_dir / "skill-snapshot" / iteration_dir.name
    snapshot_dir = snapshot_skill(skill_path, snapshot_root)

    eval_manifests = []
    for eval_case in evals:
        eval_dir = iteration_dir / eval_case.eval_name
        eval_dir.mkdir(parents=True, exist_ok=False)

        metadata = {
            "eval_id": eval_case.eval_id,
            "eval_name": eval_case.eval_name,
            "prompt": eval_case.prompt,
            "expected_output": eval_case.expected_output,
            "assertions": eval_case.assertions,
            "files": eval_case.files,
        }
        write_json(eval_dir / "eval_metadata.json", metadata)

        for output_name in DEFAULT_OUTPUT_DIRS:
            (eval_dir / output_name / "outputs").mkdir(parents=True, exist_ok=True)

        eval_manifests.append(
            {
                "eval_id": eval_case.eval_id,
                "eval_name": eval_case.eval_name,
                "path": str(eval_dir),
            }
        )

    manifest = {
        "skill_name": skill_name,
        "target_skill_path": str(skill_path),
        "workspace_dir": str(workspace_dir),
        "iteration_dir": str(iteration_dir),
        "snapshot_dir": str(snapshot_dir),
        "evals_path": str(evals_destination),
        "evals": eval_manifests,
    }
    write_json(iteration_dir / "iteration_manifest.json", manifest)
    LOGGER.info("iteration を準備しました: %s", iteration_dir)
    return 0


def get_config_metrics(configs: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    """benchmark の config を名前で取得する。"""
    for config in configs:
        if config.get("name") == name:
            return config
    return None


def detect_output_collapse(comparisons: list[dict[str, Any]]) -> bool:
    """比較結果に出力崩壊フラグがあるか確認する。"""
    return any(bool(item.get("output_collapse_detected")) for item in comparisons)


def gate_iteration(args: argparse.Namespace) -> int:
    """gate サブコマンド本体。"""
    benchmark_path = Path(args.benchmark).resolve()
    payload = load_json(benchmark_path)
    configs = payload.get("configs", [])
    comparisons = payload.get("comparisons", [])
    if not isinstance(configs, list) or not configs:
        raise ValueError("benchmark.json の configs が不正です")
    if not isinstance(comparisons, list):
        raise ValueError("benchmark.json の comparisons が不正です")

    change_kinds = [item.strip() for item in args.change_kind]
    invalid_kinds = [item for item in change_kinds if item not in ALLOWED_CHANGE_KINDS]
    if invalid_kinds:
        raise ValueError(f"未知の change_kind です: {', '.join(invalid_kinds)}")

    with_skill = get_config_metrics(configs, "with_skill")
    baseline_name = str(payload.get("baseline_name", "")).strip() or "old_skill"
    baseline = get_config_metrics(configs, baseline_name)
    if with_skill is None or baseline is None:
        raise ValueError("with_skill または baseline の metrics が見つかりません")

    pass_rate_after = float(with_skill.get("pass_rate") or 0.0)
    pass_rate_before = float(baseline.get("pass_rate") or 0.0)
    assertions_total_after = int(with_skill.get("assertions_total") or 0)
    assertions_total_before = int(baseline.get("assertions_total") or 0)
    regression_detected = pass_rate_after < pass_rate_before
    output_collapse_detected = detect_output_collapse(comparisons)

    reasons: list[str] = []
    allowed = True

    if not change_kinds:
        allowed = False
        reasons.append("change_kind が指定されていない")

    if regression_detected:
        allowed = False
        reasons.append("改善版の pass率が旧版より低い")

    if assertions_total_after == 0 or assertions_total_before == 0:
        allowed = False
        reasons.append("assertions_total が0のため評価未実施")

    if output_collapse_detected:
        allowed = False
        reasons.append("出力崩壊が検出された")

    if allowed:
        reasons.append("許可条件を全て満たした")

    gate_result = {
        "allowed": allowed,
        "change_kinds": change_kinds,
        "pass_rate_before": round(pass_rate_before, 3),
        "pass_rate_after": round(pass_rate_after, 3),
        "assertions_total_before": assertions_total_before,
        "assertions_total_after": assertions_total_after,
        "regression_detected": regression_detected,
        "output_collapse_detected": output_collapse_detected,
        "benchmark_path": str(benchmark_path),
        "reasons": reasons,
    }

    output_path = Path(args.output).resolve() if args.output else benchmark_path.with_name("auto_fix_gate.json")
    write_json(output_path, gate_result)
    LOGGER.info("自動修正ゲートを出力しました: %s", output_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """CLI パーサーを構築する。"""
    parser = argparse.ArgumentParser(description="skill-update iteration helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="評価ケースと iteration を準備する")
    prepare_parser.add_argument("--skill", required=True, help="対象スキルのディレクトリ")
    prepare_parser.add_argument("--workspace", help="作業領域ディレクトリ")
    prepare_parser.add_argument("--evals-file", help="evals.json のパス")
    prepare_parser.set_defaults(func=prepare_iteration)

    gate_parser = subparsers.add_parser("gate", help="自動修正ゲートを判定する")
    gate_parser.add_argument("--benchmark", required=True, help="benchmark.json のパス")
    gate_parser.add_argument("--change-kind", action="append", default=[], help="変更種類")
    gate_parser.add_argument("--output", help="出力先 auto_fix_gate.json")
    gate_parser.set_defaults(func=gate_iteration)
    return parser


def main() -> int:
    """エントリポイント。"""
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError, OSError) as exc:
        LOGGER.error("エラー: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
