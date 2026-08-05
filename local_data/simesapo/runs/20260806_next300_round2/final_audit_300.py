from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
TARGET = "シート1"
START, END = 3363, 3662
HERE = Path(__file__).parent


def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "").lower())


def company_key(value: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|一般社団法人|一般財団法人|[・･.,，．_/'\"()（）\[\]［］:：-]", "", norm(value))


def domain_key(value: str) -> str:
    return (urlparse(value).hostname or "").lower().removeprefix("www.")


def phone_key(value: str) -> str:
    return re.sub(r"\D", "", value or "")


book = sheets_io.get_client().open_by_url(SHEET)
target = book.worksheet(TARGET)
headers = target.get("A1:P1")[0]
rows = target.get(f"A{START}:P{END}")
rows = [row + [""] * (16 - len(row)) for row in rows]

required = {"company_name": 0, "url": 1, "contact_url": 5, "区分": 14, "検出ワード": 15}
missing = {name: [START + i for i, row in enumerate(rows) if not row[index].strip()] for name, index in required.items()}
missing = {name: values for name, values in missing.items() if values}
internal_company, internal_domain = {}, {}
for i, row in enumerate(rows, start=START):
    internal_company.setdefault(company_key(row[0]), []).append(i)
    internal_domain.setdefault(domain_key(row[1]), []).append(i)
internal_company = {k: v for k, v in internal_company.items() if k and len(v) > 1}
internal_domain = {k: v for k, v in internal_domain.items() if k and len(v) > 1}

new_names = {company_key(row[0]) for row in rows}
new_domains = {domain_key(row[1]) for row in rows}
new_phones = {phone_key(row[3]) for row in rows if phone_key(row[3])}
external_conflicts = []
for ws in book.worksheets():
    values = ws.get_all_values()
    for row_number, row in enumerate(values[1:], start=2):
        if ws.title == TARGET and START <= row_number <= END:
            continue
        padded = row + [""] * (4 - len(row))
        reasons = []
        if padded[0] and company_key(padded[0]) in new_names:
            reasons.append("company")
        if padded[1] and domain_key(padded[1]) in new_domains:
            reasons.append("domain")
        if padded[3] and phone_key(padded[3]) and phone_key(padded[3]) in new_phones:
            reasons.append("phone")
        if reasons:
            external_conflicts.append({"worksheet": ws.title, "row": row_number, "company_name": padded[0], "reasons": reasons})

snapshot = HERE / "final_300_readback.csv"
with snapshot.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(headers)
    writer.writerows(rows)

result = {
    "range": f"{TARGET}!A{START}:P{END}",
    "rows": len(rows),
    "missing_required": missing,
    "internal_company_duplicates": internal_company,
    "internal_domain_duplicates": internal_domain,
    "external_conflicts": external_conflicts,
    "snapshot": str(snapshot),
}
print(json.dumps(result, ensure_ascii=False))
if len(rows) != 300 or missing or internal_company or internal_domain or external_conflicts:
    raise SystemExit("final_audit_failed")
