import csv
import html
import json
import re
import urllib.parse

import requests


SOURCE_URL = "https://www.jmra-net.or.jp/membership/"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_jmra_official_members_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}


def strip_tags(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def normalized_domain(url):
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().removeprefix("www.")


def normalized_name(value):
    value = (
        (value or "")
        .replace("(株)", "株式会社")
        .replace("㈱", "株式会社")
        .replace("(有)", "有限会社")
        .replace("㈲", "有限会社")
    )
    value = re.sub(r"[\s\u3000・.\-]", "", value)
    return value.replace("株式会社", "").replace("有限会社", "").lower()


def cell(page, heading):
    match = re.search(
        rf"<th[^>]*>\s*{heading}\s*</th>\s*<td[^>]*>(.*?)</td>",
        page,
        flags=re.S | re.I,
    )
    return strip_tags(match.group(1)) if match else ""


def company_name(page):
    title = re.search(r"<title[^>]*>(.*?)</title>", page, flags=re.S | re.I)
    if not title:
        return ""
    value = strip_tags(title.group(1))
    value = re.sub(r"^.*?詳細[｜|]", "", value)
    return value.strip()


def main():
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    detail_urls = list(
        dict.fromkeys(
            urllib.parse.urljoin(SOURCE_URL, href)
            for href in re.findall(
                r'href=["\']([^"\']*sponsorship_detail\.html\?pdid1=\d+)',
                response.text,
                flags=re.I,
            )
        )
    )

    with open(EXISTING_PATH, encoding="utf-8") as handle:
        existing = json.load(handle)
    existing_domains = {normalized_domain(row.get("url", "")) for row in existing if row.get("url")}
    existing_names = {normalized_name(row.get("company_name", "")) for row in existing}

    rows = []
    for detail_url in detail_urls:
        try:
            detail = requests.get(detail_url, headers=HEADERS, timeout=20)
            detail.raise_for_status()
            detail.encoding = detail.apparent_encoding or "utf-8"
        except Exception:
            continue
        page = detail.text
        name = company_name(page)
        address = cell(page, "本社所在地")
        phone = cell(page, "電話番号")
        homepage = cell(page, "ホームページ")
        if not name or not address or not homepage:
            continue
        if normalized_domain(homepage) in existing_domains or normalized_name(name) in existing_names:
            continue
        try:
            site = requests.get(homepage, headers=HEADERS, timeout=15, allow_redirects=True)
            if site.status_code >= 400:
                continue
        except Exception:
            continue
        rows.append(
            {
                "company_name": name,
                "url": homepage,
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
    print(f"details={len(detail_urls)} candidates={len(rows)} -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
