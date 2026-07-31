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


SOURCE_URL = "https://jeva.or.jp/katsudo/member.html"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_jeva_official_promotion_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}
TARGET_DESC_RE = re.compile(
    r"イベント.*(?:企画|制作|運営|プロデュース)|プロモーション|"
    r"マーケティング|販売促進|キャンペーン|PR施策|"
    r"プランニング.*プロデュース|総合コンサルティング"
)
SERVICE_RE = re.compile(
    r"イベント|プロモーション|マーケティング|広告|集客|"
    r"販促|販売促進|キャンペーン|PR|ブランディング"
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
    start_match = re.search(r"法人会員", page)
    end_match = re.search(r"団体会員", page)
    if not start_match or not end_match:
        raise RuntimeError("法人会員セクションを特定できません")
    section = page[start_match.end():end_match.start()]
    members = []
    for row_html in re.findall(r"<tr\b[^>]*>(.*?)</tr>", section, flags=re.I | re.S):
        anchor = re.search(
            r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            row_html,
            flags=re.I | re.S,
        )
        cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row_html, flags=re.I | re.S)
        if not anchor or len(cells) < 2:
            continue
        href_raw, label_raw = anchor.group(1), anchor.group(2)
        description = cells[1]
        name = clean_text(label_raw)
        desc = clean_text(description)
        if not re.search(r"株式会社|有限会社|合同会社|㈱", name):
            continue
        if not TARGET_DESC_RE.search(desc):
            continue
        name = name.replace("㈱", "株式会社").replace("･", "・")
        url = urljoin(SOURCE_URL, html.unescape(href_raw).strip())
        host = urlparse(url).netloc.lower()
        if host and "facebook.com" not in host and not host.endswith("jeva.or.jp"):
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
    print(
        f"targeted={len(members)} new_domains={len(unique)} "
        f"verified={len(rows)} -> {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
