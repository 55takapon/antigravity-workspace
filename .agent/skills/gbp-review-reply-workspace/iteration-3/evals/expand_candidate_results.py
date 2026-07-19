#!/usr/bin/env python
"""Validate and expand iteration-3 candidate evaluation result parts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PART_FILES = (
    "candidate-results-01-17.json",
    "candidate-results-18-34.json",
)
EXPECTED_IDS = set(range(1, 35))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be an object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_result(iteration_root: Path, result: dict[str, Any]) -> tuple[dict[str, Any], Path]:
    eval_id = result.get("id")
    eval_name = result.get("eval_name")
    require(isinstance(eval_id, int), "result id must be an integer")
    require(isinstance(eval_name, str) and bool(eval_name), f"invalid eval_name for id {eval_id}")
    require("/" not in eval_name and "\\" not in eval_name, f"unsafe eval_name: {eval_name}")

    eval_dir = (iteration_root / eval_name).resolve()
    require(eval_dir.is_relative_to(iteration_root), f"eval path escapes iteration root: {eval_name}")
    metadata_path = eval_dir / "eval_metadata.json"
    require(metadata_path.is_file(), f"missing metadata: {metadata_path}")
    metadata = load_json(metadata_path)
    require(metadata.get("eval_id") == eval_id, f"metadata id mismatch: {eval_name}")
    require(metadata.get("eval_name") == eval_name, f"metadata name mismatch: {eval_name}")

    metadata_assertions = metadata.get("assertions")
    require(isinstance(metadata_assertions, list) and len(metadata_assertions) == 4,
            f"metadata must have exactly 4 assertions: {eval_name}")

    response = result.get("response")
    require(isinstance(response, str) and bool(response.strip()), f"empty response: {eval_name}")

    grading = result.get("grading")
    require(isinstance(grading, dict), f"invalid grading: {eval_name}")
    expectations = grading.get("expectations")
    require(isinstance(expectations, list) and len(expectations) == 4,
            f"grading must have exactly 4 expectations: {eval_name}")
    metadata_texts = [item.get("text") for item in metadata_assertions]
    grading_texts = [item.get("text") for item in expectations]
    require(grading_texts == metadata_texts, f"assertion text mismatch: {eval_name}")
    for expectation in expectations:
        require(isinstance(expectation.get("passed"), bool), f"non-boolean passed: {eval_name}")
        require(isinstance(expectation.get("evidence"), str) and bool(expectation["evidence"].strip()),
                f"missing evidence: {eval_name}")

    recalculated_critical = any(
        item["text"].startswith("[critical]") and not item["passed"]
        for item in expectations
    )
    require(grading.get("critical_failure") is recalculated_critical,
            f"critical_failure mismatch: {eval_name}")

    rubric = result.get("rubric")
    require(isinstance(rubric, dict), f"invalid rubric: {eval_name}")
    dimensions = rubric.get("dimensions")
    require(isinstance(dimensions, list) and len(dimensions) == 16,
            f"rubric must have exactly 16 dimensions: {eval_name}")
    scores: list[int] = []
    for dimension in dimensions:
        score = dimension.get("score")
        require(isinstance(score, int) and 0 <= score <= 2, f"invalid rubric score: {eval_name}")
        require(isinstance(dimension.get("reason"), str) and bool(dimension["reason"].strip()),
                f"missing rubric reason: {eval_name}")
        scores.append(score)
    require(rubric.get("total_score") == sum(scores), f"rubric total mismatch: {eval_name}")
    require(rubric.get("max_score") == 32, f"rubric max mismatch: {eval_name}")

    timing = result.get("timing")
    require(isinstance(timing, dict), f"invalid timing: {eval_name}")
    require(timing.get("measurement_status") == "unavailable_in_subagent_interface",
            f"invalid timing status: {eval_name}")
    for key in ("total_tokens", "total_duration_seconds"):
        require(key in timing and timing[key] is None, f"timing {key} must be null: {eval_name}")
    require("duration_ms" not in timing or timing["duration_ms"] is None,
            f"timing duration_ms must be null when present: {eval_name}")
    timing.setdefault("duration_ms", None)

    return result, eval_dir / "with_skill"


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    evals_dir = Path(__file__).resolve().parent
    iteration_root = evals_dir.parent.resolve()
    manifest_path = iteration_root / "iteration_manifest.json"
    require(manifest_path.is_file(), f"missing iteration manifest: {manifest_path}")
    manifest = load_json(manifest_path)
    require(Path(manifest.get("iteration_dir", "")).resolve() == iteration_root,
            "iteration root does not match manifest")

    all_results: list[dict[str, Any]] = []
    for filename in PART_FILES:
        part_path = evals_dir / filename
        require(part_path.is_file(), f"missing candidate result part: {part_path}")
        part = load_json(part_path)
        results = part.get("results")
        require(isinstance(results, list), f"results must be an array: {part_path}")
        all_results.extend(results)

    ids = [item.get("id") for item in all_results]
    names = [item.get("eval_name") for item in all_results]
    require(len(all_results) == 34, "candidate result parts must contain exactly 34 results")
    require(set(ids) == EXPECTED_IDS and len(set(ids)) == 34, "result IDs must be unique 1..34")
    require(len(set(names)) == 34, "eval_name values must be unique")

    validated: list[tuple[dict[str, Any], Path]] = []
    for result in sorted(all_results, key=lambda item: item["id"]):
        validated.append(validate_result(iteration_root, result))

    # No writes occur before every part and every case passes validation.
    for result, config_dir in validated:
        output_dir = config_dir / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "response.md").write_text(
            result["response"].rstrip() + "\n",
            encoding="utf-8",
        )
        write_json(config_dir / "grading.json", result["grading"])
        write_json(config_dir / "rubric-scores.json", result["rubric"])
        write_json(config_dir / "timing.json", result["timing"])

    print(f"expanded {len(validated)} candidate results under {iteration_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
