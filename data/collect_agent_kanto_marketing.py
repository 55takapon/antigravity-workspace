import csv
import html
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PREFECTURES = {
    "神奈川県": [
        "横浜市", "川崎市", "相模原市", "藤沢市", "横須賀市", "平塚市",
        "茅ヶ崎市", "厚木市", "大和市", "海老名市", "鎌倉市", "小田原市",
    ],
    "埼玉県": [
        "さいたま市", "川口市", "川越市", "所沢市", "越谷市", "草加市",
        "春日部市", "上尾市", "熊谷市", "戸田市", "朝霞市", "和光市",
    ],
    "千葉県": [
        "千葉市", "船橋市", "松戸市", "市川市", "柏市", "浦安市",
        "流山市", "木更津市", "市原市", "習志野市", "成田市", "八千代市",
    ],
    "茨城県": [
        "水戸市", "つくば市", "土浦市", "ひたちなか市", "日立市",
        "取手市", "守谷市", "古河市",
    ],
    "栃木県": ["宇都宮市", "小山市", "栃木市", "足利市", "佐野市", "那須塩原市"],
    "群馬県": ["高崎市", "前橋市", "太田市", "伊勢崎市", "桐生市", "館林市"],
    "新潟県": ["新潟市", "長岡市", "上越市", "三条市", "燕市", "新発田市"],
    "長野県": ["長野市", "松本市", "上田市", "佐久市", "飯田市", "諏訪市", "伊那市"],
    "山梨県": ["甲府市", "甲斐市", "笛吹市", "富士吉田市", "南アルプス市"],
}

SERVICES = [
    "Webマーケティング", "デジタルマーケティング", "Web広告代理店",
    "リスティング広告 運用", "SNS運用代行", "Instagram運用代行",
    "広告運用代行", "SEO対策会社", "販促支援会社", "店舗集客支援",
    "ECマーケティング", "Webコンサルティング",
]

SERVICE_TERMS = [
    "webマーケティング", "デジタルマーケティング", "web広告", "広告運用",
    "リスティング広告", "sns運用", "snsマーケティング", "instagram運用",
    "seo対策", "コンテンツマーケティング", "販売促進", "販促支援",
    "店舗集客", "集客支援", "ecマーケティング", "インターネット広告",
    "webコンサルティング", "マーケティング支援",
]

BLOCKED_HOSTS = {
    "web-kanji.com", "imitsu.jp", "liskul.com", "ferret-plus.com",
    "wantedly.com", "indeed.com", "jp.indeed.com", "doda.jp", "en-gage.net",
    "mynavi.jp", "townwork.net", "biz.ne.jp", "prtimes.jp", "note.com",
    "facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com",
    "google.com", "maps.google.com", "map.yahoo.co.jp", "wikipedia.org",
    "houjin.jp", "baseconnect.in", "b-mall.ne.jp",
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


def search_google(query):
    response = requests.get(
        "https://www.google.com/search?q=" + quote_plus(query) + "&num=20&hl=ja",
        headers=UA,
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    found = []
    for heading in soup.select("a h3"):
        link = heading.find_parent("a")
        if not link:
            continue
        target = link.get("href", "")
        if target.startswith("/url?"):
            target = parse_qs(urlparse(target).query).get("q", [target])[0]
        if target.startswith("http") and not is_blocked(target):
            found.append(target)
    return found


def clean_text(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def fetch(url):
    try:
        response = requests.get(url, headers=UA, timeout=20, allow_redirects=True)
        if response.status_code >= 400 or "text/html" not in response.headers.get("content-type", ""):
            return None
        return response.url, response.text
    except requests.RequestException:
        return None


def page_text(markup):
    soup = BeautifulSoup(markup, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    return soup, clean_text(soup.get_text(" ", strip=True))


def likely_company_name(soup, text):
    corp = re.compile(
        r"(?:株式会社|有限会社|合同会社|一般社団法人|一般財団法人)"
        r"[A-Za-zＡ-Ｚａ-ｚ0-9０-９ぁ-んァ-ヶ一-龠・&＆.\- ]{1,45}"
    )
    match = corp.search(text)
    if match:
        return clean_text(match.group(0))
    for selector in ['meta[property="og:site_name"]', "title", "h1"]:
        node = soup.select_one(selector)
        if not node:
            continue
        value = node.get("content") if node.name == "meta" else node.get_text(" ", strip=True)
        value = re.split(r"[|｜–—／/]", clean_text(value))[0].strip()
        if 2 <= len(value) <= 60:
            return value
    return ""


def find_prefecture(text):
    return next((pref for pref in PREFECTURES if pref in text), "")


def find_address(text, pref):
    if not pref:
        return ""
    for pattern in [
        rf"(?:〒\s*\d{{3}}[-ー−]?\d{{4}}\s*)?{pref}.{{2,100}}?(?=(?:TEL|電話|Phone|代表|お問い合わせ|$))",
        rf"{pref}[^\n。|｜]{{3,110}}",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            address = clean_text(match.group(0))
            address = re.split(r"(?:TEL|電話|Phone|代表|お問い合わせ)", address, flags=re.I)[0]
            if len(address) <= 130:
                return address
    return ""


def find_phone(text):
    for value in re.findall(r"(?<!\d)(?:0\d{1,4}[-ー− ]\d{1,4}[-ー− ]\d{3,4})(?!\d)", text):
        phone = re.sub(r"[ー− ]", "-", value)
        if 10 <= len(re.sub(r"\D", "", phone)) <= 11:
            return phone
    return ""


def verify(url):
    first = fetch(root_url(url))
    if not first or is_blocked(first[0]):
        return None
    final_url, markup = first
    soup, text = page_text(markup)
    lower = text.lower()
    service_score = sum(term in lower for term in SERVICE_TERMS)
    if service_score < 1:
        return None

    combined_text = text
    pref = find_prefecture(combined_text)
    address = find_address(combined_text, pref)
    company_pages = []
    for link in soup.select("a[href]"):
        label = clean_text(link.get_text(" ", strip=True)).lower()
        href = link.get("href", "")
        if any(term in label for term in ["会社概要", "会社情報", "企業情報", "about", "company"]):
            company_pages.append(urljoin(final_url, href))
    for company_url in company_pages[:4]:
        if address and re.search(r"(株式会社|有限会社|合同会社)", combined_text):
            break
        extra = fetch(company_url)
        if not extra or registrable_host(extra[0]) != registrable_host(final_url):
            continue
        _, extra_text = page_text(extra[1])
        combined_text += " " + extra_text
        pref = find_prefecture(combined_text)
        address = find_address(combined_text, pref)

    if not pref or not address:
        return None
    name = likely_company_name(soup, combined_text)
    if not name:
        return None

    non_meo_terms = [term for term in SERVICE_TERMS if term not in {"店舗集客", "集客支援"}]
    if "meo" in lower and not any(term in lower for term in non_meo_terms):
        return None

    canonical = soup.select_one('link[rel="canonical"]')
    official = canonical.get("href") if canonical and canonical.get("href") else root_url(final_url)
    official = root_url(urljoin(final_url, official))
    return {
        "company_name": name,
        "url": official,
        "address": address,
        "phone": find_phone(combined_text),
        "maps_url": "",
        "_prefecture": pref,
        "_service_score": service_score,
    }


def main():
    queries = [
        f'"{city}" "{service}" 会社 公式'
        for cities in PREFECTURES.values()
        for city in cities
        for service in SERVICES
    ]
    discovered = []
    with ThreadPoolExecutor(max_workers=2) as search_pool:
        search_futures = [search_pool.submit(search_google, query) for query in queries]
        for index, future in enumerate(as_completed(search_futures), 1):
            try:
                discovered.extend(future.result())
            except requests.RequestException:
                pass
            if index % 30 == 0:
                print(f"searched={index}/{len(queries)} discovered={len(discovered)}", flush=True)

    unique_urls = {}
    for url in discovered:
        host = registrable_host(url)
        if host and host not in unique_urls:
            unique_urls[host] = url

    records = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(verify, url) for url in unique_urls.values()]
        for index, future in enumerate(as_completed(futures), 1):
            try:
                record = future.result()
            except Exception:
                record = None
            if record:
                records.append(record)
            if index % 100 == 0:
                print(f"verified_domains={index}/{len(futures)} kept={len(records)}", flush=True)

    deduped = {}
    for record in records:
        host = registrable_host(record["url"])
        current = deduped.get(host)
        if not current or record["_service_score"] > current["_service_score"]:
            deduped[host] = record

    rows = sorted(deduped.values(), key=lambda x: (x["_prefecture"], x["company_name"]))
    with open("data/agent_kanto_marketing_raw.csv", "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "company_name", "url", "address", "phone", "maps_url",
                "_prefecture", "_service_score",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"queries={len(queries)} discovered={len(discovered)} "
        f"domains={len(unique_urls)} verified={len(rows)}"
    )


if __name__ == "__main__":
    main()
