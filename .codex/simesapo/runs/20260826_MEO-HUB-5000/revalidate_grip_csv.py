import argparse
import csv
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup


UA = "Mozilla/5.0 (compatible; SimesapoResearch/1.0; +https://simesapo.com/)"
TERMS = ("WEB制作", "Web制作", "ウェブ制作", "ホームページ制作", "サイト制作", "サイト構築", "マーケティング", "広告", "販促", "プロモーション", "SNS", "SEO", "MEO", "ブランディング", "デザイン", "印刷")
lock = threading.Lock()
last_request = 0.0


def fetch(row):
    global last_request
    try:
        with lock:
            wait = 0.2 - (time.monotonic() - last_request)
            if wait > 0:
                time.sleep(wait)
            last_request = time.monotonic()
        response = requests.get(row["source_url"], timeout=(5, 12), headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        business = " ".join(node.get_text(" ", strip=True) for node in soup.select("p.sec-db__list-desc"))
        row["business_description"] = business
        if not business or not any(term.lower() in business.lower() for term in TERMS):
            return row, False
        phone = row.get("phone", "")
        if "代表者名" in phone or len(re.sub(r"\D", "", phone)) < 9:
            row["phone"] = ""
        return row, True
    except requests.RequestException:
        return row, False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    with open(args.source, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    kept = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(fetch, row) for row in rows]
        for index, future in enumerate(as_completed(futures), 1):
            row, ok = future.result()
            if ok:
                kept.append(row)
            if index % 100 == 0:
                print(f"checked={index} kept={len(kept)}", flush=True)
    with open(args.output, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(kept)
    print(f"done checked={len(rows)} kept={len(kept)}")


if __name__ == "__main__":
    main()
