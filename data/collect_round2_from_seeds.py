import csv
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
]
SERVICE_TERMS = [
    "web広告", "ウェブ広告", "sns広告", "sns運用", "広告運用",
    "リスティング広告", "デジタルマーケティング", "webマーケティング",
    "マーケティング支援", "販促支援", "販売促進", "プロモーション",
    "ec支援", "ec運営", "ecマーケティング", "ネットショップ運営",
    "集客支援", "広告代理店", "総合広告", "広告代理業",
]
COMPANY_HINTS = ["会社概要", "企業情報", "会社案内", "about", "company", "profile"]
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
    )
}


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def host(url):
    value = urlparse(url).netloc.lower().split(":")[0]
    return value[4:] if value.startswith("www.") else value


def root(url):
    parsed = urlparse(url)
    return f"{parsed.scheme or 'https'}://{parsed.netloc}/"


def fetch(url):
    try:
        response = requests.get(url, headers=UA, timeout=18, allow_redirects=True)
        if response.status_code >= 400 or "text/html" not in response.headers.get("content-type", ""):
            return None
        return response.url, response.text
    except requests.RequestException:
        return None


def parse_page(markup):
    soup = BeautifulSoup(markup, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    return soup, clean(soup.get_text(" ", strip=True))


def address_from(text):
    for pref in PREFECTURES:
        if pref not in text:
            continue
        patterns = [
            rf"(?:〒\s*\d{{3}}[-ー−]?\d{{4}}\s*)?{pref}[^\n。|｜]{{3,95}}",
            rf"{pref}.{{3,95}}?(?=(?:TEL|電話|FAX|Phone|代表|資本金|$))",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if not match:
                continue
            value = clean(match.group(0))
            value = re.split(r"(?:TEL|電話|FAX|Phone|代表|資本金)", value, flags=re.I)[0]
            if 5 <= len(value) <= 120:
                return value
    return ""


def phone_from(text):
    for value in re.findall(r"(?<!\d)0\d{1,4}[-ー− ]\d{1,4}[-ー− ]\d{3,4}(?!\d)", text):
        value = re.sub(r"[ー− ]", "-", value)
        if 10 <= len(re.sub(r"\D", "", value)) <= 11:
            return value
    return ""


def company_from(text, fallback):
    pattern = (
        r"(?:株式会社|有限会社|合同会社|一般社団法人|一般財団法人)"
        r"[A-Za-zＡ-Ｚａ-ｚ0-9０-９ぁ-んァ-ヶ一-龠・&＆.\- ]{1,45}"
    )
    match = re.search(pattern, text)
    if match:
        value = clean(match.group(0))
        value = re.split(r"(?:所在地|住所|代表|事業内容|設立|資本金)", value)[0].strip()
        if 3 <= len(value) <= 60:
            return value
    return fallback


def verify(seed):
    fetched = fetch(seed["url"])
    if not fetched:
        return None
    final_url, markup = fetched
    soup, top_text = parse_page(markup)
    combined = top_text
    service_text = top_text.lower()
    company_urls = []
    for link in soup.select("a[href]"):
        label = clean(link.get_text(" ", strip=True)).lower()
        href = link.get("href", "")
        if any(term in label for term in COMPANY_HINTS):
            target = urljoin(final_url, href)
            if host(target) == host(final_url):
                company_urls.append(target)
    for target in company_urls[:4]:
        extra = fetch(target)
        if not extra:
            continue
        _, extra_text = parse_page(extra[1])
        combined += " " + extra_text

    if not any(term in service_text for term in SERVICE_TERMS):
        service_text = combined.lower()
    if not any(term in service_text for term in SERVICE_TERMS):
        return None
    if "meo" in service_text and not any(
        term in service_text
        for term in ["web広告", "ウェブ広告", "sns広告", "sns運用", "ec支援", "ec運営", "販促", "広告代理"]
    ):
        return None

    address = address_from(combined)
    if not address:
        return None
    name = company_from(combined, seed["company_name"])
    if not name:
        return None
    return {
        "company_name": name,
        "url": root(final_url),
        "address": address,
        "phone": phone_from(combined),
        "maps_url": "",
    }


def norm_name(value):
    value = clean(value).lower()
    return re.sub(r"(株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\s|　|[・･.,，。])", "", value)


def norm_phone(value):
    return re.sub(r"\D", "", value or "")


def main():
    with open("data/agent_round2_seed_urls.csv", encoding="utf-8-sig") as handle:
        seeds = list(csv.DictReader(handle))
    with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8") as handle:
        existing = json.load(handle)

    existing_names = {norm_name(row.get("company_name", "")) for row in existing if row.get("company_name")}
    existing_hosts = {host(row.get("url", "")) for row in existing if row.get("url")}
    existing_phones = {norm_phone(row.get("phone", "")) for row in existing if norm_phone(row.get("phone", ""))}

    verified = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(verify, seed) for seed in seeds]
        for future in as_completed(futures):
            try:
                row = future.result()
            except Exception:
                row = None
            if row:
                verified.append(row)

    fresh = {}
    dropped_existing = 0
    for row in verified:
        row_host = host(row["url"])
        if (
            norm_name(row["company_name"]) in existing_names
            or row_host in existing_hosts
            or (norm_phone(row["phone"]) and norm_phone(row["phone"]) in existing_phones)
        ):
            dropped_existing += 1
            continue
        fresh.setdefault(row_host, row)

    rows = sorted(fresh.values(), key=lambda row: (row["address"], row["company_name"]))
    with open("data/agent_round2_prefiltered.csv", "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["company_name", "url", "address", "phone", "maps_url"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"seeds={len(seeds)} verified={len(verified)} "
        f"existing_drop={dropped_existing} fresh={len(rows)}"
    )


if __name__ == "__main__":
    main()
