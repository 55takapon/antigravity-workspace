import csv
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = ["company_name", "url", "address", "phone", "maps_url", "status"]
HAAA_NAME_FIXES = {
    "（株）ADKマーケティング・ソリューションズ 北海道支社": "株式会社ADKマーケティング・ソリューションズ",
    "（株）朝日サービス": "株式会社朝日サービス",
    "（株）アド・ビュ一ロ一岩泉": "株式会社アド・ビューロー岩泉",
    "（株）えんれいしゃ": "株式会社えんれいしゃ",
    "廣告社（株）札幌支社": "廣告社株式会社",
    "（株）サンライズ社札幌支店": "株式会社サンライズ社",
    "（株）創文": "株式会社創文",
    "（株）東急エ一ジェンシ一 北海道支社": "株式会社東急エージェンシー",
    "（株）道新サ一ビスセン夕一": "株式会社道新サービスセンター",
    "（株）バリオン": "株式会社バリオン",
    "（株）ピ一ア一ルセン夕一": "株式会社ピーアールセンター",
    "（株）北海道朝日広告社": "株式会社北海道朝日広告社",
    "（株）北海道博報堂": "株式会社北海道博報堂",
    "（株）北海道毎日サ一ビス": "株式会社北海道毎日サービス",
}


def clean(value):
    return re.sub(r"\s+", " ", value).strip()


def fetch(url, encoding=None):
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    if encoding:
        response.encoding = encoding
    return BeautifulSoup(response.text, "html.parser")


def parse_haaa():
    soup = fetch("https://haaa.or.jp/member.html", "utf-8")
    rows = []
    tables = soup.select("table.table-01.ma_top50")
    # The first table is the 30 full advertising-agency members.
    for tr in tables[0].select("tr"):
        cells = tr.find_all("td")
        if len(cells) != 2:
            continue
        link = cells[0].find("a", href=True)
        if not link:
            continue
        company = clean(cells[0].get_text(" ", strip=True))
        company = HAAA_NAME_FIXES.get(company, company)
        detail = clean(cells[1].get_text(" ", strip=True))
        phone_match = re.search(r"TEL[：:]\s*([0-9()\-]+)", detail)
        address = re.split(r"TEL[：:]", detail, maxsplit=1)[0].strip()
        rows.append(
            {
                "company_name": company,
                "url": urljoin("https://haaa.or.jp/member.html", link["href"]),
                "address": address,
                "phone": phone_match.group(1) if phone_match else "",
                "maps_url": "",
                "status": "",
            }
        )
    return rows


def parse_kyu():
    soup = fetch("https://kyu-aaa.jp/members/", "utf-8")
    rows = []
    heading = next(
        h for h in soup.find_all(["h2", "h3"]) if "会員一覧" in clean(h.get_text())
    )
    for link in heading.find_all_next("a", href=True):
        if "JAAA日本広告業協会" in clean(link.get_text()):
            break
        if link["href"].lower().startswith("tel:"):
            continue
        company = clean(link.get_text(" ", strip=True))
        if not company or company in {"Facebookページ"}:
            continue
        parent = link.find_parent("li")
        if not parent:
            continue
        detail = clean(parent.get_text(" ", strip=True))
        phone_match = re.search(r"Tel\.\s*([0-9\-]+)", detail, re.I)
        address_match = re.search(r"(〒\d{3}-\d{4}.+?)(?:Tel\.|$)", detail, re.I)
        rows.append(
            {
                "company_name": company,
                "url": urljoin("https://kyu-aaa.jp/members/", link["href"]),
                "address": clean(address_match.group(1)) if address_match else "",
                "phone": phone_match.group(1) if phone_match else "",
                "maps_url": "",
                "status": "",
            }
        )
    return rows


def main():
    records = parse_haaa() + parse_kyu()
    seen = set()
    unique = []
    for record in records:
        key = record["url"].rstrip("/").lower()
        if key not in seen:
            seen.add(key)
            unique.append(record)
    with open(
        "data/agent_round28_regional_ad_associations_raw.csv",
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(unique)
    print(f"wrote={len(unique)}")


if __name__ == "__main__":
    main()
