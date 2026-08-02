from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
POOL = BASE / "realestate_candidate_pool.csv"
OLD_KEEP = BASE / "realestate_opener_kept_v3.csv"
OUTPUT = BASE / "realestate_opener_kept_v4.csv"
NEW_KEEP = {
    "conpro-dx.com", "tatelog.biz", "techbull.co.jp", "nexiap.com", "keysapo.com",
    "licks.co.jp", "sawan.ne.jp", "convy.co.jp", "lastcompass.co.jp", "empowerjp.com",
}

def domain(value: str) -> str:
    host = urlparse(value if "://" in (value or "") else "https://" + (value or "")).hostname or ""
    return host.lower().removeprefix("www.")

def read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

old_domains = {domain(r.get("url", "")) for r in read(OLD_KEEP)}
keep_domains = old_domains | NEW_KEEP
pool = read(POOL)
kept = [r for r in pool if domain(r.get("url", "")) in keep_domains]
missing = sorted(keep_domains - {domain(r.get("url", "")) for r in kept})
if missing:
    raise SystemExit(f"missing_from_pool={missing}")
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=pool[0].keys())
    writer.writeheader()
    writer.writerows(kept)
print({"old_keep": len(old_domains), "new_keep": len(NEW_KEEP), "merged": len(kept), "missing": missing})
