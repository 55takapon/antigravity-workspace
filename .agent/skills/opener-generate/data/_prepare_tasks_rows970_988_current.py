from __future__ import annotations

import csv
import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
INPUT_CSV = DATA_DIR / "_input_rows970_988_current.csv"
RAW_TASKS = DATA_DIR / "_tasks_rows970_988_current_raw.json"
OUTPUT_TASKS = DATA_DIR / "_tasks_rows970_988_current.json"
RESULTS = DATA_DIR / "_results_rows970_988_current.json"
BLOCKED_ROWS = {970, 971, 972, 980}


def main() -> int:
    inputs = list(csv.DictReader(INPUT_CSV.open(encoding="utf-8-sig", newline="")))
    raw_tasks = json.loads(RAW_TASKS.read_text(encoding="utf-8"))
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    if len(inputs) != len(raw_tasks):
        raise SystemExit(f"input/task count mismatch: {len(inputs)} != {len(raw_tasks)}")

    eligible = []
    for input_row, task in zip(inputs, raw_tasks, strict=True):
        row_no = int(input_row["_row"])
        if input_row["company_name"] != task["company_name"] or input_row["url"] != task["url"]:
            raise SystemExit(f"row mapping mismatch at physical row {row_no}")
        if row_no in BLOCKED_ROWS:
            continue
        eligible.append({**task, "_row": row_no})

    expected_keys = {str(task["idx"]) for task in eligible}
    if set(results) != expected_keys:
        raise SystemExit(
            f"result keys mismatch: missing={sorted(expected_keys - set(results))} "
            f"extra={sorted(set(results) - expected_keys)}"
        )
    OUTPUT_TASKS.write_text(json.dumps(eligible, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"eligible={len(eligible)} blocked={len(BLOCKED_ROWS)} tasks={OUTPUT_TASKS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
