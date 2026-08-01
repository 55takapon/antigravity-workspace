import argparse
import csv
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


LOCAL = re.compile(r"(店舗|来店|実店舗|多店舗|飲食|レストラン|美容|サロン|クリニック|歯科|医院|病院|不動産|住宅|工務店|学習塾|スクール|士業|ホテル|旅館|小売|地域密着)")
SUPPORT = re.compile(r"(集客|販促|販売促進|マーケティング|広告運用|Web制作|WEB制作|ホームページ制作|ブランディング|プロモーション|コンサルティング)", re.I)
SNS = re.compile(r"(SNS運用|Instagram運用|インスタ運用|TikTok運用|LINE公式アカウント運用|SNS広告)", re.I)
RECURRING = re.compile(r"(運用代行|継続支援|月額|伴走|定期レポート|改善提案|アカウント運用)")
COMPETITOR = re.compile(r"(MEO対策|MEO運用|Googleビジネスプロフィール運用|Googleマップ集客|ローカルSEO専門)", re.I)
local_state = threading.local()


def session():
    if not hasattr(local_state, "session"):
        value = requests.Session(); value.headers["User-Agent"] = "Mozilla/5.0"
        local_state.session = value
    return local_state.session


def score(row):
    try:
        urls = [row["url"]]
        urls.extend(url.strip() for url in (row.get("pages_checked") or "").split(" | ") if url.strip())
        texts, title_text = [], ""
        for index, url in enumerate(list(dict.fromkeys(urls))[:4]):
            response = session().get(url, timeout=(5, 12), allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            texts.append(soup.get_text(" ", strip=True))
            if index == 0:
                title_text = " ".join(node.get_text(" ", strip=True) for node in soup.select("title,h1")[:4])
        text = " ".join(texts)
    except requests.RequestException:
        return None
    local_hits = len(LOCAL.findall(text))
    support_hits = len(SUPPORT.findall(text))
    sns_hits = len(SNS.findall(text))
    recurring_hits = len(RECURRING.findall(text))
    competitor_hits = len(COMPETITOR.findall(text))
    direct_competitor = bool(COMPETITOR.search(title_text) or (competitor_hits >= 8 and sns_hits <= 2))
    if direct_competitor or sns_hits == 0:
        return None
    points = min(local_hits, 4) * 2 + min(support_hits, 4) + min(recurring_hits, 3) * 2
    if local_hits >= 2 and support_hits >= 2:
        grade = "A"
    elif local_hits >= 1 and support_hits >= 1 and recurring_hits >= 1:
        grade = "A"
    elif support_hits >= 2 and recurring_hits >= 1:
        grade = "B"
    else:
        return None
    result = dict(row)
    result["affinity_grade"] = grade
    result["affinity_score"] = str(points)
    result["local_hits"] = str(local_hits)
    result["competitor_hits"] = str(competitor_hits)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()
    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    kept = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(score, row) for row in rows]
        for future in as_completed(futures):
            item = future.result()
            if item:
                kept.append(item)
    kept.sort(key=lambda row: (row["affinity_grade"], -int(row["affinity_score"])))
    fields = list(rows[0].keys()) + ["affinity_grade", "affinity_score", "local_hits", "competitor_hits"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(kept)
    print(f"input={len(rows)} kept={len(kept)} A={sum(r['affinity_grade']=='A' for r in kept)} B={sum(r['affinity_grade']=='B' for r in kept)}")


if __name__ == "__main__":
    main()
