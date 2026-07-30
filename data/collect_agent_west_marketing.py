import csv
import html
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PREFECTURES = {
    "兵庫県": ["神戸市", "姫路市", "西宮市", "尼崎市", "明石市", "加古川市"],
    "京都府": ["京都市", "宇治市", "長岡京市", "亀岡市"],
    "滋賀県": ["大津市", "草津市", "彦根市", "近江八幡市"],
    "奈良県": ["奈良市", "橿原市", "生駒市", "大和郡山市"],
    "和歌山県": ["和歌山市", "田辺市", "岩出市"],
    "静岡県": ["静岡市", "浜松市", "沼津市", "富士市", "三島市"],
    "岐阜県": ["岐阜市", "大垣市", "各務原市", "多治見市"],
    "三重県": ["津市", "四日市市", "鈴鹿市", "桑名市"],
    "福岡県": ["福岡市", "北九州市", "久留米市", "飯塚市"],
    "熊本県": ["熊本市", "八代市", "菊池市"],
    "鹿児島県": ["鹿児島市", "霧島市", "薩摩川内市"],
    "沖縄県": ["那覇市", "浦添市", "宜野湾市", "沖縄市", "うるま市"],
}

SERVICES = [
    "Webマーケティング",
    "Web広告代理店",
    "SNS運用代行",
    "広告運用代行",
    "SEO対策会社",
    "販促支援会社",
    "店舗集客支援",
    "ECマーケティング",
]

SERVICE_TERMS = [
    "webマーケティング", "デジタルマーケティング", "web広告", "広告運用",
    "リスティング広告", "sns運用", "snsマーケティング", "seo対策",
    "コンテンツマーケティング", "販売促進", "販促支援", "店舗集客",
    "集客支援", "ecマーケティング", "インターネット広告",
]

BLOCKED_HOSTS = {
    "web-kanji.com", "imitsu.jp", "liskul.com", "ferret-plus.com",
    "wantedly.com", "indeed.com", "jp.indeed.com", "doda.jp", "en-gage.net",
    "mynavi.jp", "townwork.net", "biz.ne.jp", "prtimes.jp", "note.com",
    "facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com",
    "google.com", "maps.google.com", "map.yahoo.co.jp", "wikipedia.org",
}

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
    )
}


def root_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme or 'https'}://{parsed.netloc}/"


def registrable_host(url):
    host = urlparse(url).netloc.lower().split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def is_blocked(url):
    host = registrable_host(url)
    return not host or any(host == item or host.endswith("." + item) for item in BLOCKED_HOSTS)


def search_web(query):
    url = "https://www.bing.com/search?format=rss&q=" + quote_plus(query)
    response = requests.get(url, headers=UA, timeout=20)
    response.raise_for_status()
    found = []
    root = ET.fromstring(response.content)
    for item in root.findall(".//item"):
        node = item.find("link")
        target = node.text.strip() if node is not None and node.text else ""
        if target.startswith("http") and not is_blocked(target):
            found.append(target)
    return found


def clean_text(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def fetch(url):
    try:
        response = requests.get(url, headers=UA, timeout=20, allow_redirects=True)
        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400 or "text/html" not in content_type:
            return None
        return response.url, response.text
    except requests.RequestException:
        return None


def likely_company_name(soup):
    candidates = []
    for selector in [
        'meta[property="og:site_name"]', 'meta[name="application-name"]',
        "title", "h1",
    ]:
        node = soup.select_one(selector)
        if not node:
            continue
        value = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
        value = clean_text(value)
        if value:
            candidates.append(value)
    corp = re.compile(r"(株式会社|有限会社|合同会社|一般社団法人|一般財団法人)[^|｜/]{1,45}")
    for value in candidates:
        match = corp.search(value)
        if match:
            return clean_text(match.group(0))
    for value in candidates:
        value = re.split(r"[|｜–—\-／/]", value)[0].strip()
        if 2 <= len(value) <= 60:
            return value
    return ""


def find_prefecture(text):
    for pref in PREFECTURES:
        if pref in text:
            return pref
    return ""


def find_address(text, pref):
    if not pref:
        return ""
    patterns = [
        rf"(〒\s*\d{{3}}[-ー−]?\d{{4}}\s*)?{pref}.{{2,90}}?(?=(?:TEL|電話|Phone|代表|お問い合わせ|$))",
        rf"{pref}[^\n。|｜]{{3,100}}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            address = clean_text(match.group(0))
            address = re.split(r"(?:TEL|電話|Phone|代表|お問い合わせ)", address, flags=re.I)[0]
            if len(address) <= 120:
                return address
    return ""


def find_phone(text):
    matches = re.findall(r"(?<!\d)(?:0\d{1,4}[-ー− ]\d{1,4}[-ー− ]\d{3,4})(?!\d)", text)
    for value in matches:
        phone = re.sub(r"[ー− ]", "-", value)
        if 10 <= len(re.sub(r"\D", "", phone)) <= 11:
            return phone
    return ""


def verify(url):
    first = fetch(root_url(url))
    if not first:
        return None
    final_url, markup = first
    if is_blocked(final_url):
        return None
    soup = BeautifulSoup(markup, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    text = clean_text(soup.get_text(" ", strip=True))
    lower = text.lower()
    score = sum(term in lower for term in SERVICE_TERMS)
    if score < 1:
        return None
    pref = find_prefecture(text)
    if not pref:
        return None
    address = find_address(text, pref)
    if not address:
        company_links = []
        for link in soup.select("a[href]"):
            label = clean_text(link.get_text(" ", strip=True)).lower()
            href = link.get("href", "")
            if any(term in label for term in ["会社", "企業", "about", "company", "概要"]):
                company_links.append(urljoin(final_url, href))
        for company_url in company_links[:3]:
            extra = fetch(company_url)
            if not extra:
                continue
            extra_soup = BeautifulSoup(extra[1], "html.parser")
            for node in extra_soup(["script", "style", "noscript", "svg"]):
                node.decompose()
            extra_text = clean_text(extra_soup.get_text(" ", strip=True))
            pref = find_prefecture(extra_text) or pref
            address = find_address(extra_text, pref)
            if address:
                text += " " + extra_text
                break
    if not address:
        return None
    name = likely_company_name(soup)
    if not name:
        return None
    # MEO-only sites are excluded; sites with another confirmed service remain.
    non_meo_score = sum(term in lower for term in SERVICE_TERMS if "店舗集客" not in term)
    if "meo" in lower and non_meo_score == 0:
        return None
    canonical = soup.select_one('link[rel="canonical"]')
    official = canonical.get("href") if canonical and canonical.get("href") else root_url(final_url)
    official = root_url(urljoin(final_url, official))
    return {
        "company_name": name,
        "url": official,
        "address": address,
        "phone": find_phone(text),
        "maps_url": "",
        "_prefecture": pref,
        "_service_score": score,
    }


def main():
    queries = []
    for pref, cities in PREFECTURES.items():
        for city in cities:
            for service in SERVICES:
                queries.append(f'"{city}" "{service}" 会社 公式')

    discovered = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(search_web, query) for query in queries]
        for future in as_completed(futures):
            try:
                discovered.extend(future.result())
            except requests.RequestException:
                pass

    unique_urls = {}
    for url in discovered:
        host = registrable_host(url)
        if host and host not in unique_urls:
            unique_urls[host] = url

    records = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(verify, url): host for host, url in unique_urls.items()}
        for future in as_completed(futures):
            record = future.result()
            if record:
                records.append(record)

    deduped = {}
    for record in records:
        host = registrable_host(record["url"])
        current = deduped.get(host)
        if not current or record["_service_score"] > current["_service_score"]:
            deduped[host] = record

    rows = sorted(deduped.values(), key=lambda x: (x["_prefecture"], x["company_name"]))
    with open("data/agent_west_marketing_raw.csv", "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "company_name", "url", "address", "phone", "maps_url",
                "_prefecture", "_service_score",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"queries={len(queries)} discovered={len(discovered)} domains={len(unique_urls)} verified={len(rows)}")


if __name__ == "__main__":
    main()
