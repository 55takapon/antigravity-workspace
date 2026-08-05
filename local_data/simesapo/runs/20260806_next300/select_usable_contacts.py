from __future__ import annotations

import argparse
import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
CONTACT_RE = re.compile(r"お問い合わせ|お問合せ|問い合わせ|ご相談|contact|inquiry|メールフォーム|送信", re.I)

parser = argparse.ArgumentParser()
parser.add_argument("--seed", required=True)
parser.add_argument("--audit", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--count", type=int, default=50)
args = parser.parse_args()

with Path(args.seed).open(encoding="utf-8-sig", newline="") as handle:
    seed = list(csv.DictReader(handle))
with Path(args.audit).open(encoding="utf-8-sig", newline="") as handle:
    accepted = {(row["company_name"], row["url"], row["contact_url"]) for row in csv.DictReader(handle) if row["decision"] == "accept"}
source = [
    row for row in seed
    if (row["company_name"], row["url"], row["contact_url"]) in accepted
    and not re.search(r"(?:^|\s)(?:本社|支社|支店|営業所|事業所|センター)$", row["company_name"])
]

def check(row):
    try:
        response = requests.get(row["contact_url"], headers=HEADERS, timeout=25, allow_redirects=True)
        response.raise_for_status()
        if "html" not in response.headers.get("content-type", "").lower():
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        text = " ".join(soup.get_text(" ", strip=True).split())
        forms = soup.find_all("form")
        has_fields = any(form.find(["input", "textarea", "select"]) for form in forms)
        has_mail = bool(soup.select_one('a[href^="mailto:"]'))
        embeds = " ".join(
            [tag.get("src", "") for tag in soup.find_all(["iframe", "script"]) if tag.get("src")]
        )
        has_embedded_form = bool(re.search(r"google\.com/forms|contact-form|ninja-forms|pardot|/l/\d+|form\.movabletype|hubspot", embeds, re.I))
        route_signal = CONTACT_RE.search(response.url + " " + text[:3000])
        if has_fields or has_embedded_form or (has_mail and route_signal):
            return row
    except requests.RequestException:
        return None
    return None

usable = []
with ThreadPoolExecutor(max_workers=18) as pool:
    futures = {pool.submit(check, row): index for index, row in enumerate(source)}
    found = []
    for future in as_completed(futures):
        row = future.result()
        if row:
            found.append((futures[future], row))
usable = [row for _, row in sorted(found)][:args.count]
with Path(args.output).open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(seed[0]))
    writer.writeheader()
    writer.writerows(usable)
print({"accepted_input": len(source), "usable_contacts": len(found), "final_written": len(usable), "output": args.output})
if len(usable) != args.count:
    raise SystemExit(2)
