from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


KEYWORDS = (
    "理念", "MISSION", "Mission", "ミッション", "想い", "強み", "専門", "特化", "一貫",
    "創業", "支援", "伴走", "ワンストップ", "課題", "成果", "地域", "デザイン",
    "マーケティング", "広告", "調査", "プロモーション", "ブランド", "お客様", "クライアント",
)
DROP = re.compile(r"^(HOME|TOP|CONTACT|SERVICE|COMPANY|WORKS|NEWS|MENU|Copyright|©|〒|TEL|FAX)$", re.I)


def clean(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks")
    ap.add_argument("input_csv")
    ap.add_argument("output")
    args = ap.parse_args()
    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    rows = list(csv.DictReader(Path(args.input_csv).open(encoding="utf-8", newline="")))
    if len(tasks) != len(rows):
        raise SystemExit("tasks/input count mismatch")
    output = []
    for task, row in zip(tasks, rows, strict=True):
        raw_lines = [clean(line) for line in (task.get("hp_text") or "").splitlines()]
        lines = []
        seen = set()
        for index, line in enumerate(raw_lines):
            if not 10 <= len(line) <= 180 or DROP.match(line) or line in seen:
                continue
            seen.add(line)
            score = sum(3 for keyword in KEYWORDS if keyword in line)
            score += 2 if any(mark in line for mark in ("『", "「", "“", "”")) else 0
            score += 1 if re.search(r"\d", line) else 0
            score += max(0, 3 - index // 20)
            lines.append((score, index, line))
        lines.sort(key=lambda item: (-item[0], item[1]))
        picked = []
        for _, _, line in lines:
            short = line[:140]
            if any(short in prior or prior in short for prior in picked):
                continue
            picked.append(short)
            if len(picked) == 2:
                break
        output.append(
            {
                "row": int(row["_row"]),
                "idx": int(task["idx"]),
                "company": row["company_name"],
                "url": row["url"],
                "signals": picked,
            }
        )
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
