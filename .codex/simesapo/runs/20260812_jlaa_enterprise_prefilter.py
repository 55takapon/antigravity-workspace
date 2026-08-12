import csv
import json
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_NEXT-B-JLAA-001"
MASTER = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist" / "custmize" / "enterprise_filter"

with (RUN / "jlaa_members_source_diff.csv").open(encoding="utf-8-sig", newline="") as fh:
    rows = list(csv.DictReader(fh))
with (MASTER / "jpx_listed_companies_20260630.csv").open(encoding="utf-8-sig", newline="") as fh:
    jpx = {r["normalized_company_name"] for r in csv.DictReader(fh)}
with (MASTER / "major_group_rules.csv").open(encoding="utf-8-sig", newline="") as fh:
    rules = [r for r in csv.DictReader(fh) if r["match_type"] == "company_contains"]

for r in rows:
    reasons = []
    if r["company_norm"] in jpx:
        reasons.append("JPX会社名完全一致（公式ドメイン確認前）")
    for rule in rules:
        if rule["normalized_value"] and rule["normalized_value"].lower() in r["company_norm"].lower():
            reasons.append("大手グループ管理語=" + rule["match_value"])
    r["enterprise_prefilter"] = "review" if reasons else "pass"
    r["enterprise_reason"] = " / ".join(reasons)

fields = list(rows[0])
with (RUN / "jlaa_members_prefiltered.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
unseen = [r for r in rows if r["existing_match"] == "no"]
report = {
    "official_members": len(rows),
    "existing_matches": sum(r["existing_match"] == "yes" for r in rows),
    "unseen": len(unseen),
    "unseen_enterprise_review": sum(r["enterprise_prefilter"] == "review" for r in unseen),
    "unseen_prefilter_pass": sum(r["enterprise_prefilter"] == "pass" for r in unseen),
    "review_companies": [{"company_name": r["company_name"], "reason": r["enterprise_reason"]} for r in unseen if r["enterprise_prefilter"] == "review"],
}
(RUN / "enterprise_prefilter_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
