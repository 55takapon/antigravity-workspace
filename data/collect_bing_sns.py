import argparse
import base64
import csv
import json
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup


CITIES = "札幌市 旭川市 函館市 青森市 八戸市 盛岡市 仙台市 秋田市 山形市 福島市 郡山市 新潟市 長岡市 富山市 金沢市 福井市 長野市 松本市 甲府市 水戸市 つくば市 宇都宮市 高崎市 前橋市 さいたま市 川越市 越谷市 千葉市 船橋市 柏市 横浜市 川崎市 藤沢市 相模原市 静岡市 浜松市 名古屋市 豊橋市 岡崎市 岐阜市 津市 四日市市 大津市 京都市 大阪市 堺市 神戸市 姫路市 奈良市 和歌山市 岡山市 倉敷市 広島市 福山市 山口市 高松市 松山市 高知市 福岡市 北九州市 久留米市 長崎市 熊本市 大分市 宮崎市 鹿児島市 那覇市".split()
TERMS = ["SNS運用", "Instagram運用", "TikTok運用", "SNS広告運用", "採用SNS運用", "店舗SNS運用"]
BLOCKED = ("bing.com", "google.com", "prtimes.jp", "wantedly.com", "indeed.com", "en-gage.net", "facebook.com", "instagram.com", "youtube.com", "x.com", "twitter.com", "tiktok.com", "note.com", "ameblo.jp", "wikipedia.org", "kakaku.com", "itreview.jp", "boxil.jp", "imitsu.jp", "comparaku.com", "stock-sun.com", "kame-rad.co.jp")
local = threading.local()


def session():
    if not hasattr(local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0"
        local.session = value
    return local.session


def decode_url(url):
    try:
        value = parse_qs(urlparse(url).query).get("u", [""])[0]
        if value.startswith("a1"):
            encoded = value[2:].replace("-", "+").replace("_", "/")
            encoded += "=" * (-len(encoded) % 4)
            return base64.b64decode(encoded).decode("utf-8")
    except Exception:
        pass
    return url


def host(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def clean_name(title):
    value = re.split(r"[|｜]| - ", title, maxsplit=1)[0].strip()
    return re.sub(r"\s*(公式サイト|ホームページ|トップページ|TOP)\s*$", "", value, flags=re.I)[:120]


def search(task):
    city, term = task
    query = f'{city} "{term}" 株式会社 -おすすめ -比較 -ランキング -求人 -まとめ'
    try:
        response = session().get("https://www.bing.com/search", params={"q": query, "count": 20}, timeout=(5, 20))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = []
        for item in soup.select("li.b_algo"):
            anchor = item.select_one("h2 a")
            if not anchor:
                continue
            url = decode_url(anchor.get("href", ""))
            domain = host(url)
            if not domain or any(domain == b or domain.endswith("." + b) for b in BLOCKED):
                continue
            rows.append({"company_name": clean_name(anchor.get_text(" ", strip=True)), "url": url, "address": "", "phone": "", "maps_url": "", "area_hint": city, "query": query})
        time.sleep(random.uniform(0.5, 1.0))
        return rows
    except Exception as exc:
        print(f"search_error city={city} term={term} error={type(exc).__name__}:{exc}", flush=True)
        time.sleep(1.5)
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_csv")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    tasks = [(city, term) for city in CITIES for term in TERMS]
    found = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(search, task) for task in tasks]
        for index, future in enumerate(as_completed(futures), 1):
            found.extend(future.result())
            if index % 25 == 0:
                print(f"queries={index}/{len(tasks)} raw={len(found)}", flush=True)
    deduped, seen = [], set()
    for row in found:
        domain = host(row["url"])
        if domain in seen:
            continue
        seen.add(domain)
        deduped.append(row)
    fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(deduped)
    print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
