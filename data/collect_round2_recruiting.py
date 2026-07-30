import csv
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


PREFECTURES = [
    "北海道", "青森", "岩手", "宮城", "秋田", "山形", "福島", "茨城", "栃木",
    "群馬", "埼玉", "千葉", "東京", "神奈川", "新潟", "富山", "石川", "福井",
    "山梨", "長野", "岐阜", "静岡", "愛知", "三重", "滋賀", "京都", "大阪",
    "兵庫", "奈良", "和歌山", "鳥取", "島根", "岡山", "広島", "山口", "徳島",
    "香川", "愛媛", "高知", "福岡", "佐賀", "長崎", "熊本", "大分", "宮崎",
    "鹿児島", "沖縄",
]

ROLES = ["Webマーケター", "広告運用", "SNS運用"]
JOB_TERMS = ["募集要項", "中途採用", "キャリア採用", "正社員", "応募資格", "仕事内容"]
ROLE_TERMS = [
    "webマーケター", "デジタルマーケティング", "広告運用", "リスティング広告",
    "sns運用", "snsマーケティング", "マーケティング担当",
]
SERVICE_TERMS = [
    "webマーケティング支援", "デジタルマーケティング支援", "web広告運用",
    "広告運用代行", "リスティング広告運用", "sns運用代行", "snsマーケティング支援",
    "seoコンサルティング", "コンテンツマーケティング支援", "販売促進支援",
    "販促支援", "店舗集客支援", "集客支援", "マーケティング支援",
    "インターネット広告代理", "広告代理業",
]
CLIENT_TERMS = [
    "お客様", "クライアント", "支援実績", "導入実績", "法人向け", "企業向け",
    "ご支援", "広告主", "取引先", "顧客",
]
BLOCKED = {
    "indeed.com", "jp.indeed.com", "wantedly.com", "doda.jp", "mynavi.jp",
    "tenshoku.mynavi.jp", "en-gage.net", "求人ボックス.com", "job-medley.com",
    "green-japan.com", "openwork.jp", "careerindex.jp", "itnavi.jp", "type.jp",
    "rikunabi.com", "hrmos.co", "herp.careers", "jobcan.jp", "sonar-ats.jp",
    "prtimes.jp", "note.com", "facebook.com", "instagram.com", "x.com",
    "twitter.com", "youtube.com", "google.com", "web-kanji.com", "imitsu.jp",
}
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
    )
}


def host_of(url):
    host = urlparse(url).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def is_blocked(url):
    host = host_of(url)
    return not host or any(host == item or host.endswith("." + item) for item in BLOCKED)


def compact(value):
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_name(value):
    value = compact(value).lower()
    value = re.sub(r"(株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\(株\)|（株）)", "", value)
    return re.sub(r"[\s　・･.,，。\-ー_／/|｜()（）]", "", value)


def normalize_phone(value):
    return re.sub(r"\D", "", value or "")


def load_exclusions():
    with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8-sig") as handle:
        rows = json.load(handle)
    names, hosts, phones = set(), set(), set()
    for row in rows:
        if row.get("company_name"):
            names.add(normalize_name(row["company_name"]))
        if row.get("url") and host_of(row["url"]):
            hosts.add(host_of(row["url"]))
        if row.get("phone") and normalize_phone(row["phone"]):
            phones.add(normalize_phone(row["phone"]))
    return names, hosts, phones


def search(query):
    url = "https://www.bing.com/search?format=rss&q=" + quote_plus(query)
    response = requests.get(url, headers=UA, timeout=15)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    urls = []
    for item in root.findall(".//item"):
        node = item.find("link")
        target = node.text.strip() if node is not None and node.text else ""
        if target.startswith("http") and not is_blocked(target):
            urls.append(target)
    return urls


def fetch(url):
    try:
        response = requests.get(url, headers=UA, timeout=15, allow_redirects=True)
        if response.status_code >= 400 or "text/html" not in response.headers.get("content-type", ""):
            return None
        return response.url, response.text
    except requests.RequestException:
        return None


def soup_text(markup):
    soup = BeautifulSoup(markup, "html.parser")
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()
    return soup, compact(soup.get_text(" ", strip=True))


def root_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def get_company_pages(base, soup):
    pages = [base]
    labels = ["会社概要", "企業情報", "会社情報", "about", "company", "corporate", "profile"]
    for link in soup.select("a[href]"):
        label = compact(link.get_text(" ", strip=True)).lower()
        href = link.get("href", "")
        if any(term in label for term in labels):
            pages.append(urljoin(base, href))
    for path in ["company/", "about/", "corporate/", "profile/", "about/company/"]:
        pages.append(urljoin(root_url(base), path))
    unique = []
    seen = set()
    for page in pages:
        if host_of(page) == host_of(base) and page not in seen:
            seen.add(page)
            unique.append(page)
    return unique[:8]


def company_name(soups, all_text):
    for soup in soups:
        for node in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(node.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in {"Organization", "Corporation", "LocalBusiness"}:
                    name = compact(str(item.get("name", "")))
                    if name:
                        return name
    pattern = re.compile(
        r"((?:株式会社|有限会社|合同会社|一般社団法人|一般財団法人)"
        r"[A-Za-z0-9\u3040-\u30ff\u3400-\u9fff・･＆&\-ー ]{1,45})"
    )
    match = pattern.search(all_text)
    return compact(match.group(1)) if match else ""


def address_of(text):
    patterns = [
        r"(〒\s*\d{3}[-ー−]?\d{4}\s*)?(?:北海道|東京都|京都府|大阪府|.{2,3}県)"
        r"[^\s]{1,12}[市区町村郡][^。|｜]{1,80}",
        r"(?:北海道|東京都|京都府|大阪府|.{2,3}県)[^。|｜]{5,100}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = compact(match.group(0))
            value = re.split(r"(?:TEL|電話|FAX|アクセス|Google|代表者|設立)", value, flags=re.I)[0]
            if 8 <= len(value) <= 120 and re.search(r"\d", value):
                return value
    return ""


def phone_of(text):
    for value in re.findall(r"(?<!\d)0\d{1,4}[-ー− ]\d{1,4}[-ー− ]\d{3,4}(?!\d)", text):
        digits = normalize_phone(value)
        if 10 <= len(digits) <= 11:
            return re.sub(r"[ー− ]", "-", value)
    return ""


def verify_recruit(url, excluded_names, excluded_hosts, excluded_phones):
    recruitment = fetch(url)
    if not recruitment or is_blocked(recruitment[0]):
        return None
    final_job_url, job_markup = recruitment
    job_soup, job_text = soup_text(job_markup)
    lower_job = job_text.lower()
    if not any(term in lower_job for term in ROLE_TERMS):
        return None
    if sum(term.lower() in lower_job for term in JOB_TERMS) < 2:
        return None
    domain = host_of(final_job_url)
    if domain in excluded_hosts:
        return None

    base = root_url(final_job_url)
    home = fetch(base)
    if not home:
        return None
    home_soup, home_text = soup_text(home[1])
    soups = [home_soup]
    texts = [home_text]
    for page in get_company_pages(home[0], home_soup)[1:]:
        result = fetch(page)
        if not result:
            continue
        page_soup, page_text = soup_text(result[1])
        soups.append(page_soup)
        texts.append(page_text)
    all_text = " ".join(texts)
    lower = all_text.lower()
    service_score = sum(term in lower for term in SERVICE_TERMS)
    client_score = sum(term.lower() in lower for term in CLIENT_TERMS)
    if service_score < 1 or client_score < 1:
        return None
    if "meo" in lower and service_score == 1 and not any(
        term in lower for term in ["web広告", "sns運用", "seo", "販促"]
    ):
        return None
    name = company_name(soups, all_text)
    address = address_of(all_text)
    phone = phone_of(all_text)
    if not name or not address:
        return None
    if normalize_name(name) in excluded_names:
        return None
    if phone and normalize_phone(phone) in excluded_phones:
        return None
    return {
        "company_name": name,
        "url": base.rstrip("/"),
        "address": address,
        "phone": phone,
        "maps_url": "",
        "_job_url": final_job_url,
        "_service_score": service_score,
    }


def main():
    excluded_names, excluded_hosts, excluded_phones = load_exclusions()
    queries = []
    for pref in PREFECTURES:
        for role in ROLES:
            queries.append(f'"{role}" "{pref}" "募集要項" 採用 -indeed -wantedly -doda -mynavi')
            queries.append(f'"{role}" "{pref}" "中途採用" 会社 -求人サイト')

    found = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(search, query) for query in queries]
        for future in as_completed(futures):
            try:
                found.extend(future.result())
            except (requests.RequestException, ET.ParseError):
                pass

    domain_urls = {}
    for url in found:
        domain = host_of(url)
        if domain and domain not in excluded_hosts:
            domain_urls.setdefault(domain, url)

    verified = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [
            pool.submit(
                verify_recruit, url, excluded_names, excluded_hosts, excluded_phones
            )
            for url in domain_urls.values()
        ]
        for future in as_completed(futures):
            try:
                record = future.result()
            except Exception:
                record = None
            if record:
                verified.append(record)

    unique = {}
    for record in verified:
        domain = host_of(record["url"])
        current = unique.get(domain)
        if not current or record["_service_score"] > current["_service_score"]:
            unique[domain] = record

    rows = sorted(unique.values(), key=lambda row: row["company_name"])
    with open("data/agent_round2_recruiting_marketing_raw.csv", "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "company_name", "url", "address", "phone", "maps_url",
                "_job_url", "_service_score",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"queries={len(queries)} results={len(found)} "
        f"candidate_domains={len(domain_urls)} verified_new={len(rows)}"
    )


if __name__ == "__main__":
    main()
