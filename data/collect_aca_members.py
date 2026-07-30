import csv
import html
import json
import re
import urllib.parse

import requests


SOURCE_URL = "https://www.aca-j.or.jp/meibo/"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_aca_official_members_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}

INCLUDE = (
    "マーケティング",
    "Web",
    "WEB",
    "ウェブ",
    "インターネット広告",
    "デジタル広告",
    "広告運用",
    "SNS",
    "プロモーション",
    "PR",
)
EXCLUDE_ONLY = (
    "印刷",
    "看板",
    "映像制作",
    "システム開発",
    "出版",
    "媒体",
)


def strip_tags(value):
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def normalized_domain(url):
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().removeprefix("www.")


def normalized_name(value):
    value = re.sub(r"[\s\u3000・.\-]", "", value or "")
    return value.replace("株式会社", "").replace("有限会社", "").lower()


def cell(block, heading):
    match = re.search(
        rf"<th>\s*{heading}\s*</th>\s*<td[^>]*>(.*?)</td>",
        block,
        flags=re.S | re.I,
    )
    return strip_tags(match.group(1)) if match else ""


def main():
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    page = response.text

    with open(EXISTING_PATH, encoding="utf-8") as handle:
        existing = json.load(handle)
    existing_domains = {normalized_domain(row.get("url", "")) for row in existing if row.get("url")}
    existing_names = {normalized_name(row.get("company_name", "")) for row in existing}

    rows = []
    blocks = re.findall(
        r'<div class="b-box[^"]*"[^>]*>(.*?)</div>\s*(?=<div class="b-box|</div>)',
        page,
        flags=re.S | re.I,
    )
    for block in blocks:
        name_match = re.search(r"<h3[^>]*>(.*?)</h3>", block, flags=re.S | re.I)
        if not name_match:
            continue
        company_name = strip_tags(name_match.group(1))
        address = cell(block, "所在地")
        phone = cell(block, "TEL")
        url = cell(block, "URL")
        business = cell(block, "事業内容")
        categories = " ".join(
            strip_tags(value)
            for value in re.findall(r'<li[^>]*>(.*?)</li>', block, flags=re.S | re.I)
        )
        evidence = f"{business} {categories}"
        if not any(keyword in evidence for keyword in INCLUDE):
            continue
        if all(keyword in evidence for keyword in EXCLUDE_ONLY):
            continue
        if not company_name or not url or not address:
            continue
        if normalized_domain(url) in existing_domains or normalized_name(company_name) in existing_names:
            continue
        try:
            site = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if site.status_code >= 400:
                continue
        except Exception:
            continue
        rows.append(
            {
                "company_name": company_name,
                "url": url,
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
    print(f"blocks={len(blocks)} candidates={len(rows)} -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
