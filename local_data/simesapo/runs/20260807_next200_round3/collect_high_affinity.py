from __future__ import annotations

import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import HEADERS, discover, host
from collect_interior import legal_name

JHCMA = "https://www.jhcma.or.jp/list/"
JPCA = "https://official-jpca.jp/member/"
OUT = Path(__file__).with_name("high_affinity_raw.csv")
SEED = Path(__file__).with_name("high_affinity_seed.csv")


def soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def company_from_text(text: str) -> str:
    patterns = [
        r"(?:株式会社|有限会社|合同会社|税理士法人)\s*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+",
        r"[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+\s*(?:株式会社|有限会社|合同会社)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return legal_name(match.group(0).strip())
    return ""


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    page = soup(JHCMA)
    dealer_wrap = page.select_one(".association_wrap")
    for card in dealer_wrap.select(".association_wrap_list") if dealer_wrap else []:
        link = card.select_one("a[href]")
        name = company_from_text(card.get_text(" ", strip=True))
        if link and name:
            rows.append({
                "company_name": name,
                "url": urljoin(JHCMA, link["href"]),
                "address": "",
                "phone": "",
                "contact_url": "",
                "区分": "A｜美容室・サロン向け経営・販促支援",
                "検出ワード": "美容室・サロン顧客＋経営・教育・販促支援",
                "source_url": JHCMA,
                "source_card": card.get_text(" ", strip=True),
                "segment": "beauty_dealer",
            })

    page = soup(JPCA)
    for card in page.select(".item_wrap"):
        link = card.select_one("a[href]")
        name = company_from_text(card.get_text(" ", strip=True))
        if link and name:
            rows.append({
                "company_name": name,
                "url": urljoin(JPCA, link["href"]),
                "address": "",
                "phone": "",
                "contact_url": "",
                "区分": "A｜医院・クリニック開業・経営支援",
                "検出ワード": "医院・クリニック顧客＋開業・経営・運営支援",
                "source_url": JPCA,
                "source_card": card.get_text(" ", strip=True),
                "segment": "clinic_opening",
            })
    return rows


def official_text(url: str) -> str:
    try:
        page = soup(url)
    except Exception:
        return ""
    texts = [page.get_text(" ", strip=True)]
    root = host(url)
    scored: list[tuple[int, str]] = []
    for link in page.select("a[href]"):
        href = urljoin(url, link.get("href", ""))
        label = link.get_text(" ", strip=True)
        if host(href) != root:
            continue
        score = sum(word in (label + href).lower() for word in ["service", "support", "business", "salon", "medical", "clinic", "開業", "経営", "事業", "支援"])
        if score:
            scored.append((score, href))
    for _, href in sorted(scored, reverse=True)[:5]:
        try:
            texts.append(soup(href).get_text(" ", strip=True))
        except Exception:
            pass
    return " ".join(texts)


def affinity(row: dict[str, str]) -> tuple[bool, str]:
    text = official_text(row["url"])
    if not text:
        return False, "official_unreachable"
    if row["segment"] == "beauty_dealer":
        target = any(word in text for word in ["美容室", "美容院", "ヘアサロン", "サロン様", "サロン経営"])
        support_words = [word for word in ["経営", "開業", "集客", "販促", "教育", "セミナー", "講習", "サポート", "コンサル"] if word in text]
        continuous = any(word in text for word in ["定期", "継続", "訪問", "営業担当", "ディーラー", "会員", "オンラインショップ", "受発注"])
    else:
        target = any(word in text for word in ["医院", "クリニック", "医療機関", "医師", "歯科"])
        support_words = [word for word in ["開業", "経営", "集患", "マーケティング", "承継", "運営", "コンサル", "サポート"] if word in text]
        continuous = any(word in text for word in ["開業後", "継続", "顧問", "経営支援", "ワンストップ", "総合支援", "伴走"])
    ok = target and len(support_words) >= 2 and continuous
    return ok, "+".join(support_words[:5]) if ok else "affinity_evidence_short"


def validate(row: dict[str, str]) -> dict[str, str]:
    enriched = discover(row)
    ok, evidence = affinity(row)
    enriched["affinity_confirmed"] = "yes" if ok else "no"
    enriched["affinity_evidence"] = evidence
    return enriched


rows = {host(row["url"]): row for row in source_rows() if host(row["url"])}
results: list[dict[str, str]] = []
with ThreadPoolExecutor(max_workers=12) as pool:
    futures = [pool.submit(validate, row) for row in rows.values()]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: (row["segment"], row["company_name"]))

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
accepted = [
    row for row in results
    if row.get("company_confirmed") == "yes"
    and row.get("affinity_confirmed") == "yes"
    and bool(row.get("contact_url"))
]
seed_fields = ["company_name", "url", "address", "phone", "contact_url", "区分", "検出ワード", "source_url"]
with SEED.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=seed_fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(accepted)
print({
    "parsed": len(rows),
    "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results),
    "contact_found": sum(bool(row.get("contact_url")) for row in results),
    "affinity_confirmed": sum(row.get("affinity_confirmed") == "yes" for row in results),
    "all_gates": len(accepted),
    "output": str(OUT),
    "seed": str(SEED),
})
