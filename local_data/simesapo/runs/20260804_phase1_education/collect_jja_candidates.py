from __future__ import annotations

import csv
import html
import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

HERE = Path(__file__).parent
SOURCE = "https://jja.or.jp/member-list/kigyou/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}

EXCLUDE_TERMS = (
    "GMO", "NTT", "リクルート", "ラクスル", "東京海上", "ジャックス",
    "小学館", "学研", "東京書籍", "セイコーソリューションズ", "CyberOwl",
    "カンリー", "すららネット", "モノグサ", "ライフイズテック",
)

SERVICE_RULES = [
    (("学習塾", "塾", "予備校"), "学習塾・予備校向け支援"),
    (("スクール", "教室運営", "生徒管理", "校務"), "スクール・教室運営支援"),
    (("教材", "教育出版", "学習参考書", "テスト", "模試"), "教材・テスト・教育コンテンツ支援"),
    (("集客", "生徒募集", "マーケティング", "広告", "ホームページ"), "教育機関向け集客・制作支援"),
    (("決済", "集金", "請求", "月謝"), "教育施設向け決済・集金支援"),
    (("入退室", "保護者", "連絡", "管理システム", "ICT", "DX"), "教育施設向けICT・業務支援"),
    (("印刷", "チラシ", "パンフレット"), "学習塾向け印刷・販促支援"),
    (("経営", "コンサルティング", "研修", "人材"), "教育事業向け経営・人材支援"),
]


def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "")).lower()


def company_key(value: str) -> str:
    value = re.sub(r"株式会社|有限会社|合同会社|合資会社|一般社団法人|公益財団法人|特定非営利活動法人|[・･.,，．_'\"()（）\[\]［］:：\-]", "", norm(value))
    return value


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tr = False
        self.in_td = False
        self.rows: list[list[dict]] = []
        self.row: list[dict] = []
        self.cell_text: list[str] = []
        self.cell_href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag == "tr":
            self.in_tr = True
            self.row = []
        elif tag == "td" and self.in_tr:
            self.in_td = True
            self.cell_text = []
            self.cell_href = ""
        elif tag == "a" and self.in_td and not self.cell_href:
            self.cell_href = attrs_d.get("href") or ""

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_td:
            self.row.append({"text": " ".join(self.cell_text).strip(), "href": self.cell_href})
            self.in_td = False
        elif tag == "tr" and self.in_tr:
            if self.row:
                self.rows.append(self.row)
            self.in_tr = False


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self.links: list[dict] = []
        self.anchor_text: list[str] | None = None
        self.anchor_href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_d = dict(attrs)
        if tag == "a":
            self.anchor_text = []
            self.anchor_href = attrs_d.get("href") or ""
        for key in ("title", "alt"):
            if attrs_d.get(key):
                self.text.append(attrs_d[key] or "")

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.anchor_text is not None:
            self.anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.anchor_text is not None:
            self.links.append({"href": self.anchor_href, "text": " ".join(self.anchor_text).strip(), "alt_title": ""})
            self.anchor_text = None
            self.anchor_href = ""


def fetch_candidate(item: dict) -> dict | None:
    try:
        response = requests.get(item["url"], headers=HEADERS, timeout=20, allow_redirects=True)
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""):
            return None
    except Exception:
        return None
    parser = PageParser()
    try:
        parser.feed(response.text)
    except Exception:
        return None
    page_text = html.unescape(" ".join(parser.text))
    compact = norm(page_text)
    ck = company_key(item["company_name"])
    if not ck or ck not in company_key(page_text):
        return None
    evidence = ""
    for terms, label in SERVICE_RULES:
        if any(norm(term) in compact for term in terms):
            evidence = label
            break
    if not evidence:
        return None
    final_url = response.url
    links = []
    for link in parser.links:
        href = (link.get("href") or "").strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        absolute = urljoin(final_url, href)
        signal = f"{absolute} {link.get('text', '')} {link.get('alt_title', '')}"
        if urlparse(absolute).scheme in ("http", "https") and re.search(
            r"contact|inquiry|form|otoiawase|toiawase|お問い合わせ|お問合せ|問合せ|ご相談|資料請求",
            signal,
            re.I,
        ):
            links.append({**link, "href": absolute})
    return {**item, "url": final_url, "evidence": evidence, "links": links}


def main() -> None:
    response = requests.get(SOURCE, headers=HEADERS, timeout=30)
    response.raise_for_status()
    parser = TableParser()
    parser.feed(response.text)
    raw: list[dict] = []
    for row in parser.rows:
        if not row or not row[0].get("href"):
            continue
        name = re.sub(r"\s+", "", row[0]["text"])
        href = urljoin(SOURCE, row[0]["href"])
        if not name or not any(term in name for term in ("会社", "法人")):
            continue
        if any(term.lower() in name.lower() for term in EXCLUDE_TERMS):
            continue
        raw.append({"company_name": name, "url": href, "source_url": SOURCE})

    fetched: list[dict] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(fetch_candidate, item) for item in raw]
        for future in as_completed(futures):
            result = future.result()
            if result:
                fetched.append(result)
    fetched.sort(key=lambda row: row["company_name"])

    seed_fields = ["company_name", "url", "contact_url", "区分", "検出ワード", "source_url"]
    with (HERE / "education_candidate_seed.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=seed_fields)
        writer.writeheader()
        for row in fetched:
            writer.writerow({
                "company_name": row["company_name"],
                "url": row["url"],
                "contact_url": "",
                "区分": "S｜業界特化Web制作・店舗支援ハブ",
                "検出ワード": f"教育業界ハブ：{row['evidence']}",
                "source_url": row["url"],
            })
    pages = [{"idx": idx, "base_url": row["url"], "links": row["links"]} for idx, row in enumerate(fetched)]
    (HERE / "education_pages.json").write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    for start in range(0, len(pages), 10):
        (HERE / f"education_pages_{start // 10}.json").write_text(
            json.dumps(pages[start:start + 10], ensure_ascii=False), encoding="utf-8"
        )
    print(json.dumps({"association_rows": len(raw), "official_service_verified": len(fetched), "pages": len(pages)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
