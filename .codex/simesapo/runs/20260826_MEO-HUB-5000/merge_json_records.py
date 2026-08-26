import json
import sys
from pathlib import Path


rows = []
for source in sys.argv[2:]:
    rows.extend(json.loads(Path(source).read_text(encoding="utf-8-sig")))
Path(sys.argv[1]).write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"rows={len(rows)}")
