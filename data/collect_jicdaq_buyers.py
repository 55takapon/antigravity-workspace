import csv
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor

import requests

from collect_jaaa_candidates import (
    candidate_pages,
    fetch,
    find_address,
    find_phone,
    normalized_domain,
    normalized_name,
)


SOURCE_URL = "https://www.jicdaq.or.jp/list/"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_jicdaq_official_buyers_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}
LEGAL_RE = re.compile(r"株式会社|有限会社|合同会社|Inc\.|Japan")
TARGET_AREA_RE = re.compile(r"広告購入者|広告取引・仲介事業者")
SERVICE_RE = re.compile(
    r"広告|マーケティング|プロモーション|集客|販促|販売促進|"
    r"SNS|ソーシャルメディア|ブランディング"
)


def clean_text(value):
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", value).strip()


def inspect_member(item):
    company_name, home_url = item
    try:
        home_text, links = fetch(home_url)
    except Exception:
        return None
    combined_text = home_text
    for page_url in candidate_pages(home_url, links)[1:11]:
        try:
            page_text, _ = fetch(page_url)
            combined_text += "\n" + page_text
        except Exception:
            continue
    address = find_address(combined_text)
    phone = find_phone(combined_text)
    has_contact = phone or "問い合わせ" in combined_text or "Contact" in combined_text
    if not (address and has_contact and SERVICE_RE.search(combined_text)):
        return None
    return {
        "company_name": company_name,
        "url": home_url,
        "address": address,
        "phone": phone,
        "maps_url": "",
        "status": "",
    }


def main():
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    page = response.text
    anchor_re = re.compile(
        r'<a\b[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>',
        flags=re.I | re.S,
    )
    matches = list(anchor_re.finditer(page))
    candidates = []
    for index, match in enumerate(matches):
        name = clean_text(match.group(2))
        if not LEGAL_RE.search(name) or len(name) > 90:
            continue
        block_end = matches[index + 1].start() if index + 1 < len(matches) else min(len(page), match.end() + 2500)
        block = clean_text(page[match.end():block_end])
        if not TARGET_AREA_RE.search(block):
            continue
        candidates.append((name, html.unescape(match.group(1))))

    with open(EXISTING_PATH, encoding="utf-8") as handle:
        existing = json.load(handle)
    existing_domains = {normalized_domain(row.get("url", "")) for row in existing if row.get("url")}
    existing_names = {normalized_name(row.get("company_name", "")) for row in existing}
    unique = []
    seen_domains = set()
    for name, url in candidates:
        domain = normalized_domain(url)
        if not domain or domain in seen_domains or domain in existing_domains:
            continue
        if normalized_name(name) in existing_names:
            continue
        seen_domains.add(domain)
        unique.append((name, url))

    with ThreadPoolExecutor(max_workers=2) as executor:
        rows = [row for row in executor.map(inspect_member, unique) if row]
    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["company_name", "url", "address", "phone", "maps_url", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"listed={len(candidates)} new_domains={len(unique)} "
        f"verified={len(rows)} -> {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
