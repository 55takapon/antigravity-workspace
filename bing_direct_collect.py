import base64
import csv
import json
import re
import time
from collections import Counter
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup

BASE = Path("data")
EXCLUDE = BASE / "_exclude_plus_existing_non_kanto_300.json"
OUT = BASE / "list_non_kanto_bing_direct_auto.csv"

AREAS = [
    ("北海道", ["札幌市", "旭川市", "函館市"]),
    ("宮城県", ["仙台市", "石巻市"]),
    ("京都府", ["京都市", "宇治市"]),
    ("兵庫県", ["神戸市", "姫路市", "西宮市", "尼崎市"]),
    ("福岡県", ["福岡市", "北九州市", "久留米市"]),
    ("静岡県", ["静岡市", "浜松市", "沼津市"]),
    ("岡山県", ["岡山市", "倉敷市"]),
    ("広島県", ["広島市", "福山市"]),
    ("新潟県", ["新潟市", "長岡市"]),
    ("熊本県", ["熊本市"]),
    ("鹿児島県", ["鹿児島市"]),
    ("長野県", ["長野市", "松本市"]),
    ("石川県", ["金沢市"]),
    ("富山県", ["富山市"]),
    ("愛媛県", ["松山市"]),
    ("香川県", ["高松市"]),
]

DENY = (
    "bing.com", "google.", "yahoo.", "web-kanji", "biz.ne.jp", "wk-partners",
    "yuryoweb", "imitsu", "homepage.work", "zehitomo", "tcd-theme",
    "note.com", "facebook.com", "instagram.com", "x.com", "twitter.com",
    "youtube.com", "wantedly.com", "indeed.com",
)


def norm_url(url):
    url = (url or "").strip().lower()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url.split("/")[0].rstrip("/")


def norm_name(name):
    return re.sub(
        r"株式会社|有限会社|合同会社|一般社団法人|（株）|\(株\)|[\s　・,，.。/／｜|（）()\[\]【】「」\-ー]",
        "",
        (name or "").lower(),
    )


def decode_bing(url):
    qs = parse_qs(urlparse(unescape(url)).query)
    if "u" not in qs:
        return url
    token = qs["u"][0]
    if token.startswith("a1"):
        token = token[2:]
    try:
        pad = "=" * (-len(token) % 4)
        return base64.urlsafe_b64decode(token + pad).decode("utf-8", "ignore")
    except Exception:
        return url


def clean_title(t):
    t = unescape(t or "")
    t = re.split(r"\s[-|｜–—]\s|[｜|]", t)[0]
    t = re.sub(r"(ホームページ制作|Web制作|WEB制作|ウェブ制作|公式).*", "", t, flags=re.I)
    return t.strip(" -｜|:：")


def verified(url, pref, city):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}, timeout=8, allow_redirects=True)
        if r.status_code >= 400 or "text/html" not in r.headers.get("content-type", ""):
            return False
        text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
        has_service = any(x in text for x in ["ホームページ制作", "Web制作", "WEB制作", "ウェブ制作", "Webサイト制作"])
        has_area = pref in text or city in text
        return has_service and has_area
    except Exception:
        return False


exclude = json.loads(EXCLUDE.read_text(encoding="utf-8"))
exu = {norm_url(r.get("url", "")) for r in exclude if r.get("url")}
exn = {norm_name(r.get("company_name", "")) for r in exclude if r.get("company_name")}

records = []
seen_u = set()
seen_n = set()
stats = Counter()
pref_count = Counter()
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0", "Accept-Language": "ja,en;q=0.9"})

for pref, cities in AREAS:
    for city in cities:
        for kw in ["ホームページ制作 会社", "Web制作会社", "Webサイト制作 会社"]:
            q = f"{city} {kw} 公式 -Web幹事 -比較ビズ -優良WEB"
            html = session.get("https://www.bing.com/search?q=" + quote_plus(q) + "&setlang=ja&cc=JP", timeout=15).text
            soup = BeautifulSoup(html, "html.parser")
            anchors = soup.select("h2 a[href]") or soup.select("a[href]")
            for a in anchors[:25]:
                title = clean_title(a.get_text(" ", strip=True))
                url = decode_bing(a.get("href") or "")
                host = urlparse(url).netloc.lower()
                if not title or not url.startswith("http") or any(d in host for d in DENY):
                    continue
                u = norm_url(url)
                n = norm_name(title)
                if not u or not n or u in exu or n in exn or u in seen_u or n in seen_n:
                    stats["duplicate_or_bad"] += 1
                    continue
                if not verified(url, pref, city):
                    stats["not_verified"] += 1
                    continue
                seen_u.add(u)
                seen_n.add(n)
                pref_count[pref] += 1
                records.append({"company_name": title, "url": url, "address": pref + city, "phone": "", "maps_url": ""})
            time.sleep(0.6)

with OUT.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["company_name", "url", "address", "phone", "maps_url"])
    w.writeheader()
    w.writerows(records)

print("kept", len(records), dict(pref_count), dict(stats), OUT)
