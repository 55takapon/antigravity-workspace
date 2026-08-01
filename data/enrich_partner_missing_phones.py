import csv
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PHONE = re.compile(r"(?<!\d)(0\d{1,4}[ー\-‐‑‒–—−]\d{1,4}[ー\-‐‑‒–—−]\d{3,4})(?!\d)")
LINK = re.compile(r"(会社概要|企業情報|会社情報|アクセス|お問い合わせ|contact|company|about|profile|access)", re.I)
local = threading.local()


def session():
    if not hasattr(local, "value"):
        local.value = requests.Session()
        local.value.headers["User-Agent"] = "Mozilla/5.0"
    return local.value


def host(url):
    return urlparse(url).netloc.lower().removeprefix("www.")


def fetch(url):
    try:
        response = session().get(url, timeout=(5, 12), allow_redirects=True, stream=True)
        if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
            response.close()
            return None
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            chunks.append(chunk)
            size += len(chunk)
            if size >= 1_000_000:
                break
        response._content = b"".join(chunks)[:1_000_000]
        response.close()
        response.encoding = response.apparent_encoding or response.encoding
        return response
    except requests.RequestException:
        return None


def normalize_phone(value):
    value = re.sub(r"[ー‐‑‒–—−]", "-", value)
    return value.strip()


def phone_from_soup(soup):
    for anchor in soup.select('a[href^="tel:"]'):
        value = re.sub(r"[^0-9]", "", anchor.get("href", ""))
        if 10 <= len(value) <= 11 and value.startswith("0"):
            if len(value) == 10:
                return f"{value[:3]}-{value[3:6]}-{value[6:]}"
            return f"{value[:3]}-{value[3:7]}-{value[7:]}"
    text = soup.get_text(" ", strip=True)
    for match in PHONE.finditer(text):
        context = text[max(0, match.start() - 12):match.start()].upper()
        if "FAX" not in context:
            return normalize_phone(match.group(1))
    return ""


def enrich(row):
    first = fetch(row["url"])
    if not first:
        return row, False
    soups = [BeautifulSoup(first.text, "html.parser")]
    links = []
    for anchor in soups[0].select("a[href]"):
        target = urljoin(first.url, anchor.get("href", "")).split("#")[0]
        label = f"{anchor.get_text(' ', strip=True)} {anchor.get('href', '')}"
        if host(target) == host(first.url) and LINK.search(label) and target not in links:
            links.append(target)
    for target in links[:4]:
        response = fetch(target)
        if response:
            soups.append(BeautifulSoup(response.text, "html.parser"))
    for soup in soups:
        phone = phone_from_soup(soup)
        if phone:
            result = dict(row)
            result["phone"] = phone
            return result, True
    return row, False


latest_path = Path("data/sns_partner_final_latest.csv")
core_path = Path("data/sns_partner_final_core.csv")
output_path = Path("data/sns_partner_final_phone_enriched.csv")
with latest_path.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
with core_path.open(encoding="utf-8-sig", newline="") as handle:
    kept_domains = {host(row["url"]) for row in csv.DictReader(handle)}

targets = [row for row in rows if host(row["url"]) not in kept_domains]
results = {}
with ThreadPoolExecutor(max_workers=12) as executor:
    futures = {executor.submit(enrich, row): row for row in targets}
    for future in as_completed(futures):
        row, found = future.result()
        results[host(row["url"])] = row

final_rows = [results.get(host(row["url"]), row) for row in rows]
fields = ["company_name", "url", "address", "phone", "maps_url"]
with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(final_rows)
print(f"targets={len(targets)} phones_found={sum(bool(results[host(row['url'])].get('phone')) for row in targets)} output={output_path}")
