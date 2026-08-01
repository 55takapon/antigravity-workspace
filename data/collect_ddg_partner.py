import argparse
import csv
import html
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

import collect_bing_sns as base


SECONDARY_CITIES = """
小樽市 苫小牧市 帯広市 釧路市 北見市 弘前市 十和田市 一関市 奥州市 石巻市 大崎市
横手市 大館市 鶴岡市 酒田市 会津若松市 いわき市 日立市 ひたちなか市 古河市
小山市 足利市 太田市 伊勢崎市 桐生市 熊谷市 春日部市 所沢市 狭山市 戸田市 草加市
市川市 松戸市 流山市 木更津市 成田市 八王子市 立川市 町田市 武蔵野市 三鷹市 調布市
横須賀市 鎌倉市 茅ヶ崎市 厚木市 海老名市 長岡市 上越市 三条市 燕市 高岡市 射水市
小松市 加賀市 敦賀市 坂井市 甲斐市 富士吉田市 上田市 飯田市 諏訪市 安曇野市
大垣市 多治見市 各務原市 富士市 沼津市 磐田市 焼津市 藤枝市 一宮市 春日井市
豊田市 刈谷市 安城市 小牧市 半田市 稲沢市 鈴鹿市 松阪市 伊勢市 草津市 彦根市
長浜市 宇治市 亀岡市 茨木市 高槻市 枚方市 豊中市 吹田市 東大阪市 八尾市
岸和田市 和泉市 西宮市 尼崎市 明石市 加古川市 宝塚市 橿原市 生駒市 田辺市
米子市 倉吉市 出雲市 津山市 玉野市 尾道市 東広島市 廿日市市 下関市 周南市
岩国市 鳴門市 阿南市 丸亀市 三豊市 今治市 新居浜市 西条市 南国市 四万十市
飯塚市 大牟田市 糸島市 佐世保市 諫早市 八代市 玉名市 別府市 中津市 延岡市
都城市 霧島市 薩摩川内市 浦添市 宜野湾市 沖縄市 うるま市
""".split()

TERMS_A = [
    "SNS運用 支援会社", "Web広告 運用会社", "LINE公式 運用支援会社",
    "Webマーケティング会社", "店舗集客 支援会社", "販売促進 デジタル会社",
    "Web制作 広告運用会社", "地域広告代理店 Web", "動画マーケティング会社",
    "中小企業 マーケティング支援会社",
]
TERMS_B = [
    "飲食店 SNS集客 支援会社", "美容サロン Web集客 支援会社",
    "クリニック マーケティング会社", "不動産 Webマーケティング会社",
    "工務店 集客支援会社", "学習塾 マーケティング会社",
    "採用広報 SNS支援会社", "CRM 販促支援会社",
    "地域ブランディング会社", "PR会社 デジタルマーケティング",
]

BLOCKED = base.BLOCKED + (
    "duckduckgo.com", "prtimes.jp", "wantedly.com", "indeed.com", "note.com",
    "ameblo.jp", "facebook.com", "instagram.com", "youtube.com",
)


def host(url):
    return urlparse(url).netloc.lower().removeprefix("www.")


def decode_url(value):
    value = html.unescape(value or "")
    if value.startswith("//"):
        value = "https:" + value
    query = parse_qs(urlparse(value).query)
    if "uddg" in query:
        return unquote(query["uddg"][0])
    return value


def search(task):
    area, term = task
    query = f'{area} {term} 株式会社 -おすすめ -比較 -ランキング -求人 -まとめ'
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query, "kl": "jp-jp"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=(5, 20),
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = []
        for anchor in soup.select("a.result__a"):
            url = decode_url(anchor.get("href", ""))
            domain = host(url)
            title = anchor.get_text(" ", strip=True)
            if not domain or not title or any(domain == b or domain.endswith("." + b) for b in BLOCKED):
                continue
            if any(word in title for word in ("おすすめ", "比較", "ランキング", "求人", "一覧", "選！")):
                continue
            rows.append({
                "company_name": base.clean_name(title), "url": url, "address": "", "phone": "",
                "maps_url": "", "area_hint": area, "query": query,
            })
        time.sleep(random.uniform(0.7, 1.2))
        return rows
    except requests.RequestException:
        time.sleep(2.0)
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_csv")
    parser.add_argument("--lane", choices=["a", "b"], required=True)
    args = parser.parse_args()
    midpoint = len(SECONDARY_CITIES) // 2
    areas = SECONDARY_CITIES[:midpoint] if args.lane == "a" else SECONDARY_CITIES[midpoint:]
    terms = TERMS_A if args.lane == "a" else TERMS_B
    tasks = [(area, term) for area in areas for term in terms]
    tasks = tasks[:60]
    found = []
    with ThreadPoolExecutor(max_workers=1) as executor:
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
        writer.writeheader()
        writer.writerows(deduped)
    print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
