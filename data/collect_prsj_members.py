import csv
import html
import json
import re

import requests

from collect_jaaa_candidates import (
    candidate_pages,
    fetch,
    find_address,
    find_phone,
    normalized_domain,
    normalized_name,
)


SOURCE_URL = "https://area18.smp.ne.jp/area/table/45023/eg5o7c/M?S=reqaq2mbldof"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_prsj_official_members_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}


def canonical_name(value):
    value = html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
    value = value.replace("(株)", "株式会社").replace("(有)", "有限会社").replace("(同)", "合同会社")
    return value


def main():
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    matches = re.findall(
        r'<h2 class="company-name"><a[^>]*href="([^"]*)">(.*?)</a></h2>\s*'
        r'<p[^>]*><a[^>]*href="([^"]*)">',
        response.text,
        flags=re.S | re.I,
    )
    members = []
    for first_url, raw_name, second_url in matches:
        url = first_url or second_url
        if url:
            members.append((canonical_name(raw_name), url))

    with open(EXISTING_PATH, encoding="utf-8") as handle:
        existing = json.load(handle)
    existing_domains = {normalized_domain(row.get("url", "")) for row in existing if row.get("url")}
    existing_names = {normalized_name(row.get("company_name", "")) for row in existing}

    rows = []
    seen_domains = set()
    for company_name, home_url in members:
        domain = normalized_domain(home_url)
        if domain in seen_domains or domain in existing_domains or normalized_name(company_name) in existing_names:
            continue
        seen_domains.add(domain)
        try:
            home_text, links = fetch(home_url)
        except Exception:
            continue
        combined_text = home_text
        for page_url in candidate_pages(home_url, links)[1:]:
            try:
                page_text, _ = fetch(page_url)
                combined_text += "\n" + page_text
            except Exception:
                continue
        address = find_address(combined_text)
        phone = find_phone(combined_text)
        if address and (phone or "問い合わせ" in combined_text or "Contact" in combined_text):
            rows.append(
                {
                    "company_name": company_name,
                    "url": home_url,
                    "address": address,
                    "phone": phone,
                    "maps_url": "",
                    "status": "",
                }
            )
    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["company_name", "url", "address", "phone", "maps_url", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"members={len(members)} candidates={len(rows)} -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
