import csv
import html
import json
import re
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


SOURCE_URL = "https://paa.or.jp/member/"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_paa_official_members_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}
SERVICE_RE = re.compile(
    r"広告|プロモーション|マーケティング|集客|販促|販売促進|"
    r"WEB|Web|ウェブ|SNS|デジタル|ブランディング|企画制作"
)


def clean_name(value):
    value = html.unescape(re.sub(r"<[^>]+>", "", value))
    return re.sub(r"\s+", " ", value).strip()


def main():
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    member_details = []
    for href_raw, label_raw in re.findall(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        response.text,
        flags=re.I | re.S,
    ):
        name = clean_name(label_raw)
        href = urljoin(SOURCE_URL, html.unescape(href_raw).strip())
        host = urlparse(href).netloc.lower()
        if not name or not re.search(r"株式会社|有限会社|合同会社|一般社団法人", name):
            continue
        if not host.endswith("paa.or.jp") or "/member/" not in urlparse(href).path:
            continue
        member_details.append((name, href))

    members = []
    for name, detail_url in member_details:
        try:
            detail = requests.get(detail_url, headers=HEADERS, timeout=30)
            detail.raise_for_status()
        except Exception:
            continue
        external_urls = []
        for href_raw in re.findall(
            r'<a\b[^>]*href=["\']([^"\']+)["\']',
            detail.text,
            flags=re.I,
        ):
            href = urljoin(detail_url, html.unescape(href_raw).strip())
            parsed = urlparse(href)
            host = parsed.netloc.lower()
            if parsed.scheme not in {"http", "https"} or not host:
                continue
            if host.endswith("paa.or.jp") or "googleapis.com" in host or "fontawesome.com" in host:
                continue
            external_urls.append(href)
        if external_urls:
            members.append((name, external_urls[-1]))

    with open(EXISTING_PATH, encoding="utf-8") as handle:
        existing = json.load(handle)
    existing_domains = {normalized_domain(row.get("url", "")) for row in existing if row.get("url")}
    existing_names = {normalized_name(row.get("company_name", "")) for row in existing}

    rows = []
    seen_domains = set()
    for company_name, home_url in members:
        domain = normalized_domain(home_url)
        if not domain or domain in seen_domains or domain in existing_domains:
            continue
        if normalized_name(company_name) in existing_names:
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
        has_contact = phone or "問い合わせ" in combined_text or "Contact" in combined_text
        if address and has_contact:
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
