from __future__ import annotations

import argparse
import csv
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--field", required=True)
parser.add_argument("--contains", required=True)
args = parser.parse_args()

with Path(args.input).open(encoding="utf-8-sig", newline="") as handle:
    rows = [row for row in csv.DictReader(handle) if args.contains in row.get(args.field, "")]
fields = list(rows[0]) if rows else []
with Path(args.output).open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print({"matched": len(rows), "output": args.output})
