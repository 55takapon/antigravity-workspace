import argparse
import csv
import html
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


POSITIVE = re.compile(
    r"(Webマーケティング|WEBマーケティング|ウェブマーケティング|"
    r"デジタルマーケティング|マーケティング支援|マーケティング戦略|"
    r"広告運用|運用型広告|インターネット広告|デジタル広告|Web広告|WEB広告|"
    r"リスティング広告|Google広告|Yahoo!?広告|Meta広告|SNS広告|"
    r"SNS運用|Instagram運用|TikTok運用|LINE運用|"
    r"販売促進|販促支援|プロモーション|集客支援|集客コンサル|"
    r"Webコンサルティング|WEBコンサルティング|SEO対策|SEOコンサル|"
    r"コンテンツマーケティング|ブランディング|PR支援|広報支援|"
    r"EC支援|ECコンサル|採用マーケティング)"
)
DIGITAL_CONTEXT = re.compile(
    r"(Web|WEB|ウェブ|デジタル|インターネット|SNS|Instagram|TikTok|"
    r"LINE|Google|Yahoo|ホームページ|SEO|ECサイト)",
    re.I,
)
AD_CONTEXT = re.compile(
    r"(広告代理|総合広告|広告企画|広告制作|広告会社|広告業|媒体計画|"
    r"メディアプランニング|販売促進|販促企画|プロモーション)"
)
PROFILE_LINK = re.compile(
    r"(会社概要|企業情報|会社情報|事業内容|サービス|アクセス|"
    r"corporate|company|about|outline|profile|access|service|contact)",
    re.I,
)
HARD_EXCLUDE = re.compile(
    r"(求人情報サイト|転職サイト|比較サイト|ランキング|スクールのみ|"
    r"マーケティング情報メディア|広告媒体社)"
)
ADDRESS = re.compile(
    r"(?:〒\s*)?(\d{3})[-ー‐‑–—−]?\s*(\d{4})\s*"
    r"((?:北海道|東京都|京都府|大阪府|.{2,3}県).{2,90}?(?:\d|丁目|番地|番|号))"
)
PHONE = re.compile(
    r"(?:TEL|Tel|tel|電話)?\s*[:：]?\s*"
    r"(0\d{1,4}[-‐‑–—−]\d{1,4}[-‐‑–—−]\d{3,4})"
)


def visible_text(markup):
    markup = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", markup)
    markup = re.sub(r"(?s)<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def normalize_host(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def same_host(base, target):
    host = normalize_host(urljoin(base, target))
    return bool(host) and host == normalize_host(base)


def fetch(session, url):
    try:
        response = session.get(url, timeout=12, allow_redirects=True)
        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400 or "text/html" not in content_type:
            return None
        response.encoding = response.apparent_encoding or response.encoding
        return response
    except requests.RequestException:
        return None


def clean_address(match):
    tail = re.split(
        r"(TEL|Tel|電話|FAX|Google|アクセス|代表者|設立|資本金|事業内容|営業時間)",
        match.group(3),
        maxsplit=1,
    )[0]
    tail = tail.strip(" ：:｜|,，。")
    return f"〒{match.group(1)}-{match.group(2)} {tail[:90]}"


def verify(row, delay):
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/126.0 official-site-verification/1.0"
    )
    first = fetch(session, row["url"])
    if not first:
        return None, "fetch_failed"

    pages = [(first.url, first.text)]
    links = re.findall(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        first.text,
        re.I | re.S,
    )
    profile_urls = []
    for href, label_html in links:
        label = visible_text(label_html)
        try:
            absolute = urljoin(first.url, html.unescape(href)).split("#")[0]
        except ValueError:
            continue
        if (
            absolute != first.url
            and same_host(first.url, absolute)
            and PROFILE_LINK.search(f"{label} {href}")
            and absolute not in profile_urls
        ):
            profile_urls.append(absolute)

    for target in profile_urls[:2]:
        time.sleep(delay)
        response = fetch(session, target)
        if response:
            pages.append((response.url, response.text))

    text = " ".join(visible_text(markup) for _, markup in pages)
    services = list(dict.fromkeys(POSITIVE.findall(text)))
    if not services and DIGITAL_CONTEXT.search(text) and AD_CONTEXT.search(text):
        services = ["広告・デジタル支援"]
    address_matches = list(ADDRESS.finditer(text))
    phones = list(dict.fromkeys(
        value.replace("‐", "-").replace("‑", "-").replace("–", "-")
        .replace("—", "-").replace("−", "-")
        for value in PHONE.findall(text)
    ))
    has_company = bool(
        re.search(r"(会社概要|企業情報|法人番号|株式会社|有限会社|合同会社)", text)
        or re.search(r"(株式会社|有限会社|合同会社|㈱|㈲)", row.get("company_name", ""))
    )
    has_contact = bool(re.search(r"(お問い合わせ|問い合わせ|contact|tel:|mailto:)", text, re.I))

    if HARD_EXCLUDE.search(text):
        return None, "hard_exclude"
    if not services:
        return None, "no_service"
    if not has_company:
        return None, "no_company"
    fallback_address = (row.get("address") or "").strip()
    if not address_matches and not fallback_address:
        return None, "no_address"
    if not (phones or has_contact):
        return None, "no_contact"

    return {
        "company_name": row["company_name"].strip(),
        "url": first.url,
        "address": clean_address(address_matches[0]) if address_matches else fallback_address,
        "phone": phones[0] if phones else "",
        "maps_url": row.get("maps_url", ""),
        "service_evidence": " / ".join(services[:6]),
        "pages_checked": " | ".join(url for url, _ in pages),
    }, "kept"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--audit")
    parser.add_argument("--delay", type=float, default=0.15)
    args = parser.parse_args()

    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    kept = []
    audit = []

    def save_results():
        output_fields = ["company_name", "url", "address", "phone", "maps_url"]
        with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=output_fields)
            writer.writeheader()
            writer.writerows({key: row[key] for key in output_fields} for row in kept)
        if args.audit:
            with Path(args.audit).open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "result"])
                writer.writeheader()
                writer.writerows(audit)

    for index, row in enumerate(rows, start=1):
        try:
            item, reason = verify(row, args.delay)
        except Exception as exc:
            item, reason = None, f"error:{type(exc).__name__}"
        audit.append({
            "company_name": row.get("company_name", ""),
            "url": row.get("url", ""),
            "result": reason,
        })
        if item:
            kept.append(item)
        if index % 25 == 0:
            save_results()
            print(f"checked={index}/{len(rows)} kept={len(kept)}", flush=True)
        time.sleep(args.delay)

    save_results()
    print(f"verified={len(kept)} total={len(rows)} output={args.output_csv}")


if __name__ == "__main__":
    main()
