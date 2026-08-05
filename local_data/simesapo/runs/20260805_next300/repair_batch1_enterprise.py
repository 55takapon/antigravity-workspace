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

HERE = Path(__file__).parent
SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
TARGET = "シート1"
REPLACE_ROWS = [2763, 2784, 2785, 2786, 2787, 2788, 2789]
HEADERS = ["company_name", "url", "address", "phone", "maps_url", "contact_url", "message", "sent_at", "status", "error_reason", "screenshot_path", "provider_used", "提案区分", "", "区分", "検出ワード"]


def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "").lower())


def company_key(value: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|一般社団法人|[・･.,，．_/'\"()（）\[\]［］:：-]", "", norm(value))


def domain(value: str) -> str:
    return (urlparse(value).hostname or "").lower().removeprefix("www.")


with (HERE / "jfea_seed.csv").open(encoding="utf-8-sig", newline="") as handle:
    seed = list(csv.DictReader(handle))
with (HERE / "jfea_audit.csv").open(encoding="utf-8-sig", newline="") as handle:
    decisions = {company_key(row["company_name"]): row["decision"] for row in csv.DictReader(handle)}
with (HERE / "jfea_final50.csv").open(encoding="utf-8-sig", newline="") as handle:
    original = list(csv.DictReader(handle))

bad_names = {company_key(original[index]) for index in []}
original_domains = {domain(row["url"]) for row in original}
candidates = [row for row in seed if decisions.get(company_key(row["company_name"])) == "accept" and domain(row["url"]) not in original_domains and not re.search(r"JFE|ホシザキ|サラヤ", row["company_name"], re.I)]
replacements = candidates[: len(REPLACE_ROWS)]
if len(replacements) != len(REPLACE_ROWS):
    raise SystemExit("replacement_shortfall")

payload = []
for row in replacements:
    values = {**row, "maps_url": "", "message": "", "sent_at": "", "status": "", "error_reason": "", "screenshot_path": "", "provider_used": "", "提案区分": "", "": ""}
    payload.append([values.get(header, "") for header in HEADERS])

book = sheets_io.get_client().open_by_url(SHEET)
ws = book.worksheet(TARGET)
for row_number, values in zip(REPLACE_ROWS, payload):
    ws.update(values=[values], range_name=f"A{row_number}:P{row_number}", value_input_option="RAW")

verified = 0
for row_number, expected in zip(REPLACE_ROWS, payload):
    actual = ws.get(f"A{row_number}:P{row_number}")
    row = (actual[0] if actual else []) + [""] * 16
    verified += row[:16] == expected

with (HERE / "batch1_replacements.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(replacements[0]))
    writer.writeheader()
    writer.writerows(replacements)

print(json.dumps({"replaced_rows": REPLACE_ROWS, "replacement_companies": [row["company_name"] for row in replacements], "verified_exact": verified}, ensure_ascii=False))
if verified != len(REPLACE_ROWS):
    raise SystemExit("replacement_readback_failed")
