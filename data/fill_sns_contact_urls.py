import csv
import html
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


CONTACT = re.compile(r"(お問い合わせ|お問合せ|問い合わせ|contact|inquiry|toiawase|otoiawase)", re.I)
PHONE = re.compile(r"(?<!\d)(0\d{1,4}[-‐‑–—−]\d{1,4}[-‐‑–—−]\d{3,4})(?!\d)")
local = threading.local()


def host(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def session():
    if not hasattr(local, "session"):
        value = requests.Session(); value.headers["User-Agent"] = "Mozilla/5.0"
        local.session = value
    return local.session


def fill(row):
    if (row.get("phone") or "").strip():
        return row
    try:
        start_url = (row.get("contact_url") or row["url"]).strip()
        response = session().get(start_url, timeout=(5, 12), allow_redirects=True)
        response.raise_for_status()
        text = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
        phones = PHONE.findall(text)
        if phones:
            row["phone"] = phones[0].translate(str.maketrans("‐‑–—−", "-----"))
            return row
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.select("a[href]"):
            href = html.unescape(anchor.get("href", ""))
            label = anchor.get_text(" ", strip=True)
            if CONTACT.search(f"{label} {href}"):
                target = urljoin(response.url, href).split("#")[0]
                if host(target) == host(response.url) and target.startswith("http"):
                    row["contact_url"] = target
                    contact_response = session().get(target, timeout=(5, 12), allow_redirects=True)
                    contact_text = BeautifulSoup(contact_response.text, "html.parser").get_text(" ", strip=True)
                    phones = PHONE.findall(contact_text)
                    if phones:
                        row["phone"] = phones[0].translate(str.maketrans("‐‑–—−", "-----"))
                    return row
    except requests.RequestException:
        pass
    return row


with Path("data/sns_strict_pure_new.csv").open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
with ThreadPoolExecutor(max_workers=12) as executor:
    futures = [executor.submit(fill, row) for row in rows]
    output = [future.result() for future in as_completed(futures)]
fields = list(rows[0].keys())
with Path("data/sns_strict_with_contacts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(output)
print(f"total={len(output)} contact={sum(bool(r.get('contact_url')) for r in output)} phone={sum(bool(r.get('phone')) for r in output)}")
