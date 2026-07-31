import csv
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

import requests

from collect_jaaa_candidates import (
    candidate_pages,
    fetch,
    find_address,
    find_phone,
    normalized_domain,
    normalized_name,
)


SOURCE_URL = "https://hepc.or.jp/member.html"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_hepc_official_members_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}
SERVICE_RE = re.compile(
    r"イベント.*(?:企画|制作|運営|プロデュース)|プロモーション|"
    r"マーケティング|広告|販促|販売促進|展示会"
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
    for page_url in candidate_pages(home_url, links)[1:9]:
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
    anchors = list(
        re.finditer(
            r'<a\b[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>',
            page,
            flags=re.I | re.S,
        )
    )
    members = []
    for match in anchors:
        url = html.unescape(match.group(1)).strip()
        host = urlparse(url).netloc.lower()
        if not host or host.endswith("hepc.or.jp") or "facebook.com" in host:
            continue
        prefix = clean_text(page[max(0, match.start() - 900):match.start()])
        found = re.findall(
            r"(?:株式会社|有限会社|合同会社|I・C・C インターナショナル株式会社)"
            r"[A-Za-zＡ-Ｚａ-ｚ0-9０-９・＆&\s\u3000\u3040-\u30ff\u3400-\u9fff]+",
            prefix,
        )
        if not found:
            continue
        name = re.split(r"〒|代表取締役|取締役|TEL", found[-1])[0].strip()
        name = re.sub(r"^(?:理\s*事|監\s*事)\s*", "", name)
        members.append((name, url))

    with open(EXISTING_PATH, encoding="utf-8") as handle:
        existing = json.load(handle)
    existing_domains = {normalized_domain(row.get("url", "")) for row in existing if row.get("url")}
    existing_names = {normalized_name(row.get("company_name", "")) for row in existing}
    unique = []
    seen_domains = set()
    for name, url in members:
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
    print(f"linked={len(members)} new={len(unique)} verified={len(rows)} -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
