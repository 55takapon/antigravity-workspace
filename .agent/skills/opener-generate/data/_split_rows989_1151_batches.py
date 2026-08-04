from __future__ import annotations

import csv
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
SOURCE = DATA_DIR / "_input_rows989_1151_current.csv"
BATCHES = [(989, 1038), (1039, 1088), (1089, 1138), (1139, 1151)]


def main() -> int:
    rows = list(csv.DictReader(SOURCE.open(encoding="utf-8", newline="")))
    for start, end in BATCHES:
        selected = [row for row in rows if start <= int(row["_row"]) <= end]
        out = DATA_DIR / f"_input_rows{start}_{end}_current.csv"
        with out.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(selected)
        print(f"{start}-{end}: {len(selected)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
