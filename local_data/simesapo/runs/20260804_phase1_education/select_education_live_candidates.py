from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent
SOURCE = HERE / "education_with_contacts.csv"
SEED = HERE / "education_candidate_seed.csv"
AUDIT = HERE / "education_preappend_audit.csv"
FINAL = HERE / "education_final_verified_50.csv"
MASTER = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\custmize\enterprise_filter")
SKILL = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
HEADERS = ["company_name", "url", "address", "phone", "maps_url", "contact_url", "message", "sent_at", "status", "error_reason", "screenshot_path", "provider_used", "提案区分", "H1", "区分", "検出ワード"]

def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "").lower())

def company_key(value: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:：-]", "", norm(value))

def domain_key(value: str) -> str:
    parsed = urlparse(value if "://" in (value or "") else "https://" + (value or ""))
    return re.sub(r"^www\.", "", (parsed.hostname or "").lower()).rstrip(".")

def phone_key(value: str) -> str:
    return re.sub(r"\D", "", value or "")

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

manual_contacts = {
    domain_key(row.get("url", "")): (row.get("contact_url") or "").strip()
    for row in read_csv(SEED)
    if (row.get("contact_url") or "").strip()
}
source_rows = read_csv(SOURCE)
for row in source_rows:
    if not (row.get("contact_url") or "").strip():
        row["contact_url"] = manual_contacts.get(domain_key(row.get("url", "")), "")
candidates = [row for row in source_rows if (row.get("contact_url") or "").strip()]
confirmed = read_csv(MASTER / "confirmed_enterprise_exclusions.csv")
allow = read_csv(MASTER / "enterprise_false_positive_allowlist.csv")
jpx = read_csv(MASTER / "jpx_listed_companies_20260630.csv")
groups = read_csv(MASTER / "major_group_rules.csv")

confirmed_domains = {domain_key(row.get("official_domain", "")) for row in confirmed if row.get("official_domain")}
confirmed_pairs = {(company_key(row.get("company_name", "")), domain_key(row.get("official_domain", ""))) for row in confirmed if row.get("company_name") and row.get("official_domain")}
allow_pairs = {
    (
        company_key(row.get("company_name", "")),
        domain_key(row.get("candidate_domain", "") or row.get("official_domain", "") or row.get("url", "")),
    )
    for row in allow
    if row.get("company_name") and (row.get("candidate_domain") or row.get("official_domain") or row.get("url"))
}
jpx_names = {company_key(row.get("company_name", "")) for row in jpx if row.get("company_name")}
group_terms = [norm(row.get("match_value", "")) for row in groups if row.get("match_type") == "company_contains" and row.get("match_value")]

book = sheets_io.get_client().open_by_url(SHEET)
live_names: set[str] = set()
live_domains: set[str] = set()
live_phones: set[str] = set()
tab_counts: dict[str, int] = {}
for ws in book.worksheets():
    values = ws.get_all_values()
    tab_counts[ws.title] = max(0, len(values) - 1)
    for row in values[1:]:
        if row and row[0].strip():
            live_names.add(company_key(row[0]))
        if len(row) > 1 and row[1].strip():
            live_domains.add(domain_key(row[1]))
        if len(row) > 3 and phone_key(row[3]):
            live_phones.add(phone_key(row[3]))

audit: list[dict] = []
accepted: list[dict] = []
local_exclude_companies = {company_key("株式会社サインウェーブ"), company_key("株式会社文理")}
for row in candidates:
    ck = company_key(row.get("company_name", ""))
    dk = domain_key(row.get("url", ""))
    pk = phone_key(row.get("phone", ""))
    pair = (ck, dk)
    decision = "accept"
    reason = "no_live_or_master_match"
    if ck in local_exclude_companies:
        decision, reason = "exclude", "contact_not_sendable_or_major_group"
    elif ck in live_names or dk in live_domains or (pk and pk in live_phones):
        decision, reason = "exclude", "existing_sheet_match"
    elif pair in allow_pairs:
        decision, reason = "accept", "enterprise_false_positive_allowlist"
    elif dk in confirmed_domains or pair in confirmed_pairs:
        decision, reason = "exclude", "confirmed_enterprise"
    elif ck in jpx_names:
        decision, reason = "review", "jpx_name_requires_official_domain_check"
    elif any(term and term in norm(row.get("company_name", "")) for term in group_terms):
        decision, reason = "review", "major_group_keyword_requires_official_check"
    audit.append({"company_name": row.get("company_name", ""), "url": row.get("url", ""), "contact_url": row.get("contact_url", ""), "decision": decision, "reason": reason})
    if decision == "accept":
        accepted.append(row)

with AUDIT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "contact_url", "decision", "reason"])
    writer.writeheader(); writer.writerows(audit)

if len(accepted) >= 50:
    with FINAL.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS, extrasaction="ignore")
        writer.writeheader(); writer.writerows(accepted[:50])

counts = {key: sum(row["decision"] == key for row in audit) for key in ("accept", "exclude", "review")}
print(json.dumps({"input_with_contact": len(candidates), **counts, "reconciled": sum(counts.values()), "final_written": min(50, len(accepted)), "tab_counts": tab_counts}, ensure_ascii=False))
if len(candidates) != sum(counts.values()):
    raise SystemExit("reconciliation_failed")
if len(accepted) < 50:
    raise SystemExit(f"accepted_shortfall={50-len(accepted)}")



