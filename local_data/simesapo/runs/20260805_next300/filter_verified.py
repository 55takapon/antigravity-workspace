from __future__ import annotations

import argparse
import csv
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

source = Path(args.input)
output = Path(args.output)
with source.open(encoding="utf-8-sig", newline="") as handle:
    rows = [row for row in csv.DictReader(handle) if row.get("company_confirmed") == "yes" and row.get("contact_url", "").strip()]
fields = list(rows[0]) if rows else []
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print({"input": str(source), "verified_rows": len(rows), "output": str(output)})
