import argparse
import csv
import html
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


PLATFORM = re.compile(r"(SNS|ソーシャルメディア|Instagram|インスタ(?:グラム)?|TikTok|LINE公式|X（旧Twitter）|Twitter|YouTube)", re.I)
SERVICE = re.compile(r"(運用代行|運用支援|アカウント運用|投稿代行|運用コンサル|マーケティング支援|広告運用|SNS広告|企画.{0,12}(?:投稿|撮影|分析))", re.I)
DIRECT = re.compile(r"(SNS運用(?:代行|支援)?|SNSマーケティング|Instagram運用(?:代行|支援)?|インスタ(?:グラム)?運用(?:代行|支援)?|TikTok運用(?:代行|支援)?|LINE公式アカウント運用(?:代行|支援)?|YouTube運用(?:代行|支援)?|SNS広告運用|Instagram広告運用|Meta広告運用)", re.I)
PARTNER_SERVICE = re.compile(r"(Webマーケティング|デジタルマーケティング|Web広告|広告運用|リスティング広告|Web制作|ホームページ制作|集客支援|販促支援|販売促進|プロモーション|マーケティング支援|ブランディング)", re.I)
PROFILE_LINK = re.compile(r"(会社概要|企業情報|会社情報|事業内容|サービス|アクセス|お問い合わせ|corporate|company|about|outline|profile|access|service|contact)", re.I)
HARD_EXCLUDE = re.compile(r"(おすすめ.{0,8}\d+選|比較ランキング|求人情報サイト|転職サイト|スクールのみ|講座のみ|インフルエンサー募集|芸能事務所|タレント事務所)")
ADDRESS = re.compile(r"(?:〒\s*)?(\d{3})[-ー‐‑–—−]?\s*(\d{4})\s*((?:北海道|東京都|京都府|大阪府|.{2,3}県).{2,90}?(?:\d|丁目|番地|番|号))")
PHONE = re.compile(r"(?:TEL|Tel|tel|電話)?\s*[:：]?\s*(0\d{1,4}[-‐‑–—−]\d{1,4}[-‐‑–—−]\d{3,4})")
SOCIAL_HOSTS = {"facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com", "tiktok.com", "line.me"}
BLOCK_HOST_BITS = ("prtimes.jp", "wantedly.com", "indeed.com", "en-gage.net", "lancers.jp", "crowdworks.jp", "ranking", "matome")
thread_local = threading.local()


def visible_text(markup):
    markup = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", markup)
    markup = re.sub(r"(?s)<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def host(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def session():
    if not hasattr(thread_local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 official-site-verification/1.0"
        thread_local.session = value
    return thread_local.session


def fetch(url):
    try:
        response = session().get(url, timeout=(5, 10), allow_redirects=True, stream=True)
        if response.status_code >= 400 or "text/html" not in response.headers.get("content-type", ""):
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


def clean_address(match):
    tail = re.split(r"(TEL|Tel|電話|FAX|Google|アクセス|代表者|設立|資本金|事業内容|営業時間)", match.group(3), maxsplit=1)[0]
    return f"〒{match.group(1)}-{match.group(2)} {tail.strip(' ：:｜|,，。')[:90]}"


def verify(row, partner=False):
    url = (row.get("url") or row.get("website") or "").strip()
    original_host = host(url)
    if not original_host or original_host in SOCIAL_HOSTS or any(bit in original_host for bit in BLOCK_HOST_BITS):
        return None, "blocked_host"
    first = fetch(url)
    if not first:
        return None, "fetch_failed"
    if host(first.url) in SOCIAL_HOSTS or any(bit in host(first.url) for bit in BLOCK_HOST_BITS):
        return None, "blocked_redirect"

    pages = [(first.url, first.text)]
    links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', first.text, re.I | re.S)
    candidates = []
    for href, label_html in links:
        label = visible_text(label_html)
        target = urljoin(first.url, html.unescape(href)).split("#")[0]
        if host(target) == host(first.url) and target != first.url and PROFILE_LINK.search(f"{label} {href}") and target not in candidates:
            candidates.append(target)
    for target in candidates[:3]:
        response = fetch(target)
        if response:
            pages.append((response.url, response.text))

    text = " ".join(visible_text(markup) for _, markup in pages)
    direct = list(dict.fromkeys(DIRECT.findall(text)))
    relevant = bool(direct or (PLATFORM.search(text) and SERVICE.search(text)) or (partner and PARTNER_SERVICE.search(text)))
    has_company = bool(re.search(r"(会社概要|企業情報|法人番号|株式会社|有限会社|合同会社)", text) or re.search(r"(株式会社|有限会社|合同会社|㈱|㈲)", row.get("company_name", "")))
    address_matches = list(ADDRESS.finditer(text))
    fallback_address = (row.get("address") or "").strip()
    phones = [p.translate(str.maketrans("‐‑–—−", "-----")) for p in PHONE.findall(text)]
    has_contact = bool(re.search(r"(お問い合わせ|問い合わせ|contact|tel:|mailto:)", text, re.I))
    if HARD_EXCLUDE.search(text[:5000]) and not has_company:
        return None, "hard_exclude"
    if not relevant:
        return None, "no_sns_service"
    if not has_company:
        return None, "no_company"
    if not address_matches and not fallback_address:
        return None, "no_address"
    if not phones and not has_contact and not (row.get("phone") or "").strip():
        return None, "no_contact"

    name = (row.get("company_name") or row.get("title") or "").strip()
    return {
        "company_name": name,
        "url": first.url,
        "address": clean_address(address_matches[0]) if address_matches else fallback_address,
        "phone": phones[0] if phones else (row.get("phone") or "").strip(),
        "maps_url": (row.get("maps_url") or "").strip(),
        "service_evidence": " / ".join(direct[:5]) if direct else "SNS platform + operation service",
        "pages_checked": " | ".join(u for u, _ in pages),
    }, "kept"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--audit", required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--partner", action="store_true")
    args = parser.parse_args()
    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    kept, audit = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(verify, row, args.partner): row for row in rows}
        for index, future in enumerate(as_completed(futures), 1):
            row = futures[future]
            try:
                item, reason = future.result()
            except Exception as exc:
                item, reason = None, f"error:{type(exc).__name__}"
            audit.append({"company_name": row.get("company_name", ""), "url": row.get("url", ""), "result": reason})
            if item:
                kept.append(item)
            if index % 50 == 0:
                print(f"checked={index}/{len(rows)} kept={len(kept)}", flush=True)

    fields = ["company_name", "url", "address", "phone", "maps_url", "service_evidence", "pages_checked"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(kept)
    with Path(args.audit).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "result"])
        writer.writeheader(); writer.writerows(audit)
    print(f"verified={len(kept)} total={len(rows)} output={args.output_csv}")


if __name__ == "__main__":
    main()
