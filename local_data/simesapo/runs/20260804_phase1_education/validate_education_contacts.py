from __future__ import annotations

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

HERE = Path(__file__).parent
SOURCE = HERE / "education_final_verified_50.csv"
OUT = HERE / "education_contact_validation.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}

with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))

def check(idx_row: tuple[int, dict]) -> dict:
    idx, row = idx_row
    url = row["contact_url"]
    if "docs.google.com/forms" in url or "forms.office.com" in url or "form.run" in url:
        return {"idx": idx, "company_name": row["company_name"], "contact_url": url, "status": 200, "form_like": "yes", "reason": "hosted_form"}
    try:
        response = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        body = response.text
        forms = len(re.findall(r"<form\b", body, re.I))
        inputs = len(re.findall(r"<(input|textarea|select)\b", body, re.I))
        embeds = bool(re.search(r"hubspot|formrun|formzu|form-mailer|mw_wp_form|contact-form-7|forminator|wpforms|gravityforms|ninja-forms", body, re.I))
        valid = response.status_code < 400 and (forms > 0 or inputs >= 3 or embeds)
        return {"idx": idx, "company_name": row["company_name"], "contact_url": url, "status": response.status_code, "form_like": "yes" if valid else "no", "reason": f"forms={forms};inputs={inputs};embeds={int(embeds)};final={response.url}"}
    except Exception as exc:
        return {"idx": idx, "company_name": row["company_name"], "contact_url": url, "status": 0, "form_like": "no", "reason": type(exc).__name__}

results = []
with ThreadPoolExecutor(max_workers=10) as pool:
    futures = [pool.submit(check, item) for item in enumerate(rows)]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: row["idx"])
with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["idx", "company_name", "contact_url", "status", "form_like", "reason"])
    writer.writeheader(); writer.writerows(results)
print(json.dumps({"rows": len(results), "form_like": sum(row["form_like"] == "yes" for row in results), "review": sum(row["form_like"] == "no" for row in results)}, ensure_ascii=False))
