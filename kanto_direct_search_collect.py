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
EXCLUDE_PATH = BASE / "_exclude_plus_existing_kanto2.json"
OUT = BASE / "list_kanto_direct_search_filtered.csv"
STATS = BASE / "_kanto_direct_search_stats.json"

QUERIES = {
    "神奈川県": [
        "横浜市中区 ホームページ制作 会社",
        "横浜市港北区 Web制作会社",
        "横浜市都筑区 ホームページ制作",
        "川崎市中原区 Web制作会社",
        "川崎市高津区 ホームページ制作",
        "藤沢市 ホームページ制作 会社",
        "相模原市 Web制作会社",
        "厚木市 ホームページ制作 会社",
        "茅ヶ崎市 Web制作会社",
    ],
    "千葉県": [
        "千葉市中央区 ホームページ制作 会社",
        "船橋市 Web制作会社",
        "柏市 ホームページ制作 会社",
        "松戸市 Web制作会社",
        "市川市 ホームページ制作 会社",
        "浦安市 Web制作会社",
        "流山市 ホームページ制作 会社",
        "木更津市 Web制作会社",
    ],
    "茨城県": [
        "水戸市 ホームページ制作 会社",
        "つくば市 Web制作会社",
        "土浦市 ホームページ制作 会社",
        "ひたちなか市 Web制作会社",
        "日立市 ホームページ制作 会社",
    ],
    "群馬県": [
        "高崎市 ホームページ制作 会社",
        "前橋市 Web制作会社",
        "伊勢崎市 ホームページ制作 会社",
        "太田市 Web制作会社",
    ],
    "栃木県": [
        "宇都宮市 ホームページ制作 会社",
        "小山市 Web制作会社",
        "栃木市 ホームページ制作 会社",
        "足利市 Web制作会社",
    ],
    "埼玉県": [
        "さいたま市大宮区 ホームページ制作 会社",
        "さいたま市浦和区 Web制作会社",
        "川口市 ホームページ制作 会社",
        "川越市 Web制作会社",
        "所沢市 ホームページ制作 会社",
        "越谷市 Web制作会社",
    ],
}

DENY = (
    "web-kanji.com",
    "wk-partners.co.jp",
    "yuryoweb.com",
    "biz.ne.jp",
    "homepage.work",
    "zehitomo.com",
    "imitsu.jp",
    "imitsu.jp",
    "tcd-theme.com",
    "pitact.com",
    "dank-1.com",
    "google.com",
    "yahoo.co.jp",
    "bing.com",
    "mapion.co.jp",
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


def clean_title(title):
    title = unescape(title or "")
    title = re.split(r"[｜|]| - | – | — ", title)[0]
    title = re.sub(r"(ホームページ制作|Web制作会社|WEB制作会社|Web制作|ウェブ制作|公式サイト|トップページ).*", "", title, flags=re.I)
    return title.strip(" \t\n\r：:｜|-")


def search(query):
    url = "https://www.bing.com/search?q=" + quote_plus(query)
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    if r.status_code != 200:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for a in soup.select("li.b_algo h2 a[href], h2 a[href]"):
        href = a.get("href") or ""
        host = urlparse(href).netloc.lower()
        if not href.startswith("http") or any(d in host for d in DENY):
            continue
        title = clean_title(a.get_text(" ", strip=True))
        if len(title) < 2:
            continue
        out.append((title, href))
    return out


def looks_service_page(url, pref):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, allow_redirects=True)
        if r.status_code >= 400:
            return False, ""
        text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
        ok = ("ホームページ制作" in text or "Web制作" in text or "WEB制作" in text or "ウェブ制作" in text)
        if pref not in text and not any(x in text for x in ["横浜", "川崎", "千葉", "水戸", "つくば", "高崎", "前橋", "宇都宮", "さいたま", "川越"]):
            ok = False
        return ok, text[:300]
    except Exception:
        return False, ""


exclude = json.loads(EXCLUDE_PATH.read_text(encoding="utf-8"))
exu = {norm_url(r.get("url", "")) for r in exclude if r.get("url")}
exn = {norm_name(r.get("company_name", "")) for r in exclude if r.get("company_name")}

records = []
seen_u = set()
seen_n = set()
stats = {"queries": {}, "kept_pref": Counter(), "drop": Counter()}

for pref, queries in QUERIES.items():
    for q in queries:
        got = search(q)
        stats["queries"][q] = len(got)
        for title, url in got[:10]:
            u = norm_url(url)
            n = norm_name(title)
            if not u or not n:
                stats["drop"]["blank"] += 1
                continue
            if u in exu or n in exn or u in seen_u or n in seen_n:
                stats["drop"]["duplicate"] += 1
                continue
            ok, _ = looks_service_page(url, pref)
            if not ok:
                stats["drop"]["not_verified"] += 1
                continue
            seen_u.add(u)
            seen_n.add(n)
            stats["kept_pref"][pref] += 1
            records.append({"company_name": title, "url": url, "address": pref, "phone": "", "maps_url": ""})
        time.sleep(1.0)

with OUT.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["company_name", "url", "address", "phone", "maps_url"])
    w.writeheader()
    w.writerows(records)

STATS.write_text(
    json.dumps(
        {
            "kept_total": len(records),
            "kept_pref": dict(stats["kept_pref"]),
            "drop": dict(stats["drop"]),
            "queries": stats["queries"],
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print("kept", len(records), dict(stats["kept_pref"]), "drop", dict(stats["drop"]))
