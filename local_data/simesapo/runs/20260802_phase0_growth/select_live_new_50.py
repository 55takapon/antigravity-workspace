from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "realestate_opener_kept_v4.csv"
OUTPUT = BASE / "realestate_final_verified_50.csv"
SKILL = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
HEADERS = ["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","H1","区分","検出ワード"]

def norm(v): return re.sub(r"\s+","",unicodedata.normalize("NFKC",v or "").lower())
def ck(v): return re.sub(r"株式会社|有限会社|合同会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:-]","",norm(v))
def dk(v):
    h=urlparse(v if "://" in (v or "") else "https://"+(v or "")).hostname or ""
    return re.sub(r"^www\.","",h.lower())
def pk(v): return re.sub(r"\D","",v or "")

with SOURCE.open(encoding="utf-8-sig",newline="") as f: candidates=list(csv.DictReader(f))
book=sheets_io.get_client().open_by_url(SHEET)
names=set();domains=set();phones=set()
for ws in book.worksheets():
    vals=ws.get_all_values()
    for row in vals[1:]:
        if row and row[0].strip(): names.add(ck(row[0]))
        if len(row)>1 and row[1].strip(): domains.add(dk(row[1]))
        if len(row)>3 and pk(row[3]): phones.add(pk(row[3]))

chosen=[]; conflicts=[]
for r in candidates:
    reasons=[]
    if ck(r["company_name"]) in names: reasons.append("company")
    if dk(r["url"]) in domains: reasons.append("domain")
    if pk(r["phone"]) and pk(r["phone"]) in phones: reasons.append("phone")
    if reasons: conflicts.append((r["company_name"],reasons)); continue
    chosen.append(r)
    if len(chosen)==50: break
if len(chosen)!=50: raise SystemExit(f"new_only={len(chosen)} conflicts={conflicts}")
with OUTPUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=HEADERS);w.writeheader();w.writerows(chosen)
print({"input":len(candidates),"live_conflicts":len(conflicts),"selected":len(chosen),"conflicts":conflicts,"output":str(OUTPUT)})
