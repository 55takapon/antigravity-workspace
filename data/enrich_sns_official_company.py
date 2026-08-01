import csv
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


LEGAL = re.compile(r"(株式会社|有限会社|合同会社|㈱|㈲|\bLLC\b|\bInc\.?\b)", re.I)
SERVICE = re.compile(r"(SNS運用(?:代行|支援)?|SNSマーケティング|Instagram運用(?:代行|支援)?|インスタ(?:グラム)?運用(?:代行|支援)?|TikTok運用(?:代行|支援)?|LINE公式アカウント運用(?:代行|支援)?|YouTube運用(?:代行|支援)?|SNS広告運用|Instagram広告運用|Meta広告運用)", re.I)
PLATFORM = re.compile(r"(SNS|ソーシャルメディア|Instagram|インスタ(?:グラム)?|TikTok|LINE公式|Twitter|YouTube)", re.I)
ACTION = re.compile(r"(運用代行|運用支援|アカウント運用|投稿代行|運用コンサル|マーケティング支援|広告運用|企画.{0,12}(?:投稿|撮影|分析))", re.I)
PARTNER_SERVICE = re.compile(r"(Webマーケティング|デジタルマーケティング|Web広告|広告運用|リスティング広告|Web制作|ホームページ制作|集客支援|販促支援|販売促進|プロモーション|マーケティング支援|ブランディング)", re.I)
OFFER = re.compile(r"(サービス|事業|支援|代行|コンサル|運用|提供)")
PROFILE = re.compile(r"(会社概要|企業情報|会社情報|corporate|company|about|outline|profile)", re.I)
BLOCKED = (
    "mypl.net", "mbp-japan.com", "prtimes.jp", "dreamnews.jp", "keizai.biz",
    "hakoshin.jp", "hokkaidotimes.jp", "pro-fukushima.com", "caloo.jp",
    "city.", "pref.", "vill.", "mhlw.go.jp", ".go.jp", "kankou", "tourism",
    "wikipedia.org", "note.com", "ameblo.jp", "vercel.app", "gurutto-",
)
local = threading.local()


def session():
    if not hasattr(local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0"
        local.session = value
    return local.session


def host(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def fetch(url):
    try:
        response = session().get(url, timeout=(5, 12), allow_redirects=True, stream=True)
        if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
            response.close()
            return None
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            chunks.append(chunk)
            size += len(chunk)
            if size >= 1_500_000:
                break
        response._content = b"".join(chunks)[:1_500_000]
        response.close()
        response.encoding = response.apparent_encoding or response.encoding
        return response
    except requests.RequestException:
        return None


def clean_candidate(value):
    value = re.sub(r"\s+", " ", value or "").strip(" |｜-–—:：")
    value = re.sub(r"^(?:©|Copyright\s*\d{0,4}|All Rights Reserved\.?)+\s*", "", value, flags=re.I)
    value = re.split(r"[|｜]| - | – | — |／|/", value, maxsplit=1)[0].strip()
    value = re.sub(r"^(会社名|商号|法人名|運営会社)\s*[:：]?\s*", "", value)
    if LEGAL.search(value) and 3 <= len(value) <= 70 and not re.search(r"(事例|ニュース|お知らせ|採用情報|求人|株式会社法|設立|代表取締役|様$)", value):
        return value
    return ""


def official_name(soups, fallback, has_maps):
    strong, weak = [], []
    if has_maps and LEGAL.search(fallback or ""):
        strong.append(clean_candidate(fallback))
    for index, soup in enumerate(soups):
        if index == 0:
            meta = soup.select_one('meta[property="og:site_name"]')
            if meta:
                weak.append(clean_candidate(meta.get("content", "")))
            if soup.title:
                weak.append(clean_candidate(soup.title.get_text(" ", strip=True)))
            for node in soup.select("h1")[:3]:
                weak.append(clean_candidate(node.get_text(" ", strip=True)))
        for row in soup.select("tr"):
            text = row.get_text(" ", strip=True)
            if re.search(r"(会社名|商号|法人名|運営会社)", text):
                strong.append(clean_candidate(text))
        for node in soup.select("footer"):
            for raw in node.stripped_strings:
                if LEGAL.search(raw) and len(raw) <= 70:
                    strong.append(clean_candidate(raw))
        for raw in soup.stripped_strings:
            if re.match(r"^(会社名|商号|法人名|運営会社)\s*[:：]", raw) and LEGAL.search(raw):
                strong.append(clean_candidate(raw))
    strong = [c for c in strong if c]
    if strong:
        return min(strong, key=len)
    weak = [c for c in weak if c]
    if weak:
        return min(weak, key=len)
    if has_maps and fallback and not re.search(r"(市役所|県庁|協議会|編集部|事務局|公式サイト|一覧|記事|サービス$|会社概要$|企業情報$|会社情報$)", fallback):
        return fallback.strip()
    return ""


def verify(row, partner=False):
    url = row.get("url", "").strip()
    domain = host(url)
    if not domain or any(bit in domain or bit in url.lower() for bit in BLOCKED):
        return None, "blocked_domain"
    first = fetch(url)
    if not first:
        return None, "fetch_failed"
    root = f"{urlparse(first.url).scheme}://{urlparse(first.url).netloc}/"
    responses = [first]
    if first.url.rstrip("/") != root.rstrip("/"):
        home = fetch(root)
        if home:
            responses = [home, first]
    soup0 = BeautifulSoup(first.text, "html.parser")
    profile_urls = []
    for anchor in soup0.select("a[href]"):
        label = anchor.get_text(" ", strip=True)
        href = anchor.get("href", "")
        target = urljoin(first.url, href).split("#")[0]
        if host(target) == host(first.url) and PROFILE.search(f"{label} {href}") and target not in profile_urls:
            profile_urls.append(target)
    for target in profile_urls[:2]:
        response = fetch(target)
        if response:
            responses.append(response)
    soups = [BeautifulSoup(r.text, "html.parser") for r in responses]
    text = " ".join(s.get_text(" ", strip=True) for s in soups)
    relevant = SERVICE.search(text) or (PLATFORM.search(text) and ACTION.search(text))
    if partner:
        relevant = relevant or PARTNER_SERVICE.search(text)
    if not relevant or not OFFER.search(text):
        return None, "no_service_offer"
    name = official_name(soups, row.get("company_name", ""), bool(row.get("maps_url")))
    if not name:
        return None, "no_official_name"
    result = dict(row)
    result["company_name"] = name
    result["url"] = root.rstrip("/")
    return result, "kept"


input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/sns_verified_pure_new.csv")
output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/sns_official_strict.csv")
audit_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("data/sns_official_strict_audit.csv")
partner_mode = len(sys.argv) > 4 and sys.argv[4] == "partner"
with input_path.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
kept, audit = [], []
with ThreadPoolExecutor(max_workers=12) as executor:
    futures = {executor.submit(verify, row, partner_mode): row for row in rows}
    for index, future in enumerate(as_completed(futures), 1):
        row = futures[future]
        try:
            item, reason = future.result()
        except Exception as exc:
            item, reason = None, f"error:{type(exc).__name__}"
        audit.append({"company_name": row.get("company_name", ""), "url": row.get("url", ""), "result": reason})
        if item:
            kept.append(item)
        if index % 50 == 0:
            print(f"checked={index}/{len(rows)} kept={len(kept)}", flush=True)
fields = list(rows[0].keys())
with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(kept)
with audit_path.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "result"])
    writer.writeheader(); writer.writerows(audit)
print(f"verified={len(kept)} total={len(rows)}")
