import csv
import html
import json
import re
import urllib.parse
from html.parser import HTMLParser

import requests


JAAA_URL = "https://www.jaaa.ne.jp/about/member-companies/"
EXISTING_PATH = "data/_exclude_plus_existing_webmarketing_live.json"
OUTPUT_PATH = "data/main_jaaa_official_candidates_raw.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; prospect-research/1.0)"}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.links = []
        self._href = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")

    def handle_endtag(self, tag):
        if tag == "a":
            self._href = None
        if tag in {"p", "div", "li", "tr", "br", "dd", "dt", "h1", "h2", "h3"}:
            self.text_parts.append("\n")

    def handle_data(self, data):
        value = html.unescape(data).strip()
        if not value:
            return
        self.text_parts.append(value)
        if self._href:
            self.links.append((value, self._href))


def normalized_domain(url):
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    return parsed.netloc.lower().removeprefix("www.")


def normalized_name(value):
    value = re.sub(r"[\s\u3000・.\-]", "", value or "")
    return value.replace("株式会社", "").replace("有限会社", "").lower()


def fetch(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    parser = PageParser()
    parser.feed(response.text)
    text = "\n".join(part for part in parser.text_parts if part)
    return text, parser.links


def clean_address(value):
    value = re.sub(r"\s+", " ", value)
    value = re.split(r"(?:TEL|Tel|電話|FAX|Fax|アクセス|Google)", value)[0]
    return value.strip(" |:/")


def find_address(text):
    compact = re.sub(r"[ \t]+", " ", text)
    patterns = [
        r"(〒\s*\d{3}-\d{4}\s*[^\n]{5,100})",
        r"(\d{3}-\d{4}\s*(?:東京都|北海道|大阪府|京都府|.{2,3}県)[^\n]{5,100})",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact)
        if match:
            address = clean_address(match.group(1))
            if len(address) <= 120:
                return address
    return ""


def find_phone(text):
    for match in re.findall(r"(?<!\d)(0\d{1,4}[-‐‑–—ー]\d{1,4}[-‐‑–—ー]\d{3,4})(?!\d)", text):
        value = re.sub(r"[-‐‑–—ー]", "-", match)
        if not value.startswith(("0120", "0800")):
            return value
    return ""


def candidate_pages(home_url, links):
    base_domain = normalized_domain(home_url)
    scored = []
    keywords = ("company", "corporate", "profile", "outline", "about", "会社", "企業")
    for label, href in links:
        absolute = urllib.parse.urljoin(home_url, href)
        if normalized_domain(absolute) != base_domain:
            continue
        value = f"{label} {absolute}".lower()
        if any(keyword in value for keyword in keywords):
            scored.append(absolute)
    return list(dict.fromkeys([home_url, *scored]))[:6]


def main():
    jaaa_text, jaaa_links = fetch(JAAA_URL)
    members = [
        (label.strip(), urllib.parse.urljoin(JAAA_URL, href))
        for label, href in jaaa_links
        if "株式会社" in label or "有限会社" in label
    ]
    with open(EXISTING_PATH, encoding="utf-8") as handle:
        existing = json.load(handle)
    existing_domains = {normalized_domain(row.get("url", "")) for row in existing if row.get("url")}
    existing_names = {normalized_name(row.get("company_name", "")) for row in existing}

    rows = []
    for company_name, home_url in members:
        if normalized_domain(home_url) in existing_domains:
            continue
        if normalized_name(company_name) in existing_names:
            continue
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
        if address and (phone or "問い合わせ" in combined_text):
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
