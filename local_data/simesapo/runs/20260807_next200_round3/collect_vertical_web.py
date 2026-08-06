from __future__ import annotations

import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import HEADERS, discover, host
from collect_interior import legal_name

SOURCE_URLS = [
    "https://clinic.z-it.jp/", "https://dental-web.jp/", "https://clinic-promotion.com/",
    "https://www.clinic-seoplus.com/", "https://salone-web.com/", "https://medical-grits.jp/",
    "https://terrapocket.jp/", "https://www.nakachi.net/index.html", "https://www.salon-hp.com/",
    "https://www.doctorsupportnet.jp/business/clinic_homepage_production/", "https://shika-pro.jp/hp-seisaku",
    "https://www.medico-consulting.jp/", "https://bau-marketing.jp/", "https://kotsukotsu-web.com/",
    "https://clinic-mkt.com/", "https://seikotsuinweb.com/", "https://www.seitai-homepage.com/",
    "https://healthwebcreations.com/", "https://seikotu-hp.com/", "https://halope.co.jp/halope-web.html",
    "https://laollc.com/", "https://cantik.co.jp/seitai/", "https://www.honepage.com/", "https://clinic-yell.jp/",
    "https://www.easy-juku.com/", "https://sougiya.jp/", "https://www.cramschool-hp.com/",
    "https://www.kaitokukenbi.net/", "https://e-cre.jp/web-seo/", "https://www.interlink.jp/",
    "https://www.basic-web.co.jp/service/promotion/", "https://www.jukusite.pro/", "https://connectai.co.jp/",
    "https://www.hap-worth.com/", "https://www.souki-inc.co.jp/hp/dental/",
    "https://www.method-innovation.co.jp/", "https://lp-hp.koko-design.com/", "https://chiryo-ma.co.jp/service-hp/",
    "https://shukyaku-chiryoin.jp/", "https://www.jok-inc.com/", "https://cp-dental.cp-cms.com/",
    "https://www.reewa-web.jp/", "https://graciauto.jp/services/salon-hp",
    "https://sanwayd.com/", "https://yadobee.jp/", "https://ys-link.co.jp/", "https://gymcloud.jp/webstudio/",
    "https://www.i-o-s.co.jp/", "https://food-site.jp/", "https://gourmet.z-it.jp/",
    "https://yuumoo.co.jp/personal-gym/", "https://hotelbusiness.info/",
    "https://prime-concept.co.jp/service/yoyaku.php", "https://www.adgraphy.jp/", "https://www.yadoraku.co.jp/",
    "https://www.pagepro.jp/", "https://shigyo-web.jp/", "https://www.fudoukun.jp/", "https://www.deep-deep.jp/",
    "https://reblo.jp/", "https://good-up.co.jp/", "https://www.datalyze.co.jp/project/website/pagepro/",
    "https://www.heyaweb.jp/", "https://www.j-s-p.com/", "https://shigyou.jp/", "https://www.fudoukun.com/",
    "https://kaigo-qol.com/",
    "https://matoka.co.jp/", "https://hoiku-design.com/", "https://relight-consulting.com/web-marketing/",
    "https://en-hoiku.com/", "https://fukuya-fs.com/", "https://fluke-inc.jp/fluke-gourmet-for-shop/",
    "https://tenage.group/service/", "https://media-hack.co.jp/", "https://withteam.jp/gourmet/",
    "https://miranekodesign.com/", "https://www.iplus-web.co.jp/", "https://www.dental-styleinc.com/",
    "https://hatakeyama-kikaku.co.jp/", "https://www.ast-web.com/lp/animal_hospital/", "https://ah-navi.com/",
    "https://hplus.jp/", "https://lismotech.co.jp/",
]
HERE = Path(__file__).parent
RAW = HERE / "vertical_web_raw.csv"
SEED = HERE / "vertical_web_seed.csv"
PROFILE_RE = re.compile(r"会社概要|企業情報|会社情報|運営会社|法人概要|about(?:us)?|company|corporate|profile", re.I)
LEGAL_RE = re.compile(
    r"(?:株式会社|有限会社|合同会社)\s*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+"
    r"|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+\s*(?:株式会社|有限会社|合同会社)"
)


def fetch(url: str) -> tuple[str, BeautifulSoup]:
    response = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.url, BeautifulSoup(response.text, "html.parser")


def find_company_and_text(url: str) -> tuple[str, str, str]:
    final_url, page = fetch(url)
    pages = [(final_url, page)]
    for link in page.select("a[href]"):
        href = urljoin(final_url, link.get("href", ""))
        signal = link.get_text(" ", strip=True) + " " + href
        if host(href) == host(final_url) and PROFILE_RE.search(signal):
            try:
                pages.append(fetch(href))
            except Exception:
                pass
            if len(pages) >= 6:
                break
    combined = " ".join(soup.get_text(" ", strip=True) for _, soup in pages)
    candidates: list[str] = []
    for _, soup in pages[1:] + pages[:1]:
        for match in LEGAL_RE.finditer(soup.get_text(" ", strip=True)):
            name = legal_name(match.group(0).strip())
            if 4 <= len(name) <= 45 and not re.search(r"お客様|制作|運営|設立|代表|所在地", name):
                candidates.append(name)
    name = candidates[0] if candidates else ""
    return name, final_url, combined


def validate(url: str) -> dict[str, str] | None:
    try:
        name, final_url, text = find_company_and_text(url)
    except Exception:
        return None
    if not name:
        return None
    target_groups = {
        "medical": ["医院", "クリニック", "歯科", "医療機関"],
        "beauty": ["美容室", "美容院", "サロン"],
        "clinic": ["整骨院", "接骨院", "整体院", "鍼灸院", "治療院"],
        "pet": ["動物病院", "ペットサロン"],
        "hotel": ["旅館", "ホテル", "宿泊施設"],
        "restaurant": ["飲食店", "レストラン", "居酒屋", "カフェ"],
        "fitness": ["フィットネス", "パーソナルジム", "ピラティス", "ヨガスタジオ"],
        "realestate": ["不動産会社", "不動産業者"],
        "professional": ["士業", "税理士", "弁護士", "司法書士", "行政書士", "社会保険労務士"],
        "care": ["介護事業", "介護施設", "福祉事業"],
        "childcare": ["保育園", "幼稚園", "認定こども園", "学童保育"],
    }
    matched = next((key for key, words in target_groups.items() if any(word in text for word in words)), "")
    support = [word for word in ["集客", "集患", "ホームページ", "Web", "WEB", "広告", "運用", "SEO", "MEO", "Googleマップ", "LINE"] if word in text]
    continuous = any(word in text for word in ["継続", "運用", "保守", "公開後", "アフターフォロー", "伴走", "月額"])
    if not (matched and len(support) >= 3 and continuous):
        return None
    label = {
        "medical": "医科・歯科", "beauty": "美容室・サロン", "clinic": "治療院",
        "pet": "動物病院・ペットサロン", "hotel": "旅館・ホテル", "restaurant": "飲食店",
        "fitness": "フィットネス", "realestate": "不動産会社", "professional": "士業", "care": "介護・福祉",
        "childcare": "保育園・幼稚園",
    }[matched]
    row = {
        "company_name": name, "url": final_url, "address": "", "phone": "", "contact_url": "",
        "区分": f"S｜{label}特化Web・集客支援",
        "検出ワード": f"{label}顧客＋Web集客＋公開後運用支援",
        "source_url": url,
    }
    result = discover(row)
    result["affinity_evidence"] = "+".join(support[:6])
    return result


results: list[dict[str, str]] = []
with ThreadPoolExecutor(max_workers=12) as pool:
    futures = [pool.submit(validate, url) for url in SOURCE_URLS]
    for future in as_completed(futures):
        result = future.result()
        if result:
            results.append(result)
results = list({host(row["url"]): row for row in results if host(row["url"])}.values())
results.sort(key=lambda row: row["company_name"])
if results:
    with RAW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader(); writer.writerows(results)
NAME_NOISE_RE = re.compile(r"会社名|会社概要|企業情報|法人概要|社名|住所|所在地|ご提供|ホームページ|Google|GOOGLE|店舗・|大阪の")
accepted = [
    row for row in results
    if row.get("company_confirmed") == "yes"
    and bool(row.get("contact_url"))
    and not NAME_NOISE_RE.search(row.get("company_name", ""))
]
fields = ["company_name", "url", "address", "phone", "contact_url", "区分", "検出ワード", "source_url"]
with SEED.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
    writer.writeheader(); writer.writerows(accepted)
print({"source_urls": len(SOURCE_URLS), "affinity_found": len(results), "all_gates": len(accepted), "seed": str(SEED)})
