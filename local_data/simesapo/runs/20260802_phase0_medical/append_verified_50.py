from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / ".agent" / "skills" / "simesapo-sales-skills-dist" / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
TARGET = "シート1"
HERE = Path(__file__).parent
CSV_PATH = HERE / "final_verified_50.csv"
HEADERS = [
    "company_name", "url", "address", "phone", "maps_url", "contact_url",
    "message", "sent_at", "status", "error_reason", "screenshot_path",
    "provider_used", "提案区分", "", "区分", "検出ワード",
]


def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "").lower())


def company_key(value: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:-]", "", norm(value))


def domain_key(value: str) -> str:
    host = urlparse(value if "://" in (value or "") else "https://" + (value or "")).hostname or ""
    return re.sub(r"^www\.", "", host.lower())


def phone_key(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def get_values_retry(ws, attempts: int = 5):
    for attempt in range(attempts):
        try:
            return ws.get_all_values()
        except Exception as exc:
            if attempt + 1 == attempts or "429" not in str(exc):
                raise
            time.sleep(8 * (attempt + 1))


parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
parser.add_argument("--csv", default=str(CSV_PATH))
parser.add_argument("--count", type=int, default=50)
args = parser.parse_args()

candidate_path = Path(args.csv).resolve()
candidates = list(csv.DictReader(candidate_path.open(encoding="utf-8-sig", newline="")))
if len(candidates) != args.count:
    raise SystemExit(f"candidate_count_mismatch={len(candidates)}")

# 001の採用条件を、シートへ書き込む直前にも機械的に強制する。
# とくにcontact_url欠落は005で送信不能になるため、1件でもあれば全件停止する。
required_fields = ("company_name", "url", "contact_url", "区分", "検出ワード")
missing_required = [
    {
        "candidate_row": index,
        "company_name": row.get("company_name", ""),
        "missing": [field for field in required_fields if not (row.get(field) or "").strip()],
    }
    for index, row in enumerate(candidates, start=2)
]
missing_required = [item for item in missing_required if item["missing"]]
if missing_required:
    print(json.dumps({"missing_required": missing_required}, ensure_ascii=False))
    raise SystemExit(f"required_field_check_failed={len(missing_required)}")

client = sheets_io.get_client()
book = client.open_by_url(SHEET)
worksheets = book.worksheets()
live_names: set[str] = set()
live_domains: set[str] = set()
live_phones: set[str] = set()
tab_counts: dict[str, int] = {}
target_values = None

for ws in worksheets:
    values = get_values_retry(ws)
    tab_counts[ws.title] = max(0, len(values) - 1)
    if ws.title == TARGET:
        target_values = values
    for row in values[1:]:
        if row and row[0].strip():
            live_names.add(company_key(row[0]))
        if len(row) > 1 and row[1].strip():
            live_domains.add(domain_key(row[1]))
        if len(row) > 3 and phone_key(row[3]):
            live_phones.add(phone_key(row[3]))

if target_values is None:
    raise SystemExit("target_worksheet_not_found")
if target_values[0][:16] != HEADERS:
    raise SystemExit("target_header_mismatch=" + json.dumps(target_values[0][:16], ensure_ascii=False))

conflicts = []
for row in candidates:
    reasons = []
    if company_key(row["company_name"]) in live_names:
        reasons.append("company_name")
    if domain_key(row["url"]) in live_domains:
        reasons.append("domain")
    if phone_key(row["phone"]) and phone_key(row["phone"]) in live_phones:
        reasons.append("phone")
    if reasons:
        conflicts.append({"company_name": row["company_name"], "reasons": reasons})

preview = {
    "mode": "write" if args.write else "preview",
    "candidate_count": len(candidates),
    "live_tab_count": len(worksheets),
    "target_rows_before": len(target_values) - 1,
    "live_conflicts": conflicts,
    "tab_counts": tab_counts,
}
print(json.dumps(preview, ensure_ascii=False))
if conflicts:
    raise SystemExit(f"live_conflicts={len(conflicts)}")
if not args.write:
    raise SystemExit(0)

target = book.worksheet(TARGET)
start_row = len(target_values) + 1
payload = [[row.get(h, "") if h else row.get("", "") for h in HEADERS] for row in candidates]
end_row = start_row + len(payload) - 1
target.update(values=payload, range_name=f"A{start_row}:P{end_row}", value_input_option="RAW")
readback = target.get(f"A{start_row}:P{end_row}")

verified = 0
errors = []
for offset, (expected, actual) in enumerate(zip(payload, readback)):
    padded = actual + [""] * (16 - len(actual))
    if padded[:16] == expected:
        verified += 1
    else:
        errors.append({"row": start_row + offset, "company_name": expected[0]})

result = {
    "written": len(payload),
    "start_row": start_row,
    "end_row": end_row,
    "readback_rows": len(readback),
    "verified_exact": verified,
    "verification_errors": errors,
    "target_rows_after": len(target_values) - 1 + len(payload),
}
print(json.dumps(result, ensure_ascii=False))
if len(readback) != len(payload) or verified != len(payload):
    raise SystemExit("readback_verification_failed")
