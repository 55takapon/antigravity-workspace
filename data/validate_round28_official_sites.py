import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


SERVICE_WORDS = (
    "広告",
    "マーケティング",
    "プロモーション",
    "販促",
    "web",
    "デジタル",
    "sns",
    "ブランディング",
)
LINK_WORDS = (
    "会社",
    "企業",
    "about",
    "company",
    "service",
    "事業",
    "業務",
    "contact",
    "問い合わせ",
)
EXCLUDE_NAMES = {
    "Omnicom Content Experiences 株式会社",
    "廣告社株式会社",
    "株式会社ADKマーケティング・ソリューションズ",
    "株式会社 九州博報堂",
    "株式会社 大広九州",
    "株式会社 東急エージェンシー",
    "株式会社 電通九州",
    "株式会社創文",
    "株式会社北海道博報堂",
}
CORE_NO_CONTACT = {
    "株式会社 大広九州",
    "株式会社 東急エージェンシー",
    "株式会社東急エージェンシー",
}


def digits(value):
    return re.sub(r"\D", "", value or "")


def fetch(session, url):
    response = session.get(
        url,
        timeout=25,
        headers={"User-Agent": "Mozilla/5.0 (compatible; research/1.0)"},
        allow_redirects=True,
    )
    response.raise_for_status()
    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding
    return response.url, BeautifulSoup(response.text, "html.parser")


def validate(record):
    session = requests.Session()
    pages = []
    errors = []
    try:
        final_url, soup = fetch(session, record["url"])
        pages.append((final_url, soup))
    except Exception as exc:
        return {**record, "reachable": False, "error": str(exc)}

    host = urlparse(final_url).netloc.lower().removeprefix("www.")
    links = []
    for link in soup.find_all("a", href=True):
        label = (link.get_text(" ", strip=True) + " " + link["href"]).lower()
        target = urljoin(final_url, link["href"]).split("#", 1)[0]
        target_host = urlparse(target).netloc.lower().removeprefix("www.")
        if (
            target.startswith(("http://", "https://"))
            and target_host == host
            and any(word in label for word in LINK_WORDS)
            and target not in links
        ):
            links.append(target)
    for target in links[:8]:
        try:
            pages.append(fetch(session, target))
        except Exception as exc:
            errors.append(f"{target}: {exc}")

    combined = "\n".join(
        page.get_text(" ", strip=True).lower() for _, page in pages
    )
    service_hits = [word for word in SERVICE_WORDS if word in combined]
    postal = re.search(r"\d{3}-\d{4}", record["address"])
    phone = digits(record["phone"])
    address_match = bool(postal and postal.group(0) in combined)
    phone_match = bool(phone and phone in digits(combined))
    contact_urls = sorted(
        {
            url
            for url, _ in pages
            if any(word in url.lower() for word in ("contact", "inquiry", "toiawase"))
        }
    )
    return {
        **record,
        "reachable": True,
        "final_url": final_url,
        "service_hits": service_hits,
        "address_match": address_match,
        "phone_match": phone_match,
        "contact_urls": contact_urls,
        "pages_checked": len(pages),
        "errors": errors,
    }


def main():
    if "--from-cache" in sys.argv:
        with open(
            "data/agent_round28_official_validation.json",
            encoding="utf-8",
        ) as handle:
            results = json.load(handle)
    else:
        with open(
            "data/agent_round28_regional_ad_associations_prefiltered.csv",
            encoding="utf-8-sig",
        ) as handle:
            records = list(csv.DictReader(handle))
        results = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(validate, record): record for record in records}
            for future in as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda item: item["company_name"])
        with open(
            "data/agent_round28_official_validation.json",
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(results, handle, ensure_ascii=False, indent=2)
    selected = []
    for result in results:
        if result["company_name"] in EXCLUDE_NAMES | CORE_NO_CONTACT:
            continue
        if not result.get("reachable") or not result.get("service_hits"):
            continue
        if not (result.get("address_match") or result.get("phone_match")):
            continue
        selected.append({key: result.get(key, "") for key in (
            "company_name", "url", "address", "phone", "maps_url", "status"
        )})
    for record in selected:
        if record["company_name"] == "株式会社ピーアールセンター":
            record["address"] = "〒060-0001 北海道札幌市中央区北1条西8丁目2-8 ピーアールセンタービル"
    with open(
        "data/agent_round28_regional_ad_associations.csv",
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["company_name", "url", "address", "phone", "maps_url", "status"],
        )
        writer.writeheader()
        writer.writerows(selected)
    print(f"selected={len(selected)}")
    for result in results:
        print(
            result["company_name"],
            f"reachable={result.get('reachable')}",
            f"services={','.join(result.get('service_hits', []))}",
            f"address={result.get('address_match')}",
            f"phone={result.get('phone_match')}",
            f"contact={len(result.get('contact_urls', []))}",
        )


if __name__ == "__main__":
    main()
