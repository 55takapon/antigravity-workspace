from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent

def norm(v): return re.sub(r"\s+", "", unicodedata.normalize("NFKC", v or "").lower())
def cname(v): return re.sub(r"株式会社|有限会社|合同会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:-]", "", norm(v))
def domain(v): return re.sub(r"^www\.", "", (urlparse(v).hostname or "").lower())

sources = [
    "quality_gate_full_results.csv",
    "additional_quality_results.csv",
    "supplement_quality_results.csv",
    "third_quality_results.csv",
    "fourth_quality_results.csv",
    "fifth_quality_results.csv",
]
rows = []
for name in sources:
    rows.extend(r for r in csv.DictReader((HERE / name).open(encoding="utf-8-sig", newline="")) if r["decision"] == "accept")

# 公式会社概要で確認した運営会社名へ補正する。
name_overrides = {
    "株式会社BAU": "株式会社MATSURI",
    "株式会社ほねぺじ": "株式会社HSK",
}
for row in rows:
    row["company_name"] = name_overrides.get(row["company_name"], row["company_name"])

first = {r["company_name"]: r for r in csv.DictReader((HERE / "quality_gate_full_results.csv").open(encoding="utf-8-sig", newline=""))}
fourth = {r["company_name"]: r for r in csv.DictReader((HERE / "fourth_quality_results.csv").open(encoding="utf-8-sig", newline=""))}
manual = []
for old_name, new_name in [
    ("有限会社アップルハウス", "フルリール株式会社"),
    ("株式会社システムズナカシマ", "ユニバーサル・インタラクティブ株式会社"),
    ("株式会社REACT", "株式会社ハンズ"),
]:
    row = dict(first[old_name]); row["company_name"] = new_name; row["decision"] = "accept_manual_official_profile"; manual.append(row)
row = dict(fourth["株式会社AllSO"]); row["decision"] = "accept_manual_official_service"; row["service_evidence_ok"] = "true"; manual.append(row)
rows.extend(manual)

# バッチ内の会社名・ドメイン重複を禁止。
seen_names, seen_domains, unique = set(), set(), []
for row in rows:
    nk, dk = cname(row["company_name"]), domain(row["url"])
    if nk in seen_names or dk in seen_domains: continue
    seen_names.add(nk); seen_domains.add(dk); unique.append(row)

existing = json.loads((HERE / "existing_master.json").read_text(encoding="utf-8"))
existing_names = {cname(r.get("company_name", "")) for r in existing if r.get("company_name")}
existing_domains = {domain(r.get("url", "")) for r in existing if r.get("url")}
conflicts = [r for r in unique if cname(r["company_name"]) in existing_names or domain(r["url"]) in existing_domains]
if conflicts:
    raise SystemExit("final conflicts: " + ", ".join(r["company_name"] for r in conflicts))
assert len(unique) == 50, len(unique)

out = []
for r in unique:
    out.append({
        "company_name": r["company_name"], "url": r["url"], "address": r.get("address", ""),
        "phone": r.get("phone", ""), "maps_url": r.get("maps_url", ""), "contact_url": r["contact_url"],
        "message": "", "sent_at": "", "status": "", "error_reason": "", "screenshot_path": "",
        "provider_used": "", "提案区分": "", "": "", "区分": "S｜業界特化Web制作",
        "検出ワード": "医療・歯科・介護等の業界特化Web制作・運用",
    })
with (HERE / "final_verified_50.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print({"final": len(out), "unique_company": len(seen_names), "unique_domain": len(seen_domains), "contact": sum(bool(r["contact_url"]) for r in out)})
