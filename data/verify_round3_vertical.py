import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
SERVICE_TERMS = [
    "webマーケティング", "デジタルマーケティング", "web広告", "広告運用",
    "sns運用", "snsマーケティング", "seo対策", "seoコンサルティング",
    "販促支援", "販売促進", "集客支援", "web集客", "広告代理",
]
VERTICAL_TERMS = [
    "医療", "歯科", "クリニック", "美容", "サロン", "飲食", "レストラン",
    "ホテル", "旅館", "宿泊", "観光", "不動産", "住宅", "工務店", "士業",
    "税理士", "弁護士", "学習塾", "教育", "スクール", "自動車", "中古車",
]
PREFS = (
    "北海道|東京都|京都府|大阪府|青森県|岩手県|宮城県|秋田県|山形県|福島県|"
    "茨城県|栃木県|群馬県|埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|"
    "山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|"
    "鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|"
    "佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県"
)


def compact(value):
    return re.sub(r"\s+", " ", value or "").strip()


def host_of(url):
    host = urlparse(url).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def norm_name(value):
    value = compact(value).lower()
    value = re.sub(r"(株式会社|有限会社|合同会社|一般社団法人|一般財団法人)", "", value)
    return re.sub(r"[\s　・･.,，。\-ー_／/|｜()（）]", "", value)


def norm_phone(value):
    return re.sub(r"\D", "", value or "")


def fetch(url):
    try:
        response = requests.get(url, headers=UA, timeout=10, allow_redirects=True)
        if response.status_code >= 400 or "text/html" not in response.headers.get("content-type", ""):
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        return compact(soup.get_text(" ", strip=True))
    except requests.RequestException:
        return ""


def address_of(text):
    pattern = rf"(〒\s*\d{{3}}[-ー−]?\d{{4}}\s*)?(?:{PREFS}).{{2,105}}?(?=(?:TEL|電話|FAX|代表|設立|資本金|事業内容|$))"
    for match in re.finditer(pattern, text, re.I):
        value = compact(match.group(0))
        value = re.split(r"(?:TEL|電話|FAX|代表|設立|資本金|事業内容)", value, flags=re.I)[0]
        if 9 <= len(value) <= 120 and re.search(r"\d", value):
            return value
    return ""


def phone_of(text):
    for value in re.findall(r"(?<!\d)0\d{1,4}[-ー− ]\d{1,4}[-ー− ]\d{3,4}(?!\d)", text):
        if 10 <= len(norm_phone(value)) <= 11:
            return re.sub(r"[ー− ]", "-", value)
    return ""


def exclusions():
    with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8-sig") as handle:
        rows = json.load(handle)
    names, domains, phones = set(), set(), set()
    for row in rows:
        if row.get("company_name"):
            names.add(norm_name(row["company_name"]))
        if row.get("url"):
            domains.add(host_of(row["url"]))
        if row.get("phone"):
            phones.add(norm_phone(row["phone"]))
    return names, domains, phones


def verify(seed, names, domains, phones):
    if norm_name(seed["company_name"]) in names or host_of(seed["url"]) in domains:
        return None
    pages = ["", "company/", "about/", "company-profile/", "corporate/", "profile/", "about/company/"]
    texts = []
    for path in pages:
        text = fetch(urljoin(seed["url"].rstrip("/") + "/", path))
        if text:
            texts.append(text)
        if len(texts) >= 4:
            break
    all_text = " ".join(texts)
    lower = all_text.lower()
    if not any(term in lower for term in SERVICE_TERMS):
        return None
    if not any(term in all_text for term in VERTICAL_TERMS):
        return None
    # MEO-only providers are excluded; another confirmed digital service must exist.
    non_meo = any(term in lower for term in ["webマーケティング", "web広告", "広告運用", "sns運用", "seo", "販促"])
    if "meo" in lower and not non_meo:
        return None
    address = address_of(all_text)
    if not address:
        return None
    phone = phone_of(all_text)
    if phone and norm_phone(phone) in phones:
        return None
    return {
        "company_name": seed["company_name"],
        "url": seed["url"].rstrip("/"),
        "address": address,
        "phone": phone,
        "maps_url": "",
    }


def main():
    with open("data/round3_vertical_seeds.csv", encoding="utf-8-sig") as handle:
        seeds = list(csv.DictReader(handle))
    names, domains, phones = exclusions()
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(verify, seed, names, domains, phones) for seed in seeds]
        for future in as_completed(futures):
            record = future.result()
            if record:
                rows.append(record)
    unique = {host_of(row["url"]): row for row in rows}
    rows = sorted(unique.values(), key=lambda row: row["company_name"])
    with open("data/agent_round3_vertical_verified.csv", "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "address", "phone", "maps_url"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"seeds={len(seeds)} verified_new={len(rows)}")


if __name__ == "__main__":
    main()
