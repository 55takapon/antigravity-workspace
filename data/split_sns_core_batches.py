import csv
import json
from pathlib import Path


source = Path("data/sns_verified_pure_new.csv")
output = Path("data/sns_core_batches")
output.mkdir(exist_ok=True)
with source.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
for index in range(0, len(rows), 35):
    batch = rows[index:index + 35]
    (output / f"batch_{index // 35 + 1:02d}.json").write_text(
        json.dumps(batch, ensure_ascii=False), encoding="utf-8"
    )
print(f"records={len(rows)} batches={(len(rows) + 34) // 35}")
