import csv
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
POOL = BASE / "construction_candidate_pool.csv"
URLS = BASE / "construction_keep_urls.txt"
OUTPUT = BASE / "construction_opener_kept.csv"

def domain(value):
    host = urlparse(value if "://" in (value or "") else "https://" + (value or "")).hostname or ""
    return host.lower().removeprefix("www.")

with POOL.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
keep = {domain(x.strip()) for x in URLS.read_text(encoding="utf-8-sig").splitlines() if x.strip()}
out = [r for r in rows if domain(r.get("url", "")) in keep]
missing = sorted(keep - {domain(r.get("url", "")) for r in out})
if missing:
    raise SystemExit(f"missing={missing}")
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(out)
print({"pool": len(rows), "keep": len(keep), "merged": len(out), "missing": missing})
