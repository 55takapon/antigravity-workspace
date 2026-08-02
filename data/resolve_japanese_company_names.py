import argparse
import csv
import html
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


LEGAL_FORMS = "株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人"
LEGAL = re.compile(rf"(?:{LEGAL_FORMS})")
LABEL = re.compile(r"^(?:会社名|商号|法人名|正式名称|社名|運営会社)$")
COMPANY_LABEL = re.compile(r"^(?:会社概要|企業情報|会社案内|運営会社|corporate|company|about(?: us)?|profile)$", re.I)
COMPANY_PATH = re.compile(r"/(?:company|corporate|about|profile|overview|outline)/?$", re.I)
POLICY_LABEL = re.compile(r"^(?:プライバシーポリシー|個人情報保護方針|特定商取引法に基づく表記|利用規約|privacy(?: policy)?|terms)$", re.I)
POLICY_PATH = re.compile(r"/(?:privacy|privacy-policy|policy|terms|tokushoho|law)/?$", re.I)
BAD = re.compile(r"(?:著作権|帰属|事務局|運営事務局|主催|会社概要はこちら|公式サイト|オフィシャルサイト|登録商標|All Rights|Copyright|〒|TEL|FAX)", re.I)
GENERIC = re.compile(rf"^(?:{LEGAL_FORMS})\s*(?:代表|代表取締役|代表取締役社長|創立|英語表記|本社|拠点|所在地|設立|について|内|co)?$", re.I)
STOP = re.compile(r"(?:所在地|住所|代表者|代表取締役|設立|創業|資本金|事業内容|電話|TEL|FAX|〒|個人情報|以下[、,]|は[、,]|では[、,]|について|ご相談|会社概要|会社案内|サービス|製品情報|事例紹介|お問い?合せ|ホーム|HOME)", re.I)
NAME_CHARS = r"A-Za-z0-9Ａ-Ｚａ-ｚ一-龠々ぁ-んァ-ヶ・ー＆&＋+@'’\-. \u3000"
local = threading.local()


def session() -> requests.Session:
    if not hasattr(local, "value"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0 (compatible; official-name-resolver/1.0)"
        local.value = value
    return local.value


def fetch(url: str):
    try:
        response = session().get(url, timeout=(5, 15), allow_redirects=True)
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


def normalize(value: str) -> str:
    return re.sub(r"[^0-9a-z一-龠ぁ-んァ-ヶ]", "", html.unescape(value or "").lower())


def clean_candidate(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"^[\s\W_]*(?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)?\d{2})?[\s.・:：-]*", "", value)
    value = re.sub(r"^[\s\W_]*(?:Copyright|©|\(c\)|（c）)[\s\W_]*", "", value, flags=re.I)
    value = re.sub(r"^[【\[]?(?:運営会社|会社名|法人名|商号)[】\]：:\s]*", "", value)
    value = re.sub(r"\s*(?:All Rights Reserved|Copyright.*)$", "", value, flags=re.I)
    value = re.split(r"[（(【\[]|(?:英語|英文)表記|\s+[|｜]\s+", value, maxsplit=1)[0]
    value = STOP.split(value, maxsplit=1)[0]
    value = re.sub(r"\s+", " ", value).strip(" ,.:：;；-｜|()（）[]【】")
    prefix = re.search(rf"(?:{LEGAL_FORMS})\s*[{NAME_CHARS}]{{2,50}}", value)
    suffix = re.search(rf"[{NAME_CHARS}]{{2,50}}?\s*(?:{LEGAL_FORMS})", value)
    matches = [match.group(0).strip() for match in (prefix, suffix) if match]
    if matches:
        value = min(matches, key=len)
    value = re.sub(r"\s+(?:Inc\.?|Co\.?\s*,?\s*Ltd\.?|Ltd\.?|LLC)\s*$", "", value, flags=re.I)
    # Some page builders duplicate a trailing brand after the legal name.
    match = re.match(rf"^((?:{LEGAL_FORMS})\s*(.+?))\s+\2$", value, flags=re.I)
    return (match.group(1) if match else value).strip()


def valid_name(value: str) -> bool:
    if not (3 <= len(value) <= 60) or not LEGAL.search(value):
        return False
    if BAD.search(value) or GENERIC.fullmatch(value):
        return False
    if re.search(r"(?:は|が|を|に|へ|と|より|です|ます)$", value):
        return False
    return len(normalize(LEGAL.sub("", value))) >= 2


def labeled_candidates(soup: BeautifulSoup) -> list[str]:
    values = []
    for row in soup.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) >= 2 and LABEL.fullmatch(re.sub(r"\s+", "", cells[0].get_text(" ", strip=True))):
            values.append(cells[1].get_text(" ", strip=True))
    for dt in soup.select("dt"):
        if LABEL.fullmatch(re.sub(r"\s+", "", dt.get_text(" ", strip=True))):
            dd = dt.find_next_sibling("dd")
            if dd:
                values.append(dd.get_text(" ", strip=True))
    for node in soup.select("p,li,div"):
        text = re.sub(r"\s+", " ", node.get_text(" ", strip=True))
        if len(text) > 180:
            continue
        match = re.match(r"(?:会社名|商号|法人名|正式名称|社名)[：:\s]+(.{3,90})", text)
        if match:
            values.append(match.group(1))
    return values


def jsonld_candidates(soup: BeautifulSoup) -> list[str]:
    values = []
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
                kinds = item.get("@type", [])
                kinds = kinds if isinstance(kinds, list) else [kinds]
                if any(kind in {"Organization", "Corporation", "LocalBusiness", "ProfessionalService"} for kind in kinds):
                    if isinstance(item.get("legalName"), str):
                        values.append(item["legalName"])
                    if isinstance(item.get("name"), str):
                        values.append(item["name"])
                stack.extend(value for value in item.values() if isinstance(value, (dict, list)))
    return values


def body_legal_candidates(soup: BeautifulSoup) -> list[str]:
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    values = []
    patterns = [
        rf"((?:{LEGAL_FORMS})\s*[A-Za-z0-9Ａ-Ｚａ-ｚ一-龠ぁ-んァ-ヶ・ー＆&＋+@'’\-. ]{{2,40}})",
        rf"([A-Za-z0-9Ａ-Ｚａ-ｚ一-龠ぁ-んァ-ヶ・ー＆&＋+@'’\-. ]{{2,40}}\s*(?:{LEGAL_FORMS}))",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            context = text[max(0, match.start() - 60): match.end() + 60]
            if re.search(r"(?:個人情報|プライバシー|当社|弊社|運営|会社概要|法人名|会社名|商号|Copyright|©)", context, re.I):
                values.append(match.group(1))
    return values


def discover_pages(response) -> list[str]:
    soup = BeautifulSoup(response.text, "html.parser")
    host = urlparse(response.url).netloc.lower().removeprefix("www.")
    links = []
    for anchor in soup.select("a[href]"):
        label = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
        href = urljoin(response.url, anchor.get("href", ""))
        if urlparse(href).netloc.lower().removeprefix("www.") != host:
            continue
        path = urlparse(href).path.rstrip("/") + "/"
        if COMPANY_LABEL.fullmatch(label) or COMPANY_PATH.search(path) or POLICY_LABEL.fullmatch(label) or POLICY_PATH.search(path):
            if href not in links:
                links.append(href)
    return links[:5]


def resolve(row: dict) -> dict:
    result = {**row, "resolved_name": "", "name_source": "", "name_source_url": "", "name_state": "", "name_reason": ""}
    if not (row.get("contact_url") or "").strip():
        result.update(name_state="skip", name_reason="blank_contact_url")
        return result
    response = fetch(root_url(row.get("url", ""))) or fetch(row.get("url", ""))
    if response is None:
        result.update(name_state="exclude", name_reason="official_site_fetch_failed")
        return result
    pages = [("root", response)]
    for link in discover_pages(response):
        page = fetch(link)
        if page is not None:
            pages.append(("official_page", page))
    candidates = []
    for source, page in pages:
        soup = BeautifulSoup(page.text, "html.parser")
        priority = 0 if source == "official_page" else 3
        candidates.extend((priority, "labeled", page.url, value) for value in labeled_candidates(soup))
        candidates.extend((priority + 1, "jsonld", page.url, value) for value in jsonld_candidates(soup))
        candidates.extend((priority + 2, "body_legal", page.url, value) for value in body_legal_candidates(soup))
    existing = clean_candidate(row.get("company_name", ""))
    all_text = " ".join(BeautifulSoup(page.text, "html.parser").get_text(" ", strip=True) for _, page in pages)
    if valid_name(existing) and normalize(existing) in normalize(all_text):
        # Keep an already valid official Japanese name unless an explicit
        # company-profile label provides a better correction.
        candidates.append((-1, "existing_confirmed", response.url, existing))
    seen = set()
    existing_key = normalize(existing)
    for _, source, source_url, raw in sorted(candidates, key=lambda item: item[0]):
        name = clean_candidate(raw)
        key = normalize(name)
        if key in seen:
            continue
        seen.add(key)
        if source == "body_legal" and existing_key and not (existing_key in key or key in existing_key):
            continue
        if valid_name(name):
            result.update(resolved_name=name, name_source=source, name_source_url=source_url, name_state="confirmed", name_reason="")
            return result
    result.update(name_state="exclude", name_reason="japanese_legal_name_unconfirmed")
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
        futures = {executor.submit(resolve, row): row for row in rows}
        for index, future in enumerate(as_completed(futures), 1):
            try:
                output.append(future.result())
            except Exception as exc:
                row = futures[future]
                output.append({**row, "resolved_name": "", "name_source": "", "name_source_url": "", "name_state": "exclude", "name_reason": f"error:{type(exc).__name__}"})
            if index % 100 == 0:
                counts = {state: sum(1 for row in output if row["name_state"] == state) for state in ("confirmed", "exclude", "skip")}
                print(f"checked={index}/{len(rows)} {counts}", flush=True)
    output.sort(key=lambda row: int(row["_row"]))
    fields = list(rows[0].keys()) + ["resolved_name", "name_source", "name_source_url", "name_state", "name_reason"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output)
    counts = {state: sum(1 for row in output if row["name_state"] == state) for state in ("confirmed", "exclude", "skip")}
    print(json.dumps({"total": len(output), **counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
