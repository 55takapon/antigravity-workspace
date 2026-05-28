#!/usr/bin/env python3
"""skill-update の benchmark を集計する。"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))
CONFIG_ORDER = ("with_skill", "old_skill", "without_skill")


def configure_logging() -> None:
    """標準出力向けロギング設定。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def load_json(path: Path) -> dict[str, Any]:
    """JSON ファイルを辞書として読む。"""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON の最上位が辞書ではありません: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    """JSON を保存する。"""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def safe_mean(values: list[float]) -> float:
    """空配列を考慮した平均値。"""
    return round(statistics.mean(values), 3) if values else 0.0


def safe_stddev(values: list[float]) -> float:
    """要素数が不足していても扱える標準偏差。"""
    return round(statistics.pstdev(values), 3) if len(values) >= 2 else 0.0


def load_expectations(grading_path: Path) -> list[dict[str, Any]]:
    """grading.json の expectations を返す。"""
    if not grading_path.is_file():
        return []
    grading = load_json(grading_path)
    expectations = grading.get("expectations", [])
    return [item for item in expectations if isinstance(item, dict)]


def collect_output_files(output_dir: Path) -> list[str]:
    """outputs/ 配下のファイル一覧を返す。"""
    if not output_dir.is_dir():
        return []
    return sorted(str(path.relative_to(output_dir)) for path in output_dir.rglob("*") if path.is_file())


def load_timing(timing_path: Path) -> dict[str, float]:
    """timing.json を読む。"""
    if not timing_path.is_file():
        return {"total_tokens": 0.0, "total_duration_seconds": 0.0}
    timing = load_json(timing_path)
    return {
        "total_tokens": float(timing.get("total_tokens") or 0.0),
        "total_duration_seconds": float(timing.get("total_duration_seconds") or 0.0),
    }


def build_eval_summary(eval_dir: Path, config_name: str) -> dict[str, Any] | None:
    """評価ケース1件ぶんの集計を返す。"""
    config_dir = eval_dir / config_name
    if not config_dir.is_dir():
        return None

    metadata = load_json(eval_dir / "eval_metadata.json")
    expectations = load_expectations(config_dir / "grading.json")
    timing = load_timing(config_dir / "timing.json")
    output_files = collect_output_files(config_dir / "outputs")
    passed_count = sum(1 for item in expectations if bool(item.get("passed")))

    return {
        "eval_name": metadata.get("eval_name", eval_dir.name),
        "eval_id": metadata.get("eval_id"),
        "prompt": metadata.get("prompt", ""),
        "assertions_total": len(expectations),
        "assertions_passed": passed_count,
        "output_files_count": len(output_files),
        "output_files": output_files,
        "total_tokens": timing["total_tokens"],
        "total_duration_seconds": timing["total_duration_seconds"],
    }


def build_config_metrics(eval_summaries: list[dict[str, Any]], name: str, label: str) -> dict[str, Any]:
    """設定ごとの集計値を計算する。"""
    assertion_totals = [int(item["assertions_total"]) for item in eval_summaries]
    assertion_passed = [int(item["assertions_passed"]) for item in eval_summaries]
    token_values = [float(item["total_tokens"]) for item in eval_summaries]
    duration_values = [float(item["total_duration_seconds"]) for item in eval_summaries]
    output_counts = [int(item["output_files_count"]) for item in eval_summaries]

    zero_assertion_evals = [
        str(item.get("eval_name") or "")
        for item in eval_summaries
        if int(item["assertions_total"]) == 0
    ]
    if zero_assertion_evals:
        raise ValueError(
            f"{name} に assertions_total=0 の評価ケースがあります: {', '.join(zero_assertion_evals)}"
        )

    assertions_total = sum(assertion_totals)
    assertions_passed_total = sum(assertion_passed)
    pass_rate = round((assertions_passed_total / assertions_total) * 100, 3) if assertions_total else 0.0

    return {
        "name": name,
        "label": label,
        "eval_count": len(eval_summaries),
        "assertions_total": assertions_total,
        "assertions_passed": assertions_passed_total,
        "pass_rate": pass_rate,
        "mean_tokens": safe_mean(token_values),
        "stddev_tokens": safe_stddev(token_values),
        "mean_duration_seconds": safe_mean(duration_values),
        "stddev_duration_seconds": safe_stddev(duration_values),
        "output_files_total": sum(output_counts),
        "evals": eval_summaries,
    }


def comparison_name(with_skill_name: str, baseline_name: str) -> str:
    """比較名を作る。"""
    return f"{with_skill_name}_vs_{baseline_name}"


def build_comparison(with_skill: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    """改善版と baseline の差分を計算する。"""
    pass_rate_delta = round(float(with_skill["pass_rate"]) - float(baseline["pass_rate"]), 3)
    mean_tokens_delta = round(float(with_skill["mean_tokens"]) - float(baseline["mean_tokens"]), 3)
    mean_duration_delta = round(
        float(with_skill["mean_duration_seconds"]) - float(baseline["mean_duration_seconds"]),
        3,
    )
    output_collapse_detected = (
        int(with_skill["output_files_total"]) == 0 and int(baseline["output_files_total"]) > 0
    )

    regression_detected = False
    baseline_evals = {item["eval_name"]: item for item in baseline.get("evals", [])}
    for eval_item in with_skill.get("evals", []):
        baseline_eval = baseline_evals.get(eval_item["eval_name"])
        if baseline_eval is None:
            continue
        if int(eval_item["assertions_passed"]) < int(baseline_eval["assertions_passed"]):
            regression_detected = True
            break

    return {
        "name": comparison_name(str(with_skill["name"]), str(baseline["name"])),
        "pass_rate_delta": pass_rate_delta,
        "mean_tokens_delta": mean_tokens_delta,
        "mean_duration_seconds_delta": mean_duration_delta,
        "regression_detected": regression_detected or pass_rate_delta < 0,
        "output_collapse_detected": output_collapse_detected,
    }


def find_eval_dirs(iteration_dir: Path) -> list[Path]:
    """iteration 配下の評価ケースディレクトリを返す。"""
    eval_dirs = []
    for child in sorted(iteration_dir.iterdir()):
        if child.is_dir() and (child / "eval_metadata.json").is_file():
            eval_dirs.append(child)
    if not eval_dirs:
        raise ValueError(f"評価ケースが見つかりません: {iteration_dir}")
    return eval_dirs


def markdown_for_benchmark(benchmark: dict[str, Any]) -> str:
    """benchmark.md の本文を組み立てる。"""
    lines = [
        f"# Benchmark: {benchmark['skill_name']}",
        "",
        f"- 生成日時: {benchmark['generated_at']}",
        f"- iteration: `{benchmark['iteration_dir']}`",
        f"- baseline: `{benchmark['baseline_name']}`",
        "",
        "| 設定 | eval数 | pass率 | 平均tokens | 平均秒数 | 出力ファイル数 |",
        "|:-----|------:|------:|-----------:|----------:|---------------:|",
    ]
    for config in benchmark["configs"]:
        lines.append(
            "| {label} | {eval_count} | {pass_rate:.3f}% | {mean_tokens:.3f} | "
            "{mean_duration_seconds:.3f} | {output_files_total} |".format(**config)
        )

    if benchmark["comparisons"]:
        lines.extend(
            [
                "",
                "## 差分",
                "",
                "| 比較 | pass率差分 | 平均tokens差分 | 平均秒数差分 | 回帰 | 出力崩壊 |",
                "|:-----|-----------:|---------------:|--------------:|:----|:---------|",
            ]
        )
        for item in benchmark["comparisons"]:
            lines.append(
                "| {name} | {pass_rate_delta:.3f} | {mean_tokens_delta:.3f} | "
                "{mean_duration_seconds_delta:.3f} | {regression_detected} | "
                "{output_collapse_detected} |".format(**item)
            )
    return "\n".join(lines) + "\n"


def aggregate(iteration_dir: Path, skill_name: str) -> dict[str, Any]:
    """iteration ディレクトリを集計する。"""
    eval_dirs = find_eval_dirs(iteration_dir)
    config_metrics: list[dict[str, Any]] = []

    for config_name in CONFIG_ORDER:
        eval_summaries = []
        for eval_dir in eval_dirs:
            summary = build_eval_summary(eval_dir, config_name)
            if summary is not None:
                eval_summaries.append(summary)
        if not eval_summaries:
            continue
        label = "改善版" if config_name == "with_skill" else "旧版" if config_name == "old_skill" else "baseline"
        config_metrics.append(build_config_metrics(eval_summaries, config_name, label))

    if not config_metrics:
        raise ValueError("集計対象の設定が見つかりません")

    baseline_name = "old_skill" if any(item["name"] == "old_skill" for item in config_metrics) else "without_skill"
    benchmark = {
        "skill_name": skill_name,
        "generated_at": datetime.now(JST).isoformat(),
        "iteration_dir": str(iteration_dir.resolve()),
        "baseline_name": baseline_name,
        "configs": config_metrics,
        "comparisons": [],
    }

    with_skill = next((item for item in config_metrics if item["name"] == "with_skill"), None)
    baseline = next((item for item in config_metrics if item["name"] == baseline_name), None)
    if with_skill and baseline and with_skill is not baseline:
        benchmark["comparisons"].append(build_comparison(with_skill, baseline))

    return benchmark


def main() -> int:
    """CLI エントリポイント。"""
    configure_logging()
    parser = argparse.ArgumentParser(description="Aggregate benchmark data for skill-update")
    parser.add_argument("iteration_dir", help="iteration-N のパス")
    parser.add_argument("--skill-name", required=True, help="対象スキル名")
    parser.add_argument("--json-output", help="benchmark.json の出力先")
    parser.add_argument("--md-output", help="benchmark.md の出力先")
    args = parser.parse_args()

    iteration_dir = Path(args.iteration_dir).resolve()
    json_output = Path(args.json_output).resolve() if args.json_output else iteration_dir / "benchmark.json"
    md_output = Path(args.md_output).resolve() if args.md_output else iteration_dir / "benchmark.md"

    try:
        benchmark = aggregate(iteration_dir, args.skill_name)
        write_json(json_output, benchmark)
        md_output.write_text(markdown_for_benchmark(benchmark), encoding="utf-8")
    except (FileNotFoundError, OSError, ValueError) as exc:
        LOGGER.error("エラー: %s", exc)
        return 1

    LOGGER.info("benchmark を出力しました: %s", json_output)
    LOGGER.info("benchmark markdown を出力しました: %s", md_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
