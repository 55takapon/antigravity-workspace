from __future__ import annotations

import argparse
import csv
from pathlib import Path
from urllib.parse import urlparse

parser = argparse.ArgumentParser()
parser.add_argument("--inputs", nargs="+", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

rows = []
fields = []
seen = set()
for item in args.inputs:
    with Path(item).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            for field in row:
                if field not in fields:
                    fields.append(field)
            key = (urlparse(row.get("url", "")).hostname or "").lower().removeprefix("www.")
            if key and key not in seen:
                seen.add(key)
                rows.append(row)

with Path(args.output).open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
print({"inputs": len(args.inputs), "unique_domains": len(rows), "output": args.output})
