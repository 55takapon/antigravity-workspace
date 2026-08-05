from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).parent
SOURCE = "https://www.aca-j.or.jp/meibo/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
CONTACT_RE = re.compile(r"contact|inquiry|toiawase|otoiawase|form|お問い合わせ|お問合せ|問合せ|ご相談|見積", re.I)
NOISE_RE = re.compile(r"採用|recruit|ログイン|login|資料ダウンロード|download|プライバシー|privacy", re.I)
PROFILE_RE = re.compile(r"会社概要|企業情報|会社情報|法人概要|about(?:us)?|company|corporate|profile", re.I)


def host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def company_key(value: str) -> str:
    value = re.sub(r"\s+", "", value).lower()
    return re.sub(r"株式会社|有限会社|合同会社|一般社団法人|[・･.,，．_/'\"()（）\[\]［］:：-]", "", value)


def discover(row: dict[str, str]) -> dict[str, str]:
    try:
        response = requests.get(row["url"], headers=HEADERS, timeout=20, allow_redirects=True)
        response.raise_for_status()
        if "html" not in response.headers.get("content-type", "").lower():
            raise ValueError("non_html")
        soup = BeautifulSoup(response.text, "html.parser")
        base_host = host(response.url)
        links = []
        profile_links = []
        for anchor in soup.find_all("a", href=True):
            target = urljoin(response.url, anchor["href"])
            signal = anchor.get_text(" ", strip=True) + " " + target
            if host(target) == base_host and CONTACT_RE.search(signal) and not NOISE_RE.search(signal):
                links.append(target.split("#", 1)[0])
            if host(target) == base_host and PROFILE_RE.search(signal) and not NOISE_RE.search(signal):
                profile_links.append(target.split("#", 1)[0])
        links = list(dict.fromkeys(links))
        profile_links = list(dict.fromkeys(profile_links))[:4]
        profile_text = soup.get_text(" ", strip=True)
        confirmed_url = response.url
        for profile_url in profile_links:
            try:
                profile_response = requests.get(profile_url, headers=HEADERS, timeout=16, allow_redirects=True)
                if profile_response.ok and "html" in profile_response.headers.get("content-type", "").lower():
                    candidate_text = BeautifulSoup(profile_response.text, "html.parser").get_text(" ", strip=True)
                    profile_text += " " + candidate_text
                    if company_key(row["company_name"]) in company_key(candidate_text):
                        confirmed_url = profile_response.url
                        break
            except requests.RequestException:
                pass
        confirmed = company_key(row["company_name"]) in company_key(profile_text)
        return {**row, "url": response.url, "contact_url": links[0] if links else "", "profile_url": confirmed_url, "company_confirmed": "yes" if confirmed else "no", "fetch": "ok"}
    except Exception as exc:
        return {**row, "contact_url": "", "profile_url": "", "company_confirmed": "no", "fetch": type(exc).__name__}


def main() -> None:
    response = requests.get(SOURCE, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for h3 in soup.find_all("h3"):
        card = h3.parent
        text = card.get_text(" ", strip=True)
        name = h3.get_text(" ", strip=True)
        url_match = re.search(r"URL\s+(https?://\S+)", text)
        phone_match = re.search(r"TEL\s+([^F]+?)(?:\s+FAX|\s+URL)", text)
        business_match = re.search(r"事業内容\s+(.+?)(?:\s+(?:Web|DM|求人|印刷|映像|イベント|PR|東京|大阪|愛知|神奈川|千葉|埼玉|北海道|福岡)\b|$)", text)
        if not url_match or not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        official_url = url_match.group(1).rstrip(".,）)")
        evidence = (business_match.group(1) if business_match else text.split("事業内容", 1)[-1])[:180]
        rows.append({
            "company_name": name,
            "url": official_url,
            "address": re.sub(r"^.*?所在地\s*", "", text).split(" TEL ", 1)[0][:180],
            "phone": phone_match.group(1).strip() if phone_match else "",
            "contact_url": "",
            "区分": "S｜地域広告・販促・Web・クリエイティブ支援",
            "検出ワード": "広告業協同組合公式会員：" + evidence,
            "source_url": SOURCE,
        })
    unique = {host(row["url"]): row for row in rows if host(row["url"])}
    results = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    output = HERE / "aca_crawled.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({"parsed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "output": str(output)})


if __name__ == "__main__":
    main()
