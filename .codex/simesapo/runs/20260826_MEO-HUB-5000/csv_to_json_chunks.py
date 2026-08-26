import csv
import json
import sys
from pathlib import Path

source, out_dir, size = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
rows = list(csv.DictReader(open(source, encoding="utf-8-sig", newline="")))
out_dir.mkdir(parents=True, exist_ok=True)
for index in range(0, len(rows), size):
    path = out_dir / f"chunk_{index // size:03d}.json"
    path.write_text(json.dumps(rows[index:index + size], ensure_ascii=False), encoding="utf-8")
print(f"rows={len(rows)} chunks={(len(rows) + size - 1) // size}")
