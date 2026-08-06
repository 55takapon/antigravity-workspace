from __future__ import annotations

import csv
import base64
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import HEADERS, discover, host
from collect_interior import legal_name

SOURCE = "https://zenbishoren.com/"
OUT = Path(__file__).with_name("zenbishoren_raw.csv")
SEED = Path(__file__).with_name("zenbishoren_seed.csv")
BLOCKED = {
    "zenbishoren.com", "jhcma.or.jp", "facebook.com", "instagram.com", "x.com", "youtube.com",
    "prtimes.jp", "wantedly.com", "en-gage.net", "indeed.com", "mapion.co.jp", "itp.ne.jp",
}


def fetch(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def normalize_member(text: str) -> str:
    text = re.sub(r"\s+(?:[東西南北]?(?:支店|支社|営業所|地区本部)|[（(].*?[）)])(?:.*)?$", "", text.strip())
    text = text.replace("(株)", "株式会社").replace("（株）", "株式会社")
    text = text.replace("(有)", "有限会社").replace("（有）", "有限会社")
    return legal_name(text)


def member_names() -> list[str]:
    page = fetch(SOURCE)
    names: list[str] = []
    for item in page.select("li"):
        text = item.get_text(" ", strip=True)
        if not re.search(r"(?:株式会社|有限会社|合同会社|\(株\)|（株）|\(有\)|（有）)", text):
            continue
        name = normalize_member(text)
        if re.search(r"株式会社|有限会社|合同会社", name) and not re.search(r"組合|協会|学校", name):
            names.append(name)
    return list(dict.fromkeys(names))


def bing_candidates(name: str) -> list[str]:
    search_name = re.sub(r"株式会社|有限会社|合同会社", "", name).strip()
    try:
        response = requests.get(
            "https://www.bing.com/search",
            params={"q": f'"{search_name}" 美容 ディーラー'},
            headers=HEADERS,
            timeout=25,
        )
        response.raise_for_status()
    except Exception:
        return []
    page = BeautifulSoup(response.text, "html.parser")
    urls: list[str] = []
    for link in page.select("li.b_algo h2 a[href]"):
        url = link.get("href", "")
        if host(url) == "bing.com":
            encoded = parse_qs(urlparse(url).query).get("u", [""])[0]
            if encoded.startswith("a1"):
                try:
                    url = base64.b64decode(encoded[2:] + "===").decode("utf-8")
                except Exception:
                    continue
        domain = host(url)
        if url.startswith("http") and domain and not any(domain == b or domain.endswith("." + b) for b in BLOCKED):
            urls.append(url)
    return urls[:4]


def page_text(url: str) -> str:
    try:
        page = fetch(url)
    except Exception:
        return ""
    texts = [page.get_text(" ", strip=True)]
    domain = host(url)
    links: list[tuple[int, str]] = []
    for link in page.select("a[href]"):
        href = urljoin(url, link.get("href", ""))
        label = link.get_text(" ", strip=True)
        if host(href) != domain:
            continue
        score = sum(word in (label + href).lower() for word in ["service", "support", "business", "salon", "美容", "経営", "開業", "事業", "支援"])
        if score:
            links.append((score, href))
    for _, href in sorted(links, reverse=True)[:5]:
        try:
            texts.append(fetch(href).get_text(" ", strip=True))
        except Exception:
            pass
    return " ".join(texts)


def probe(name: str) -> dict[str, str] | None:
    for url in bing_candidates(name):
        text = page_text(url)
        if not text:
            continue
        target = any(word in text for word in ["美容室", "美容院", "ヘアサロン", "サロン様", "サロン経営"])
        support = [word for word in ["経営", "開業", "集客", "販促", "教育", "セミナー", "講習", "サポート", "コンサル"] if word in text]
        continuous = any(word in text for word in ["定期", "継続", "訪問", "営業担当", "ディーラー", "会員", "受発注"])
        if not (target and len(support) >= 2 and continuous):
            continue
        row = {
            "company_name": name,
            "url": url,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "A｜美容室・サロン向け経営・販促支援",
            "検出ワード": "美容室・サロン顧客＋経営・教育・販促支援",
            "source_url": SOURCE,
        }
        result = discover(row)
        result["affinity_confirmed"] = "yes"
        result["affinity_evidence"] = "+".join(support[:5])
        return result
    return None


names = member_names()
results: list[dict[str, str]] = []
with ThreadPoolExecutor(max_workers=10) as pool:
    futures = [pool.submit(probe, name) for name in names]
    for future in as_completed(futures):
        result = future.result()
        if result:
            results.append(result)
results = list({host(row["url"]): row for row in results if host(row["url"])}.values())
results.sort(key=lambda row: row["company_name"])

if results:
    with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    accepted = [row for row in results if row.get("company_confirmed") == "yes" and bool(row.get("contact_url"))]
    fields = ["company_name", "url", "address", "phone", "contact_url", "区分", "検出ワード", "source_url"]
    with SEED.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(accepted)
else:
    accepted = []
print({"member_names": len(names), "affinity_found": len(results), "all_gates": len(accepted), "seed": str(SEED)})
