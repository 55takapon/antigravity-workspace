import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
    )
}
ROLE_TERMS = [
    "webマーケター", "デジタルマーケティング", "広告運用", "web広告",
    "sns運用", "snsマーケティング", "seoコンサルタント",
    "マーケティングディレクター", "マーケティングコンサルタント",
]
ACTIVE_TERMS = [
    "募集要項", "中途採用", "キャリア採用", "正社員", "契約社員",
    "応募資格", "仕事内容", "募集職種", "採用情報", "募集中",
]
SERVICE_TERMS = [
    "webマーケティング", "デジタルマーケティング", "web広告",
    "広告運用", "リスティング広告", "sns運用", "snsマーケティング",
    "seo対策", "seoコンサルティング", "販促支援", "販売促進",
    "集客支援", "広告代理", "プロモーション支援",
]
CLIENT_TERMS = ["クライアント", "お客様", "顧客", "企業向け", "法人向け", "支援実績", "導入実績"]


def compact(value):
    return re.sub(r"\s+", " ", value or "").strip()


def host_of(url):
    host = urlparse(url).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def normalize_name(value):
    value = compact(value).lower()
    value = re.sub(r"(株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\(株\)|（株）)", "", value)
    return re.sub(r"[\s　・･.,，。\-ー_／/|｜()（）]", "", value)


def normalize_phone(value):
    return re.sub(r"\D", "", value or "")


def fetch(url):
    try:
        response = requests.get(url, headers=UA, timeout=10, allow_redirects=True)
        if response.status_code >= 400:
            return None
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        return response.url, soup, compact(soup.get_text(" ", strip=True))
    except requests.RequestException:
        return None


def company_pages(base):
    paths = [
        "", "company/", "about/", "company/about/", "corporate/", "profile/",
        "about/company/", "company/profile/", "outline/", "access/",
    ]
    return [urljoin(base.rstrip("/") + "/", path) for path in paths]


def address_of(text):
    patterns = [
        r"(〒\s*\d{3}[-ー−]?\d{4}\s*)?(?:北海道|東京都|京都府|大阪府|"
        r"青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|"
        r"埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|"
        r"岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|鳥取県|"
        r"島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|"
        r"佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)"
        r".{2,100}?(?=(?:TEL|電話|FAX|Google|アクセス|代表者|設立|資本金|$))",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            value = compact(match.group(0))
            value = re.split(r"(?:TEL|電話|FAX|Google|アクセス|代表者|設立|資本金)", value, flags=re.I)[0]
            if 10 <= len(value) <= 120 and re.search(r"\d", value):
                return value
    return ""


def phone_of(text):
    for value in re.findall(r"(?<!\d)0\d{1,4}[-ー− ]\d{1,4}[-ー− ]\d{3,4}(?!\d)", text):
        digits = normalize_phone(value)
        if 10 <= len(digits) <= 11:
            return re.sub(r"[ー− ]", "-", value)
    return ""


def load_exclusions():
    with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8-sig") as handle:
        rows = json.load(handle)
    names, hosts, phones = set(), set(), set()
    for row in rows:
        if row.get("company_name"):
            names.add(normalize_name(row["company_name"]))
        if row.get("url"):
            hosts.add(host_of(row["url"]))
        if row.get("phone"):
            phones.add(normalize_phone(row["phone"]))
    return names, hosts, phones


def verify(seed, excluded_names, excluded_hosts, excluded_phones):
    if normalize_name(seed["company_name"]) in excluded_names or host_of(seed["url"]) in excluded_hosts:
        return {"_drop": "existing", "_seed": seed["company_name"]}
    job = fetch(seed["job_url"])
    if not job:
        return {"_drop": "job_fetch", "_seed": seed["company_name"]}
    job_lower = job[2].lower()
    if not any(term in job_lower for term in ROLE_TERMS):
        return {"_drop": "role", "_seed": seed["company_name"]}
    if sum(term in job_lower for term in ACTIVE_TERMS) < 2:
        return {"_drop": "active", "_seed": seed["company_name"]}

    texts = []
    for page in company_pages(seed["url"]):
        result = fetch(page)
        if result:
            texts.append(result[2])
        if len(texts) >= 4:
            break
    all_text = " ".join(texts)
    lower = all_text.lower()
    if not any(term in lower for term in SERVICE_TERMS):
        return {"_drop": "service", "_seed": seed["company_name"]}
    if not any(term.lower() in lower for term in CLIENT_TERMS):
        return {"_drop": "client", "_seed": seed["company_name"]}
    address = address_of(all_text)
    if not address:
        return {"_drop": "address", "_seed": seed["company_name"]}
    phone = phone_of(all_text)
    if phone and normalize_phone(phone) in excluded_phones:
        return {"_drop": "phone_existing", "_seed": seed["company_name"]}
    return {
        "company_name": seed["company_name"],
        "url": seed["url"].rstrip("/"),
        "address": address,
        "phone": phone,
        "maps_url": "",
        "_job_url": seed["job_url"],
    }


def main():
    with open("data/round2_recruiting_seeds.csv", encoding="utf-8-sig") as handle:
        seeds = list(csv.DictReader(handle))
    excluded_names, excluded_hosts, excluded_phones = load_exclusions()
    records = []
    dropped = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [
            pool.submit(verify, seed, excluded_names, excluded_hosts, excluded_phones)
            for seed in seeds
        ]
        for future in as_completed(futures):
            record = future.result()
            if record and record.get("_drop"):
                dropped.append(record)
            elif record:
                records.append(record)
    unique = {host_of(row["url"]): row for row in records}
    rows = sorted(unique.values(), key=lambda row: row["company_name"])
    with open("data/agent_round2_recruiting_verified.csv", "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["company_name", "url", "address", "phone", "maps_url", "_job_url"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"seeds={len(seeds)} verified_new={len(rows)}")
    for row in sorted(dropped, key=lambda item: (item["_drop"], item["_seed"])):
        print(f"drop={row['_drop']} name={row['_seed']}")


if __name__ == "__main__":
    main()
