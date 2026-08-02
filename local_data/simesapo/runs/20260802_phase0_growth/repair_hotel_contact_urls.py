from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
POOL = BASE / "hotel_candidate_pool.csv"
FINAL = BASE / "hotel_final_verified_50_v2.csv"
SKILL = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "シート1"
START_ROW = 2216
END_ROW = 2260

def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "").lower())

def company_key(value: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:：-]", "", norm(value))

def domain_key(value: str) -> str:
    host = urlparse(value if "://" in (value or "") else "https://" + (value or "")).hostname or ""
    return host.lower().removeprefix("www.")

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

ap = argparse.ArgumentParser()
ap.add_argument("--write", action="store_true")
args = ap.parse_args()

pool = read_csv(POOL)
final = read_csv(FINAL)
targets = final[: END_ROW - START_ROW + 1]
by_pair = {(company_key(r["company_name"]), domain_key(r["url"])): r["contact_url"].strip() for r in pool}
contacts = []
missing = []
for offset, row in enumerate(targets):
    key = (company_key(row["company_name"]), domain_key(row["url"]))
    contact = by_pair.get(key, "")
    if not contact:
        missing.append({"row": START_ROW + offset, "company_name": row["company_name"], "url": row["url"]})
    contacts.append(contact)
if len(targets) != 45 or len(contacts) != 45 or missing:
    raise SystemExit({"targets": len(targets), "contacts": len(contacts), "missing": missing})

book = sheets_io.get_client().open_by_url(SHEET)
ws = book.worksheet(WORKSHEET)
live = ws.get(f"A{START_ROW}:F{END_ROW}")
identity_errors = []
for i, (sheet_row, expected) in enumerate(zip(live, targets), START_ROW):
    company = sheet_row[0] if len(sheet_row) > 0 else ""
    url = sheet_row[1] if len(sheet_row) > 1 else ""
    if company_key(company) != company_key(expected["company_name"]) or domain_key(url) != domain_key(expected["url"]):
        identity_errors.append({"row": i, "sheet_company": company, "expected_company": expected["company_name"], "sheet_url": url, "expected_url": expected["url"]})
if identity_errors:
    raise SystemExit({"identity_errors": identity_errors})

print({"mode": "write" if args.write else "preview", "rows": 45, "range": f"F{START_ROW}:F{END_ROW}", "matched": 45, "missing": 0})
if not args.write:
    raise SystemExit(0)
ws.update([[x] for x in contacts], f"F{START_ROW}:F{END_ROW}", value_input_option="RAW")
readback = ws.get(f"F{START_ROW}:F{END_ROW}")
actual = [(r[0] if r else "") for r in readback]
errors = [{"row": START_ROW+i, "expected": e, "actual": a} for i, (e, a) in enumerate(zip(contacts, actual)) if e != a]
if len(actual) != 45 or errors:
    raise SystemExit({"readback_rows": len(actual), "errors": errors})
print({"written": 45, "readback": len(actual), "verified_exact": 45, "errors": []})
