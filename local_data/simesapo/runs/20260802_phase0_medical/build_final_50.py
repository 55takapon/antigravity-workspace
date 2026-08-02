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
unique = [r for r in unique if r not in conflicts]

# 書き込み直前の全タブ再照合で新たに既存化していた候補。
live_conflict_names = {cname("日本ビスカ株式会社"), cname("株式会社デントランス")}
unique = [r for r in unique if cname(r["company_name"]) not in live_conflict_names]

# 正式社名への補正後に判明した既存重複を除き、追加監査を通過した純増候補で補充する。
for name in [
    "sixth_quality_results.csv",
    "seventh_quality_results.csv",
    "eighth_quality_results.csv",
    "tenth_quality_results.csv",
    "eleventh_quality_results.csv",
    "twelfth_quality_results.csv",
]:
    for row in csv.DictReader((HERE / name).open(encoding="utf-8-sig", newline="")):
        if row["decision"] != "accept":
            continue
        if cname(row["company_name"]) in live_conflict_names:
            continue
        if cname(row["company_name"]) in existing_names or domain(row["url"]) in existing_domains:
            continue
        if cname(row["company_name"]) in {cname(r["company_name"]) for r in unique}:
            continue
        if domain(row["url"]) in {domain(r["url"]) for r in unique}:
            continue
        unique.append(row)

# 初回探索で問い合わせ先未検出だったが、公式相談フォームを後から確認できた候補。
so_medical = {
    "company_name": "SO MEDICAL DESIGN合同会社",
    "url": "https://somedical.co.jp/",
    "address": "",
    "phone": "",
    "maps_url": "",
    "contact_url": "https://somedical.co.jp/consultation/",
}
if (
    cname(so_medical["company_name"]) not in existing_names
    and domain(so_medical["url"]) not in existing_domains
    and cname(so_medical["company_name"]) not in {cname(r["company_name"]) for r in unique}
    and domain(so_medical["url"]) not in {domain(r["url"]) for r in unique}
):
    unique.append(so_medical)

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
print({
    "final": len(out),
    "removed_existing_conflicts": len(conflicts),
    "unique_company": len({cname(r["company_name"]) for r in unique}),
    "unique_domain": len({domain(r["url"]) for r in unique}),
    "contact": sum(bool(r["contact_url"]) for r in out),
})
