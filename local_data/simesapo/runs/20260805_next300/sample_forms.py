from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

POSITIONS = [1, 11, 21, 31, 41]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
BAN_RE = re.compile(r"営業目的|売り込み|セールス|勧誘|営業メール|営業のご連絡|営業に関する|営業活動", re.I)
REJECT_RE = re.compile(r"お断り|固くお断り|ご遠慮|送信しない|受け付けておりません|返信いたしかね", re.I)
PHONE_RE = re.compile(r"電話営業|営業電話|電話での営業", re.I)

parser = argparse.ArgumentParser()
parser.add_argument("--csv", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

with Path(args.csv).open(encoding="utf-8-sig", newline="") as handle:
    source = list(csv.DictReader(handle))

results = []
for position in POSITIONS:
    row = source[position - 1]
    result = {"position": position, "company_name": row["company_name"], "contact_url": row["contact_url"], "status": "fetch_failed", "http_status": "", "form_count": 0, "matched_text": ""}
    try:
        response = requests.get(row["contact_url"], headers=HEADERS, timeout=25, allow_redirects=True)
        result["http_status"] = response.status_code
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        result["form_count"] = len(soup.find_all("form"))
        snippets = []
        for match in BAN_RE.finditer(text):
            snippets.append(text[max(0, match.start() - 35): min(len(text), match.end() + 65)])
        joined = " | ".join(snippets)[:500]
        result["matched_text"] = joined
        if PHONE_RE.search(text) and REJECT_RE.search(joined):
            result["status"] = "phone_sales_only_ban"
        elif BAN_RE.search(text) and REJECT_RE.search(joined):
            result["status"] = "explicit_sales_ban"
        elif result["form_count"] or re.search(r"入力|必須|送信|確認画面|お名前|メールアドレス", text):
            result["status"] = "no_ban_text_form_present"
        else:
            result["status"] = "unclear_no_form_detected"
    except Exception as exc:
        result["matched_text"] = type(exc).__name__
    results.append(result)

output = Path(args.output)
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print({"sampled": len(results), "counts": {status: sum(r["status"] == status for r in results) for status in sorted({r["status"] for r in results})}, "output": str(output)})
