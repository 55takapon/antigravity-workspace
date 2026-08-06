import concurrent.futures
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
SCRIPTS = SKILL / ".claude" / "skills" / "002-contact-extract" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import write_contacts  # noqa: E402

batch_path = Path(sys.argv[1])
result_glob = sys.argv[2]
batch = json.loads(batch_path.read_text(encoding="utf-8"))
by_idx = {int(row["idx"]): row for row in batch}
results = {}
for path in sorted(batch_path.parent.glob(result_glob)):
    results.update(write_contacts.load_results(path))

resolved = {}
probe_jobs = {}
for idx, result in results.items():
    if result.get("method") == "link" and str(result.get("contact_url") or "").startswith(("http://", "https://")):
        resolved[idx] = result["contact_url"]
    elif result.get("method") == "probe":
        probe_jobs[idx] = result.get("probe_candidates", [])
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(write_contacts.probe, candidates): idx for idx, candidates in probe_jobs.items()}
    for future in concurrent.futures.as_completed(futures):
        try:
            resolved[futures[future]] = future.result()
        except Exception:
            resolved[futures[future]] = ""

output = []
for idx in sorted(by_idx):
    row = by_idx[idx]
    hrefs = [str(link.get("href") or "") for link in row.get("links") or []]
    form_url = resolved.get(idx, "")
    has_mail = any(h.lower().startswith("mailto:") for h in hrefs)
    has_tel = any(h.lower().startswith("tel:") for h in hrefs)
    if form_url:
        category = "form"
    elif has_mail:
        category = "email_only_or_form_not_found"
    elif has_tel:
        category = "phone_only_or_form_not_found"
    else:
        category = "no_contact_method_found"
    output.append({"row": row["_row"], "company_name": row.get("company_name", ""), "current_contact_url": row.get("current_contact_url", ""), "verified_form_url": form_url, "has_mail_link": has_mail, "has_tel_link": has_tel, "category": category})
print(json.dumps(output, ensure_ascii=False))
