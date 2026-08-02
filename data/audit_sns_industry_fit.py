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


SNS_TERMS = [
    "SNS運用代行", "SNS運用支援", "SNSアカウント運用", "SNS運用", "SNSマーケティング",
    "Instagram運用代行", "Instagram運用支援", "Instagram運用", "インスタグラム運用代行",
    "インスタグラム運用", "インスタ運用代行", "TikTok運用代行", "TikTok運用",
    "X運用代行", "Twitter運用代行", "LINE公式アカウント運用", "YouTube運用代行",
    "SNS広告運用", "SNS広告", "Instagram広告運用", "Meta広告運用",
]
WEB_TERMS = [
    "ホームページ制作", "ホームページ作成", "Webサイト制作", "ウェブサイト制作", "Web制作",
    "ウェブ制作", "コーポレートサイト制作", "採用サイト制作", "ECサイト制作", "LP制作",
    "ランディングページ制作", "サイトリニューアル", "WordPress制作",
]
MARKETING_TERMS = [
    "Webマーケティング", "ウェブマーケティング", "デジタルマーケティング", "Web広告運用",
    "Web広告", "リスティング広告運用", "リスティング広告", "Google広告運用", "広告運用代行",
    "SEOコンサルティング", "SEO対策", "Web集客支援", "集客支援", "販促支援",
    "マーケティング支援", "広告代理店", "プロモーション支援",
]
MEO_TERMS = ["MEO対策", "MEO運用代行", "Googleマップ集客", "Googleビジネスプロフィール運用", "ローカルSEO"]
SERVICE_LABEL = re.compile(
    r"^(?:サービス|事業内容|事業紹介|提供サービス|業務内容|できること|solution|solutions|service|services|business|works?)$",
    re.I,
)
SERVICE_PATH = re.compile(
    r"/(?:service|services|business|solution|solutions|web(?:site|[-_](?:create|production))?|homepage|home-page|"
    r"sitemake|sns|social-media|instagram|marketing|advertising|promotion|creative|webdesign|web-design|lp)(?:/|[-_.]|$)",
    re.I,
)
BLOCK_PATH = re.compile(
    r"/(?:blog|column|news|topics|case|cases|customer|customers|interview|example|examples|achievement|achievements|"
    r"works|category_works|portfolio|project|projects|result|results|media|contact|inquiry|recruit|career|member|staff|tag|category)(?:/|_|$)",
    re.I,
)
OFFER_CONTEXT = re.compile(r"(?:サービス|事業|提供|代行|支援|サポート|受託|対応|承ります|お任せ|ソリューション|プラン|料金|ご相談)")
thread_local = threading.local()


def session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0 (compatible; industry-fit-audit/1.0)"
        thread_local.session = value
    return thread_local.session


def fetch(url: str):
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


def host(url: str) -> str:
    try:
        return urlparse(url if "://" in url else "https://" + url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def root_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else "https://" + url)
    return f"{parsed.scheme or 'https'}://{parsed.netloc}/"


def text_of(soup: BeautifulSoup, selector: str | None = None) -> str:
    nodes = soup.select(selector) if selector else [soup]
    return re.sub(r"\s+", " ", " ".join(node.get_text(" ", strip=True) for node in nodes)).strip()


def discover_service_pages(response) -> list[tuple[str, str]]:
    soup = BeautifulSoup(response.text, "html.parser")
    base_host = host(response.url)
    found = []
    for anchor in soup.select("a[href]"):
        label = text_of(anchor)
        target = urljoin(response.url, anchor.get("href", "")).split("#")[0]
        path = urlparse(target).path
        if host(target) != base_host or BLOCK_PATH.search(path):
            continue
        if SERVICE_LABEL.fullmatch(label) or SERVICE_PATH.search(path):
            item = (target, label)
            if target != response.url and all(existing[0] != target for existing in found):
                found.append(item)
    return found[:6]


def term_hits(term: str, pages: list[dict]) -> list[dict]:
    hits = []
    needle = term.lower()
    for page in pages:
        heading = page["heading"]
        body = page["body"]
        heading_hit = needle in heading.lower()
        contexts = []
        lower = body.lower()
        start = 0
        while True:
            index = lower.find(needle, start)
            if index < 0:
                break
            context = body[max(0, index - 100):index + len(term) + 100]
            if OFFER_CONTEXT.search(context):
                contexts.append(context)
            start = index + len(needle)
        if heading_hit or contexts:
            score = (8 if page["kind"] == "service" and heading_hit else 5 if heading_hit else 0)
            score += 4 if page["kind"] == "service" and contexts else 2 if contexts else 0
            hits.append({"term": term, "url": page["url"], "score": score, "heading": heading_hit})
    return hits


def best_evidence(terms: list[str], pages: list[dict]) -> tuple[int, list[dict]]:
    all_hits = []
    for term in terms:
        all_hits.extend(term_hits(term, pages))
    all_hits.sort(key=lambda item: (-item["score"], terms.index(item["term"]), item["url"]))
    unique, seen = [], set()
    for item in all_hits:
        if item["term"] in seen:
            continue
        seen.add(item["term"])
        unique.append(item)
    score = sum(item["score"] for item in unique[:3])
    return score, unique[:5]


def audit(row: dict) -> dict:
    result = {**row, "fit_state": "", "fit_reason": "", "fit_category": "", "fit_evidence": "", "evidence_urls": ""}
    url = (row.get("url") or "").strip()
    if not url or not (row.get("contact_url") or "").strip():
        result.update(fit_state="exclude", fit_reason="missing_required_url")
        return result
    response = fetch(root_url(url)) or fetch(url)
    if response is None:
        result.update(fit_state="review", fit_reason="official_site_fetch_failed")
        return result
    if host(response.url) != host(url):
        # Redirects within an apex/www pair are fine; unrelated hosts need review.
        left, right = host(response.url), host(url)
        if not (left.endswith("." + right) or right.endswith("." + left)):
            result.update(fit_state="review", fit_reason="cross_domain_redirect")
            return result

    root_soup = BeautifulSoup(response.text, "html.parser")
    pages = [{"kind": "root", "url": response.url, "heading": text_of(root_soup, "title,h1,h2"), "body": text_of(root_soup)}]
    for page_url, label in discover_service_pages(response):
        page = fetch(page_url)
        if page is None:
            continue
        soup = BeautifulSoup(page.text, "html.parser")
        pages.append({"kind": "service", "url": page.url, "heading": f"{label} {text_of(soup, 'title,h1,h2')}", "body": text_of(soup)})

    sns_score, sns_hits = best_evidence(SNS_TERMS, pages)
    web_score, web_hits = best_evidence(WEB_TERMS, pages)
    marketing_score, marketing_hits = best_evidence(MARKETING_TERMS, pages)
    meo_score, meo_hits = best_evidence(MEO_TERMS, pages)

    # One explicit service-page hit or two corroborating root/service hits are required.
    def qualifies(score, hits):
        return bool(hits) and (score >= 8 or any(item["heading"] and item["score"] >= 5 for item in hits))

    sns_ok = qualifies(sns_score, sns_hits)
    web_ok = qualifies(web_score, web_hits)
    marketing_ok = qualifies(marketing_score, marketing_hits)
    meo_primary = meo_score >= 12 and not (sns_ok or web_ok or marketing_ok)

    if meo_primary:
        state, category, reason, hits = "exclude", "MEO直接競合", "direct_meo_competitor", meo_hits
    elif sns_ok:
        state, category, reason, hits = "sns", "SNS運用・SNS広告", "", sns_hits
    elif web_ok:
        state, category, reason, hits = "web", "Web制作会社", "", web_hits
    elif marketing_ok:
        state, category, reason, hits = "marketing", "Webマーケティング・広告", "", marketing_hits
    else:
        state, category, reason, hits = "exclude", "", "official_service_unconfirmed", []

    result.update(
        fit_state=state,
        fit_reason=reason,
        fit_category=category,
        fit_evidence=" / ".join(item["term"] for item in hits[:3]),
        evidence_urls=" | ".join(dict.fromkeys(item["url"] for item in hits[:3])),
    )
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
            row = futures[future]
            try:
                output.append(future.result())
            except Exception as exc:
                output.append({**row, "fit_state": "review", "fit_reason": f"error:{type(exc).__name__}", "fit_category": "", "fit_evidence": "", "evidence_urls": ""})
            if index % 100 == 0:
                counts = {state: sum(item["fit_state"] == state for item in output) for state in ("sns", "web", "marketing", "exclude", "review")}
                print(f"checked={index}/{len(rows)} {counts}", flush=True)
    output.sort(key=lambda item: int(item["_row"]))
    fields = list(rows[0].keys()) + ["fit_state", "fit_reason", "fit_category", "fit_evidence", "evidence_urls"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(output)
    counts = {state: sum(item["fit_state"] == state for item in output) for state in ("sns", "web", "marketing", "exclude", "review")}
    print(json.dumps({"total": len(output), **counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
