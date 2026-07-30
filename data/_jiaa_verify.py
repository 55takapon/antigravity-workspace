import csv
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
INFILE = ROOT / "data" / "_jiaa_candidates.csv"
OUTFILE = ROOT / "data" / "_jiaa_verified_audit.csv"

POSITIVE = re.compile(
    r"(広告運用|運用型広告|インターネット広告|デジタル広告|Web広告|WEB広告|"
    r"ウェブ広告|リスティング広告|SNS広告|SNS運用|デジタルマーケティング|"
    r"Webマーケティング|WEBマーケティング|マーケティング支援|プロモーション支援)"
)
PROFILE_LINK = re.compile(
    r"(会社概要|企業情報|corporate|company|about|outline|profile|access|事業内容|service|contact)",
    re.I,
)
EXCLUDE_NAME = re.compile(
    r"(新聞|放送|テレビ|ラジオ|出版|マイクロソフト|グーグル|アマゾン|ソフトバンク|"
    r"メルカリ|楽天グループ|LINEヤフー|ByteDance|Spotify|Pinterest|Facebook|"
    r"アクセンチュア|電通$|博報堂$|大広$|東急エージェンシー|読売広告社|"
    r"マッキャン|TBS|フジテレビ|講談社|小学館|集英社|新潮社|文藝春秋|KADOKAWA)"
)


def visible_text(markup):
    markup = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", markup)
    markup = re.sub(r"(?s)<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def same_host(base, url):
    a = urlparse(base).netloc.lower().removeprefix("www.")
    b = urlparse(url).netloc.lower().removeprefix("www.")
    return not b or a == b


def fetch(session, url):
    try:
        r = session.get(url, timeout=15, allow_redirects=True)
        if r.status_code >= 400 or "text/html" not in r.headers.get("content-type", ""):
            return None
        r.encoding = r.apparent_encoding or r.encoding
        return r
    except requests.RequestException:
        return None


def address_candidates(text):
    patterns = [
        r"〒\s*(\d{3})[-ー‐‑–—−]?\s*(\d{4})\s*([^〒]{8,100})",
        r"(\d{3})[-ー‐‑–—−](\d{4})\s*([^〒]{8,100})",
    ]
    found = []
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            tail = re.split(
                r"(TEL|Tel|tel|電話|FAX|Fax|fax|Google|アクセス|代表者|設立|資本金|事業内容)",
                m.group(3),
                maxsplit=1,
            )[0]
            tail = tail.strip(" ：:｜|,，。")
            if re.search(r"(都|道|府|県).{1,12}(市|区|郡)", tail) and re.search(r"\d", tail):
                found.append(f"〒{m.group(1)}-{m.group(2)} {tail[:80]}")
    return found


def phone_candidates(text):
    phones = re.findall(r"(?:TEL|Tel|tel|電話)?\s*[:：]?\s*(0\d{1,4}[-‐‑–—−]\d{1,4}[-‐‑–—−]\d{3,4})", text)
    return list(dict.fromkeys(p.replace("‐", "-").replace("‑", "-").replace("–", "-").replace("—", "-").replace("−", "-") for p in phones))


def verify(row):
    if row["existing_name"] == "True" or row["existing_domain"] == "True":
        return None
    if EXCLUDE_NAME.search(row["company_name"]):
        return None
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; official-site-verification/1.0)"
    first = fetch(session, row["url"])
    if not first:
        return None
    pages = [(first.url, first.text)]
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', first.text, re.I | re.S)
    picked = []
    for href, label in links:
        label = visible_text(label)
        absolute = urljoin(first.url, html.unescape(href))
        if PROFILE_LINK.search(label + " " + href) and same_host(first.url, absolute):
            clean_url = absolute.split("#")[0]
            if clean_url not in picked and clean_url != first.url:
                picked.append(clean_url)
    for url in picked[:6]:
        r = fetch(session, url)
        if r:
            pages.append((r.url, r.text))
    combined = " ".join(visible_text(markup) for _, markup in pages)
    services = list(dict.fromkeys(POSITIVE.findall(combined)))
    addresses = address_candidates(combined)
    phones = phone_candidates(combined)
    has_contact = bool(re.search(r"(お問い合わせ|問い合わせ|contact)", combined, re.I))
    if not services or not addresses or not (phones or has_contact):
        return None
    return {
        "company_name": row["company_name"],
        "url": first.url,
        "address": addresses[0],
        "phone": phones[0] if phones else "",
        "has_contact": has_contact,
        "service_evidence": " / ".join(services[:5]),
        "pages_checked": " | ".join(url for url, _ in pages),
    }


with INFILE.open(encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

verified = []
with ThreadPoolExecutor(max_workers=12) as pool:
    futures = [pool.submit(verify, row) for row in rows]
    for future in as_completed(futures):
        item = future.result()
        if item:
            verified.append(item)

verified.sort(key=lambda x: x["company_name"])
with OUTFILE.open("w", newline="", encoding="utf-8-sig") as f:
    fields = ["company_name", "url", "address", "phone", "has_contact", "service_evidence", "pages_checked"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(verified)

print(f"verified={len(verified)} out={OUTFILE}")
