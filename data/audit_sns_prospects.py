import argparse
import csv
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


LEGAL = re.compile(r"(?:株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|Inc\.?|Co\.?\s*,?\s*Ltd\.?|LLC)", re.I)
JP_LEGAL = re.compile(r"(?:株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人)")
BAD_NAME = re.compile(
    r"(?:著作権|帰属します|事務局|運営会社|HP運営会社|All Rights Reserved|Copyright|Official Web Site|"
    r"プライバシーポリシー|サイトマップ|お問い合わせ|会社概要はこちら|［公式］|オフィシャルサイト)",
    re.I,
)
BAD_HOST = re.compile(
    r"(?:baseconnect\.in|biz-maps\.com|wantedly\.com|prtimes\.jp|ipros\.com|canpan\.info|"
    r"town\.|city\.|pref\.|go\.jp|wikipedia\.org|note\.com)$",
    re.I,
)
NON_COMPANY = re.compile(r"(?:市役所|町役場|村役場|観光協会|商工会議所|大学|専門学校|高等学校|病院|クリニック|歯科医院)$")
NON_TARGET_NAME = re.compile(
    r"(?:工務店|建設|建築|不動産|住宅|ホテル|旅館|病院|クリニック|歯科|製薬|薬局|食品|フーズ|"
    r"製作所|工業|運輸|物流|保険|銀行|信用金庫|税理士|弁護士|司法書士|学校|学園|セメント)",
    re.I,
)
PROJECT_SITE = re.compile(r"(?:ポータルサイト|情報サイト|求人サイト|ニュースサイト|移住|観光情報|公式メディア|事務局|運営事務局)", re.I)
COMPETITOR = re.compile(r"(?:MEO対策|MEO運用代行|Googleマップ集客|Googleビジネスプロフィール運用|ローカルSEO専門)", re.I)

CATEGORIES = [
    (
        "SNS運用・SNS広告",
        ["SNS運用代行", "SNS運用", "SNSマーケティング", "Instagram運用", "インスタグラム運用", "TikTok運用", "X運用", "SNS広告", "ソーシャルメディア運用"],
    ),
    (
        "Web広告・デジタル集客",
        ["Webマーケティング", "ウェブマーケティング", "デジタルマーケティング", "Web広告", "インターネット広告", "リスティング広告", "Google広告", "Yahoo広告", "Meta広告", "広告運用", "SEO対策", "SEOコンサルティング"],
    ),
    (
        "Web制作・クリエイティブ",
        ["ホームページ制作", "Webサイト制作", "ウェブサイト制作", "Web制作", "ウェブ制作", "LP制作", "ランディングページ制作", "動画制作", "映像制作", "ブランディング", "クリエイティブ制作"],
    ),
    (
        "店舗・業種特化マーケティング",
        ["店舗集客", "集客支援", "販促支援", "販売促進", "マーケティング支援", "地域プロモーション", "採用マーケティング", "EC運営支援", "EC支援", "CRM支援", "LINE公式アカウント運用", "LINE運用支援", "インバウンド支援"],
    ),
]
OFFER = re.compile(r"(?:代行|支援|コンサル|受託|提供|サポート|ソリューション|制作会社|広告代理店|サービス)")
STRONG_SERVICE = {
    "SNS運用代行", "SNSマーケティング", "Instagram運用", "インスタグラム運用", "TikTok運用", "SNS広告",
    "Webマーケティング", "ウェブマーケティング", "デジタルマーケティング", "Web広告", "インターネット広告",
    "リスティング広告", "Google広告", "Yahoo広告", "Meta広告", "広告運用", "SEO対策", "SEOコンサルティング",
    "ホームページ制作", "Webサイト制作", "ウェブサイト制作", "Web制作", "ウェブ制作", "LP制作",
    "ランディングページ制作", "動画制作", "映像制作", "クリエイティブ制作", "店舗集客", "集客支援",
    "販促支援", "マーケティング支援", "地域プロモーション", "採用マーケティング", "EC運営支援", "EC支援",
    "CRM支援", "LINE公式アカウント運用", "LINE運用支援", "インバウンド支援",
}
PRIMARY_INDUSTRY = re.compile(
    r"(?:工務店|建設会社|建築会社|不動産会社|住宅会社|ホテル|旅館|病院|クリニック|歯科医院|"
    r"製造会社|製作所|工業株式会社|運送会社|物流会社|保険代理店|税理士法人|法律事務所|学校法人|学習塾)",
    re.I,
)
COMPANY_LABEL = re.compile(r"^\s*(?:会社概要|企業情報|会社案内|私たちについて|運営会社|corporate|company|about(?: us)?|profile)\s*$", re.I)
COMPANY_PATH = re.compile(r"/(?:company|corporate|about|profile|overview|outline)/?$", re.I)
SERVICE_LABEL = re.compile(r"^\s*(?:サービス|事業内容|事業紹介|提供サービス|service|business|solution)\s*$", re.I)
SERVICE_PATH = re.compile(r"/(?:service|services|business|solution|solutions)/?$", re.I)
local = threading.local()


def session() -> requests.Session:
    if not hasattr(local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0 (compatible; prospect-audit/1.0)"
        local.session = value
    return local.session


def fetch(url: str):
    try:
        response = session().get(url, timeout=(5, 14), allow_redirects=True)
        if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
            return None
        if len(response.content) > 1_500_000:
            response._content = response.content[:1_500_000]
        return response
    except requests.RequestException:
        return None


def root_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else "https://" + url)
    return f"{parsed.scheme or 'https'}://{parsed.netloc}/"


def clean_name(value: str) -> str:
    value = re.sub(r"^[\s\W_]*(?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)?\d{2})?[\s.・:：-]*", "", value or "")
    value = re.sub(r"^[\s\W_]*(?:Copyright|©|\(c\)|（c）)[\s\W_]*", "", value, flags=re.I)
    value = re.sub(r"\s*(?:All Rights Reserved|Copyright.*|Official Web Site).*?$", "", value, flags=re.I)
    value = re.sub(r"^[【\[]?運営会社[】\]：:\s]*", "", value)
    value = re.sub(r"^[（(]?事務局[：:]\s*", "", value)
    value = re.sub(r"[）)]$", "", value)
    return re.sub(r"\s+", " ", value).strip(" ,.-｜|")


def jsonld_names(soup: BeautifulSoup) -> list[str]:
    names = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            item = stack.pop()
            if isinstance(item, list):
                stack.extend(item)
            elif isinstance(item, dict):
                kind = item.get("@type", "")
                kinds = kind if isinstance(kind, list) else [kind]
                if any(k in {"Organization", "Corporation", "LocalBusiness", "ProfessionalService"} for k in kinds):
                    if isinstance(item.get("name"), str):
                        names.append(item["name"])
                stack.extend(v for v in item.values() if isinstance(v, (dict, list)))
    return names


def labeled_names(soup: BeautifulSoup) -> list[str]:
    names = []
    for node in soup.select("tr,dl,p,li"):
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
        match = re.search(r"(?:会社名|商号|法人名|社名)[：:\s]+(.{2,90})", text)
        if match:
            names.append(match.group(1))
    return names


def trim_legal_name(value: str) -> str:
    name = clean_name(value)
    name = re.split(r"(?:所在地|住所|代表者|設立|資本金|事業内容|TEL|電話|ホーム|ニュース|採用情報|詳しくはこちら|に帰属|＞|#)", name, maxsplit=1)[0].strip()
    prefix = re.search(r"(?:株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人)\s*[A-Za-z0-9一-龠ぁ-んァ-ヶ・ー@＆&＋+\-.]{1,36}", name)
    suffix = re.search(r"[A-Za-z0-9一-龠ぁ-んァ-ヶ・ー@＆&＋+\-.]{1,36}\s*(?:株式会社|有限会社|合同会社|合資会社|合名会社)", name)
    matches = [match.group(0).strip() for match in (prefix, suffix) if match]
    if matches:
        return min(matches, key=len).strip(" ,.-｜|")
    return name


def valid_legal_name(name: str) -> bool:
    if not (2 <= len(name) <= 65) or BAD_NAME.search(name):
        return False
    if re.search(r"(?:株式会社|有限会社|合同会社|合資会社|合名会社)\s*(?:内|本社|拠点|より)?$", name):
        return False
    if re.search(r"^(?:東京都より|運営事務局|HP運営会社名)", name):
        return False
    return bool(JP_LEGAL.search(name))


def pick_name(existing: str, root_soup: BeautifulSoup, company_soups: list[BeautifulSoup]) -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []
    for soup in company_soups:
        candidates.extend(("company_label", value) for value in labeled_names(soup))
        candidates.extend(("company_jsonld", value) for value in jsonld_names(soup))
    candidates.extend(("root_jsonld", value) for value in jsonld_names(root_soup))
    candidates.append(("existing", existing))
    for source, candidate in candidates:
        name = trim_legal_name(candidate)
        if valid_legal_name(name):
            return name, source
    name = clean_name(existing)
    if 2 <= len(name) <= 70 and LEGAL.search(name) and not BAD_NAME.search(name) and name.lower() not in {"inc", "inc.", "company inc."}:
        return name, "existing_english"
    return "", "unresolved"


def discover_pages(root_response) -> tuple[list[str], list[str]]:
    soup = BeautifulSoup(root_response.text, "html.parser")
    company, service = [], []
    root_host = urlparse(root_response.url).netloc.lower().removeprefix("www.")
    for anchor in soup.select("a[href]"):
        label = anchor.get_text(" ", strip=True)
        href = urljoin(root_response.url, anchor.get("href", ""))
        if urlparse(href).netloc.lower().removeprefix("www.") != root_host:
            continue
        path = urlparse(href).path.rstrip("/") + "/"
        if (COMPANY_LABEL.search(label) or COMPANY_PATH.search(path)) and href not in company:
            company.append(href)
        if (SERVICE_LABEL.search(label) or SERVICE_PATH.search(path)) and href not in service:
            service.append(href)
    return company[:2], service[:2]


def contextual_count(text: str, term: str) -> int:
    count = 0
    lower = text.lower()
    needle = term.lower()
    start = 0
    while True:
        index = lower.find(needle, start)
        if index < 0:
            break
        context = text[max(0, index - 90): index + len(term) + 90]
        if term in STRONG_SERVICE or OFFER.search(context):
            count += 1
        start = index + len(needle)
    return count


def classify(root_text: str, root_heading: str, service_text: str) -> tuple[str, list[str], int, int]:
    scored = []
    for index, (category, terms) in enumerate(CATEGORIES):
        hits = []
        score = 0
        for term in terms:
            heading_count = root_heading.lower().count(term.lower())
            service_count = contextual_count(service_text, term)
            root_count = contextual_count(root_text, term)
            if heading_count or service_count or root_count:
                hits.append(term)
                score += min(6, heading_count * 4 + service_count * 3 + root_count)
        scored.append((score, len(hits), -index, category, hits))
    score, distinct, _, category, hits = max(scored)
    if score < 3:
        return "", [], score, distinct
    if PRIMARY_INDUSTRY.search(root_heading) and score < 6 and distinct < 2:
        return "", [], score, distinct
    return category, hits[:3], score, distinct


def audit(row: dict) -> dict:
    url = (row.get("url") or "").strip()
    existing = (row.get("company_name") or "").strip()
    result = {**row, "official_name": "", "name_source": "", "audit_state": "", "audit_reason": "", "category": "", "evidence": "", "resolved_url": ""}
    if not url:
        result.update(audit_state="exclude", audit_reason="blank_url")
        return result
    host = urlparse(url if "://" in url else "https://" + url).netloc.lower().removeprefix("www.")
    if BAD_HOST.search(host):
        result.update(audit_state="exclude", audit_reason="non_official_host")
        return result
    response = fetch(root_url(url))
    if response is None:
        response = fetch(url)
    if response is None:
        result.update(audit_state="review", audit_reason="fetch_failed")
        return result
    company_links, service_links = discover_pages(response)
    company_responses, service_responses = [], []
    for link in company_links:
        page = fetch(link)
        if page is not None:
            company_responses.append(page)
    for link in service_links:
        page = fetch(link)
        if page is not None:
            service_responses.append(page)
    root_soup = BeautifulSoup(response.text, "html.parser")
    company_soups = [BeautifulSoup(item.text, "html.parser") for item in company_responses]
    service_soups = [BeautifulSoup(item.text, "html.parser") for item in service_responses]
    root_text = root_soup.get_text(" ", strip=True)
    service_text = " ".join(soup.get_text(" ", strip=True) for soup in service_soups)
    all_text = " ".join([root_text, service_text, *[soup.get_text(" ", strip=True) for soup in company_soups]])
    title_h1 = " ".join(node.get_text(" ", strip=True) for node in root_soup.select("title,h1")[:4])
    name, source = pick_name(existing, root_soup, company_soups)
    result["official_name"], result["name_source"], result["resolved_url"] = name, source, root_url(response.url).rstrip("/")
    if not name:
        result.update(audit_state="review", audit_reason="official_name_unresolved")
        return result
    name_token = re.sub(r"(?:株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|\W)", "", name).lower()
    reliable_name = source in {"company_label", "company_jsonld", "root_jsonld"} or (len(name_token) >= 3 and name_token in re.sub(r"\W", "", title_h1).lower())
    if not reliable_name and not company_links:
        result.update(audit_state="review", audit_reason="official_domain_unconfirmed")
        return result
    if NON_COMPANY.search(name):
        result.update(audit_state="exclude", audit_reason="non_company_entity")
        return result
    competitor_hits = len(COMPETITOR.findall(all_text))
    if COMPETITOR.search(title_h1) or competitor_hits >= 8:
        result.update(audit_state="exclude", audit_reason="direct_meo_competitor")
        return result
    category, evidence, service_score, distinct = classify(root_text, title_h1, service_text)
    if not category:
        result.update(audit_state="exclude", audit_reason="target_service_unconfirmed")
        return result
    heading_has_target = any(term.lower() in title_h1.lower() for _, terms in CATEGORIES for term in terms)
    if NON_TARGET_NAME.search(name):
        result.update(audit_state="exclude", audit_reason="primary_industry_mismatch")
        return result
    if category == "店舗・業種特化マーケティング" and distinct == 1 and evidence == ["販売促進"]:
        result.update(audit_state="exclude", audit_reason="weak_incidental_keyword")
        return result
    if category == "Web制作・クリエイティブ" and distinct == 1 and evidence == ["ブランディング"] and not heading_has_target:
        result.update(audit_state="exclude", audit_reason="weak_incidental_keyword")
        return result
    if PROJECT_SITE.search(title_h1) and not reliable_name and not heading_has_target:
        result.update(audit_state="exclude", audit_reason="project_or_media_site")
        return result
    result.update(audit_state="valid", audit_reason="", category=category, evidence=" / ".join(evidence))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    output = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(audit, row): row for row in rows}
        for index, future in enumerate(as_completed(futures), 1):
            try:
                output.append(future.result())
            except Exception as exc:
                row = futures[future]
                output.append({**row, "official_name": "", "name_source": "", "audit_state": "review", "audit_reason": f"error:{type(exc).__name__}", "category": "", "evidence": "", "resolved_url": ""})
            if index % 100 == 0:
                counts = {state: sum(1 for item in output if item["audit_state"] == state) for state in ("valid", "exclude", "review")}
                print(f"checked={index}/{len(rows)} {counts}", flush=True)
    output.sort(key=lambda item: int(item["_row"]))
    fields = list(rows[0].keys()) + ["official_name", "name_source", "audit_state", "audit_reason", "category", "evidence", "resolved_url"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output)
    counts = {state: sum(1 for item in output if item["audit_state"] == state) for state in ("valid", "exclude", "review")}
    print(json.dumps({"total": len(output), **counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
