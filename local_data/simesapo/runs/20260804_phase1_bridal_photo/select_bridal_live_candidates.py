from __future__ import annotations

import argparse, csv, json, re, sys, unicodedata
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent
parser = argparse.ArgumentParser()
parser.add_argument("--seed", default=str(HERE / "bridal_candidate_seed.csv"))
parser.add_argument("--audit", default=str(HERE / "bridal_preappend_audit.csv"))
parser.add_argument("--final", default=str(HERE / "bridal_final_verified_50.csv"))
args = parser.parse_args()
SEED, AUDIT, FINAL = Path(args.seed), Path(args.audit), Path(args.final)
MASTER = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\custmize\enterprise_filter")
SKILL = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
HEADERS = ["company_name", "url", "address", "phone", "maps_url", "contact_url", "message", "sent_at", "status", "error_reason", "screenshot_path", "provider_used", "提案区分", "H1", "区分", "検出ワード"]

def norm(v): return re.sub(r"\s+", "", unicodedata.normalize("NFKC", v or "").lower())
def company_key(v): return re.sub(r"株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:：-]", "", norm(v))
def domain_key(v):
    p = urlparse(v if "://" in (v or "") else "https://" + (v or "")); return re.sub(r"^www\.", "", (p.hostname or "").lower()).rstrip(".")
def phone_key(v): return re.sub(r"\D", "", v or "")
def read(path):
    with path.open(encoding="utf-8-sig", newline="") as h: return list(csv.DictReader(h))

candidates = read(SEED)
confirmed, allow, jpx, groups = [read(MASTER / name) for name in ("confirmed_enterprise_exclusions.csv", "enterprise_false_positive_allowlist.csv", "jpx_listed_companies_20260630.csv", "major_group_rules.csv")]
confirmed_domains = {domain_key(r.get("official_domain", "")) for r in confirmed if r.get("official_domain")}
confirmed_pairs = {(company_key(r.get("company_name", "")), domain_key(r.get("official_domain", ""))) for r in confirmed if r.get("company_name") and r.get("official_domain")}
allow_pairs = {(company_key(r.get("company_name", "")), domain_key(r.get("candidate_domain", "") or r.get("official_domain", "") or r.get("url", ""))) for r in allow if r.get("company_name") and (r.get("candidate_domain") or r.get("official_domain") or r.get("url"))}
jpx_names = {company_key(r.get("company_name", "")) for r in jpx if r.get("company_name")}
group_terms = [norm(r.get("match_value", "")) for r in groups if r.get("match_type") == "company_contains" and r.get("match_value")]

book = sheets_io.get_client().open_by_url(SHEET)
live_names, live_domains, live_phones = set(), set(), set()
tab_counts = {}
for ws in book.worksheets():
    values = ws.get_all_values(); tab_counts[ws.title] = max(0, len(values)-1)
    for row in values[1:]:
        if row and row[0].strip(): live_names.add(company_key(row[0]))
        if len(row)>1 and row[1].strip(): live_domains.add(domain_key(row[1]))
        if len(row)>3 and phone_key(row[3]): live_phones.add(phone_key(row[3]))

audit, accepted = [], []
seen_names, seen_domains = set(), set()
for row in candidates:
    ck, dk, pk = company_key(row.get("company_name", "")), domain_key(row.get("url", "")), phone_key(row.get("phone", ""))
    pair = (ck, dk); decision, reason = "accept", "no_live_or_master_match"
    if not ck or not dk or not row.get("contact_url", "").strip(): decision, reason = "exclude", "required_field_blank"
    elif ck in seen_names or dk in seen_domains: decision, reason = "exclude", "candidate_duplicate"
    elif ck in live_names or dk in live_domains or (pk and pk in live_phones): decision, reason = "exclude", "existing_sheet_match"
    elif pair in allow_pairs: decision, reason = "accept", "enterprise_false_positive_allowlist"
    elif dk in confirmed_domains or pair in confirmed_pairs: decision, reason = "exclude", "confirmed_enterprise"
    elif ck in jpx_names: decision, reason = "review", "jpx_name_requires_official_domain_check"
    elif any(term and term in norm(row.get("company_name", "")) for term in group_terms): decision, reason = "review", "major_group_keyword_requires_official_check"
    audit.append({"company_name": row.get("company_name", ""), "url": row.get("url", ""), "contact_url": row.get("contact_url", ""), "decision": decision, "reason": reason})
    if decision == "accept":
        seen_names.add(ck); seen_domains.add(dk)
        accepted.append({
            "company_name": row["company_name"], "url": row["url"], "address": "", "phone": "", "maps_url": "", "contact_url": row["contact_url"],
            "message": "", "sent_at": "", "status": "", "error_reason": "", "screenshot_path": "", "provider_used": "",
            "提案区分": "", "H1": "", "区分": row["区分"], "検出ワード": row["検出ワード"]
        })

with AUDIT.open("w", encoding="utf-8-sig", newline="") as h:
    w=csv.DictWriter(h, fieldnames=["company_name","url","contact_url","decision","reason"]); w.writeheader(); w.writerows(audit)
if len(accepted)>=50:
    with FINAL.open("w", encoding="utf-8-sig", newline="") as h:
        w=csv.DictWriter(h, fieldnames=HEADERS); w.writeheader(); w.writerows(accepted[:50])
counts={k:sum(r["decision"]==k for r in audit) for k in ("accept","exclude","review")}
print(json.dumps({"input":len(candidates),**counts,"reconciled":sum(counts.values()),"final_written":min(50,len(accepted)),"tab_counts":tab_counts},ensure_ascii=False))
if len(candidates)!=sum(counts.values()): raise SystemExit("reconciliation_failed")
if len(accepted)<50: raise SystemExit(f"accepted_shortfall={50-len(accepted)}")
