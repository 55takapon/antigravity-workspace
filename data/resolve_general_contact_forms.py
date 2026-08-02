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

from audit_contact_form_existence import classify_form, CONTACT_MARKER, FORM_HOST


GOOD = re.compile(r"(?:contact|inquiry|inquire|toiawase|otoiawase|お問い合わせ|お問合せ|問い合わせ|ご相談|ご依頼)", re.I)
BAD_PURPOSE = re.compile(r"(?:資料請求|資料ダウンロード|ダウンロードフォーム|見積依頼|お見積もり|採用応募|採用エントリー|中途エントリー|応募フォーム|エントリーフォーム|予約フォーム|セミナー申込|イベント申込|デモ申込|トライアル申込)", re.I)
HARD_BAD_PURPOSE = re.compile(r"(?:資料ダウンロード|ダウンロードフォーム|見積依頼|お見積もり|採用応募|採用エントリー|中途エントリー|応募フォーム|エントリーフォーム|予約フォーム|セミナー申込|イベント申込|デモ申込|トライアル申込)", re.I)
BAD_PATH = re.compile(r"/(?:request|download|dlform|document|material|catalog|brochure|price|pricing|estimate|quote|recruit|career|entry[^/]*|apply|application|reservation|reserve|booking|seminar|event|demo|trial)(?:/|$|[?#])", re.I)
NON_FORM_LINK = re.compile(r"^(?:#|javascript:|mailto:|tel:)", re.I)
thread_local = threading.local()


def session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0 (compatible; general-contact-resolver/1.0)"
        thread_local.session = value
    return thread_local.session


def host(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def acceptable_host(candidate: str, base: str) -> bool:
    left, right = host(candidate), host(base)
    return bool(left and (left == right or left.endswith("." + right) or right.endswith("." + left) or FORM_HOST.search(candidate)))


def score_candidate(url: str, text: str, base: str, current: str) -> int:
    if not url or NON_FORM_LINK.search(url) or not acceptable_host(url, base):
        return -1000
    signature = f"{url} {text}"
    score = 0
    path = urlparse(url).path.rstrip("/").lower()
    if re.search(r"/(?:contact|inquiry|inquire|toiawase|otoiawase)$", path):
        score += 120
    if re.search(r"/(?:お問い合わせ|お問合せ|問い合わせ)$", path):
        score += 120
    if path.endswith("/mail"):
        score += 80
    if GOOD.search(text):
        score += 60
    if GOOD.search(url):
        score += 50
    if FORM_HOST.search(url):
        score += 35
    if url == current:
        score += 5
    if BAD_PATH.search(url):
        score -= 180
    if BAD_PURPOSE.search(text):
        score -= 160
    return score


def page_form(response) -> tuple[bool, str, str, list[tuple[str, str]]]:
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    heading = " ".join(node.get_text(" ", strip=True) for node in soup.select("h1,h2")[:5])
    purpose = f"{title} {heading}"
    if HARD_BAD_PURPOSE.search(purpose) or (BAD_PURPOSE.search(purpose) and not GOOD.search(purpose)):
        return False, "wrong_purpose", title, []
    for form in soup.select("form"):
        valid, evidence = classify_form(form)
        if valid:
            return True, evidence, title, []
    for iframe in soup.select("iframe[src]"):
        source = urljoin(response.url, iframe.get("src", ""))
        signature = " ".join([source, iframe.get("title", ""), iframe.get("name", "")])
        if FORM_HOST.search(source) or CONTACT_MARKER.search(signature):
            return True, "form_iframe", title, []
    if FORM_HOST.search(response.url):
        body = soup.get_text(" ", strip=True)
        if re.search(r"(?:フォーム|質問|回答を送信|送信|必須|required)", body, re.I) and not re.search(r"(?:権限が必要|ログインしてください|受付を終了|回答の受け付けを終了)", body):
            return True, "external_form_open", title, []
    nested = []
    for anchor in soup.select("a[href]"):
        text = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))
        href = urljoin(response.url, anchor.get("href", ""))
        if GOOD.search(f"{text} {href}") or FORM_HOST.search(href):
            nested.append((href, text))
    return False, "no_form", title, nested


def resolve(row: dict, page: dict | None) -> dict:
    base, current = row.get("url", ""), row.get("contact_url", "")
    candidates = [(current, "current")]
    for link in (page or {}).get("links", []):
        candidates.append((link.get("href", ""), " ".join([link.get("text", ""), link.get("alt_title", "")])))
    ranked, seen = [], set()
    for url, text in candidates:
        url = urljoin(base, url).split("#")[0] if url and not FORM_HOST.search(url) else url
        if not url or url in seen:
            continue
        seen.add(url)
        score = score_candidate(url, text, base, current.split("#")[0])
        if score > 0:
            ranked.append((score, url, text))
    ranked.sort(reverse=True)
    attempts = []
    for score, url, text in ranked[:8]:
        try:
            response = session().get(url, timeout=(5, 20), allow_redirects=True)
        except requests.RequestException as exc:
            attempts.append(f"{url}:fetch_{type(exc).__name__}")
            continue
        if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
            attempts.append(f"{url}:http_{response.status_code}")
            continue
        valid, evidence, title, nested = page_form(response)
        if valid and not BAD_PATH.search(response.url):
            return {"_row": row.get("_row", ""), "company_name": row.get("company_name", ""), "url": base, "old_contact_url": current, "resolved_contact_url": response.url, "contact_state": "valid", "contact_evidence": evidence, "page_title": title, "attempts": " | ".join(attempts)}
        attempts.append(f"{response.url}:{evidence}")
        for nested_url, nested_text in nested[:5]:
            if score_candidate(nested_url, nested_text, base, current) <= 0 or BAD_PATH.search(nested_url):
                continue
            try:
                nested_response = session().get(nested_url, timeout=(5, 20), allow_redirects=True)
                nested_valid, nested_evidence, nested_title, _ = page_form(nested_response)
                if nested_valid and not BAD_PATH.search(nested_response.url):
                    return {"_row": row.get("_row", ""), "company_name": row.get("company_name", ""), "url": base, "old_contact_url": current, "resolved_contact_url": nested_response.url, "contact_state": "valid", "contact_evidence": nested_evidence, "page_title": nested_title, "attempts": " | ".join(attempts)}
                attempts.append(f"{nested_response.url}:{nested_evidence}")
            except requests.RequestException as exc:
                attempts.append(f"{nested_url}:fetch_{type(exc).__name__}")
    return {"_row": row.get("_row", ""), "company_name": row.get("company_name", ""), "url": base, "old_contact_url": current, "resolved_contact_url": "", "contact_state": "unresolved", "contact_evidence": "general_contact_form_unconfirmed", "page_title": "", "attempts": " | ".join(attempts)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("batch_json")
    parser.add_argument("output_csv")
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    pages = json.loads(Path(args.batch_json).read_text(encoding="utf-8"))
    by_row = {str(page.get("_row")): page for page in pages}
    output = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(resolve, row, by_row.get(str(row.get("_row")))): row for row in rows}
        for index, future in enumerate(as_completed(futures), 1):
            row = futures[future]
            try:
                output.append(future.result())
            except Exception as exc:
                output.append({"_row": row.get("_row", ""), "company_name": row.get("company_name", ""), "url": row.get("url", ""), "old_contact_url": row.get("contact_url", ""), "resolved_contact_url": "", "contact_state": "unresolved", "contact_evidence": f"error:{type(exc).__name__}", "page_title": "", "attempts": ""})
            if index % 50 == 0:
                print(f"checked={index}/{len(rows)} valid={sum(item['contact_state']=='valid' for item in output)}", flush=True)
    output.sort(key=lambda item: int(item["_row"]))
    fields = ["_row", "company_name", "url", "old_contact_url", "resolved_contact_url", "contact_state", "contact_evidence", "page_title", "attempts"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(output)
    print(json.dumps({"total": len(output), "valid": sum(item["contact_state"] == "valid" for item in output), "unresolved": sum(item["contact_state"] != "valid" for item in output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
