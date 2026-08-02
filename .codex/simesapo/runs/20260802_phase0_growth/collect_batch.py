from __future__ import annotations

import argparse
import base64
import csv
import html
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
sys.path.insert(0, str(SKILL / ".codex_pydeps"))
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
TARGET = "シート1"
MASTER = SKILL / "custmize" / "enterprise_filter"
HERE = Path(__file__).parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/127 Safari/537.36"

SEGMENTS = {
    "beauty": {
        "label": "美容室・サロン",
        "evidence": ["美容室", "美容院", "理美容", "ヘアサロン", "美容サロン", "エステサロン", "ネイルサロン", "まつげ", "アイラッシュ", "サロン集客"],
        "seeds": [
            "https://staxia.jp/marketing/beauty-salon-homepage-company/", "https://yuryoweb.com/recommended/beauty-salon/",
            "https://www.webclimb.co.jp/hp-biyousitsu/", "https://hnavi.co.jp/knowledge/blog/beauty-hp_companies/",
            "https://saisia.co.jp/services/web-production/beauty/hp-companies/", "https://salone-web.com/", "https://www.pro-salon.jp/prosalon/01.html",
            "https://www.suma-one.jp/", "https://zhibo.jp/", "https://terrapocket.jp/", "https://orange-japan.com/",
            "https://www.nakachi.net/", "https://www.salon-chirashiwork.com/", "https://beaust.jp/", "https://salon-hack.com/",
            "https://graciauto.jp/", "https://www.misepage.com/", "https://www.ifine.jp/", "https://salon-web.com/",
            "https://www.belcom.co.jp/salon/", "https://www.salon-hp.com/", "https://hako.salon/", "https://webextend.me/",
            "https://imuzen.com/", "https://www.styledesigner.net/", "https://partners.barberin.jp/", "https://salonsupport.waytogo.co.jp/",
            "https://uni-design.tokyo/", "https://www.salons-promo.com/", "https://www.pccinc.jp/", "https://www.sales-dx.jp/service/beauty-salon",
            "https://nex-i.net/", "https://www.cielo-marketing.com/", "https://sbmconsul.co.jp/esthetic-salon/", "https://gicp.co.jp/consulting/esthe/",
            "https://splice-web.com/", "https://ddm-cosmo.com/service/industry-top/beauty-salon/", "https://www.beau-tech.jp/business",
            "https://esthe-consulting.com/menu/marketing/", "https://xeno-st.co.jp/", "https://cyberzero.jp/", "https://www.w-stage.jp/service_set/salon/",
            "https://kwin.co.jp/service/",
            "https://salon-support.miravis.co.jp/", "https://salonmarugoto.jp/", "https://four-design.co.jp/", "https://yuizum.com/",
            "https://webmarketing.dxup.jp/", "https://amandine.co.jp/", "https://aim-ag.com/", "https://salon-plus-gpj.com/plan",
            "https://salonboardagency.com/", "https://meo-salon.jp/", "https://hitokoto.tokyo/", "https://fe-mo.co.jp/attracting_customers/",
            "https://salotas.com/", "https://beauty-network-media.com/", "https://www.teamflatworks.jp/industry/beauty",
            "https://www.eyesta.com/", "https://www.mediaselect.jp/work.html", "https://www.beeline-inc.co.jp/", "https://salon-rescue.com/",
            "https://linyforsalon.waytogo.co.jp/", "https://www.line100.com/", "https://in-line.jp/line/", "https://jei-one.co.jp/service/line.html",
            "https://www.esprit-net.jp/", "https://ractory.co.jp/line/", "https://www.seineline.com/solution/line.html", "https://liibe.co.jp/line/",
            "https://www.hp-nagoya.com/", "https://salon-hansoku.com/works/", "https://www.mag-net.co.jp/works/", "https://mecreate.co.jp/hair-salon/",
            "https://medi-cro.jp/results/hair/", "https://alive-web.co.jp/workscat/beauty/", "https://www.spd-inc.jp/works-business/beauty-health/",
            "https://www.mqe.jp/works/web/", "https://aigis.co.jp/results/support/the-barbershop%E3%80%90ties%E3%80%91", "https://www.zoddo.info/product/",
            "https://www.nishikiweb.jp/project/hair-salon-homepage-production-results/", "https://www.macaya.jp/hp/works/", "https://www.aisalo-hp.com/work",
            "https://www.jevat.com/0w_hp_ref.html", "https://www.bright-art.com/", "https://web-gmm.com/achievements/", "https://ace214.com/web/works/",
            "https://g-conure-works.com/portfolio/product/product5/", "https://clear-salonhp.jp/works/", "https://www.e-compass.ne.jp/web/works/000108/",
            "https://www.recruit-beauty.jp/", "https://hairsalon.homepaging.jp/design/works", "https://xstudio.co.jp/works/", "https://homepage.hyogo.jp/",
            "https://sapporo-webstudio.jp/", "https://xn--yck7ccu3lc4264ce4ay1qdwe.net/works", "https://miyabi-design-office.com/works/works.html",
            "https://kamu-design.com/hairsalon-egao-20241099/", "https://muu-tech.co/", "https://shikiori.com/works/", "https://gggggggg.jp/works",
            "https://lelien-design.com/", "http://www.kurinet.co.jp/hcm/", "https://attlabo.com/business/salon/", "https://sociola.co.jp/works/hairsalon/",
            "https://yokohama-design.jp/works/832/", "https://saloncms.com/", "https://www.salons-promo.com/work", "https://andcre.com/portfolio/?category=web-development",
            "https://img-a.jp/", "https://www.tratto-brain.jp/works/genre_salon.html", "https://mizuho-factory.com/works_laterre/",
            "https://www.jbl-tachikawa.co.jp/support/", "https://web.k-art-factory.jp/", "https://www.crea-d.com/service/create/",
            "https://www.medico-consulting.jp/beauty.html", "https://www.beautygarage.jp/topics/solution", "http://salon-market.jp/design.html",
            "https://kamishima-beauty.com/service/support/", "https://www.kikuya-bisyodo.co.jp/column/newdeal/", "https://fujisangyou-beauty.com/about_us/",
            "https://ysb-create.com/1/", "https://beauty.spiqa.design/", "https://www.adva.jp/open", "https://www.mitsui-corp.co.jp/support/design/",
            "https://fukuyama-world-biyou.net/", "https://www.amyth-beauty.com/service.html", "https://bmade-office.com/service/",
            "https://salon-kaigyou.com/support/biyousitsu-homepage", "https://www.beautyshopplus.com/reason", "https://www.one-clue.com/hairsalon_support/",
            "https://www.maia-bsd.jp/business/", "https://www.e-hanabusa.com/", "https://vibon.jp/service02.html", "https://fe-mo.co.jp/web_design/",
            "https://www.adva.jp/sales", "https://ao-design-salon.com/", "https://www.eyelashgarage.jp/",
        ],
        "queries": [
            "美容室 サロン 専門 ホームページ制作 会社", "美容院 集客 Web制作 サロン 専門 会社",
            "エステサロン 専門 ホームページ制作 会社", "美容室 サロン Webマーケティング 支援 会社",
            "美容室 ホームページ制作 専門 東京", "美容室 ホームページ制作 専門 大阪",
            "美容室 ホームページ制作 専門 名古屋", "美容室 ホームページ制作 専門 福岡",
            "ネイル アイラッシュ サロン ホームページ制作", "理美容室 ホームページ制作 集客支援",
            "美容業界 Web制作 ブランディング 会社", "美容室 SNS運用 集客支援 会社",
            "エステサロン Web集客 コンサルティング 制作会社", "サロン 開業支援 ホームページ制作 会社",
            "美容室 求人サイト 制作 会社", "美容サロン LP制作 集客 会社",
            "ホットペッパー 運用代行 美容室 会社", "美容業界 デジタルマーケティング 支援 会社",
            "美容室 販促 デザイン ホームページ 会社", "サロン専門 MEO Web制作 会社",
        ],
    },
    "food": {
        "label": "飲食店",
        "evidence": ["飲食店", "レストラン", "居酒屋", "カフェ", "外食", "フードビジネス", "飲食業界", "店舗集客"],
        "queries": [
            "飲食店 専門 ホームページ制作 会社", "レストラン Web制作 集客支援 会社", "居酒屋 ホームページ制作 専門",
            "飲食業界 Webマーケティング 支援 会社", "飲食店 ホームページ制作 東京", "飲食店 ホームページ制作 大阪",
            "飲食店 ホームページ制作 名古屋", "飲食店 ホームページ制作 福岡", "カフェ ホームページ制作 集客 会社",
            "外食産業 ブランディング Web制作", "飲食店 SNS運用 集客支援 会社", "飲食店 開業支援 Web制作 会社",
            "飲食店 販促 デザイン 制作会社", "飲食店 求人サイト 制作 会社", "飲食店 EC テイクアウト Web制作",
            "飲食店 MEO ホームページ制作 会社", "飲食店 集客コンサルティング Web", "レストラン ブランディング デザイン会社",
            "フードビジネス デジタルマーケティング 会社", "飲食店 多店舗 Web運用 支援会社",
        ],
    },
    "hotel": {
        "label": "旅館・ホテル・観光",
        "evidence": ["旅館", "ホテル", "宿泊施設", "観光", "温泉", "リゾート", "宿泊業", "インバウンド"],
        "queries": [
            "旅館 ホテル 専門 ホームページ制作 会社", "宿泊施設 Web制作 集客支援 会社", "ホテル Webマーケティング 会社",
            "旅館 ホームページ制作 東京", "旅館 ホームページ制作 大阪", "ホテル ホームページ制作 京都",
            "宿泊施設 ホームページ制作 九州", "観光業 Web制作 支援会社", "ホテル 旅館 SNS運用 会社",
            "宿泊施設 予約サイト 制作会社", "旅館 集客コンサルティング Web", "ホテル ブランディング Web制作",
            "観光 インバウンド デジタルマーケティング 会社", "温泉旅館 ホームページ リニューアル 制作会社",
            "宿泊業 DX Web集客 支援会社", "ホテル MEO ホームページ制作", "観光施設 ホームページ制作 会社",
            "旅館 販促 デザイン 制作会社", "ホテル 多言語サイト 制作会社", "宿泊施設 OTA 運用代行 会社",
        ],
    },
    "realestate": {
        "label": "不動産",
        "evidence": ["不動産会社", "不動産業", "不動産業界", "賃貸", "売買仲介", "住宅会社", "物件", "不動産集客"],
        "queries": [
            "不動産会社 専門 ホームページ制作 会社", "不動産 Web制作 集客支援 会社", "不動産業界 Webマーケティング 会社",
            "不動産 ホームページ制作 東京", "不動産 ホームページ制作 大阪", "不動産 ホームページ制作 名古屋",
            "不動産 ホームページ制作 福岡", "賃貸 仲介 ホームページ制作 会社", "不動産 SNS運用 集客支援",
            "不動産 ポータル 連動 ホームページ制作", "不動産 ブランディング Web制作", "不動産会社 MEO Web集客",
            "不動産 DX マーケティング 支援会社", "不動産 販促 デザイン 制作会社", "住宅 不動産 Webコンサルティング",
            "不動産 採用サイト 制作会社", "不動産 LP制作 広告運用 会社", "地域不動産 ホームページ制作 専門",
            "不動産 物件管理 システム ホームページ", "不動産会社 集客コンサルティング Web",
        ],
    },
    "construction": {
        "label": "建築・工務店・リフォーム",
        "evidence": ["工務店", "建築会社", "住宅会社", "リフォーム会社", "ハウスメーカー", "住宅業界", "建設業", "施工会社"],
        "queries": [
            "工務店 専門 ホームページ制作 会社", "建築会社 Web制作 集客支援 会社", "リフォーム会社 ホームページ制作 専門",
            "工務店 ホームページ制作 東京", "工務店 ホームページ制作 大阪", "工務店 ホームページ制作 名古屋",
            "工務店 ホームページ制作 福岡", "住宅業界 Webマーケティング 支援会社", "建築 リフォーム SNS運用 会社",
            "工務店 集客コンサルティング Web", "住宅会社 ブランディング Web制作", "建設業 ホームページ制作 会社",
            "工務店 MEO Web集客", "リフォーム会社 広告運用 LP制作", "住宅業界 販促 デザイン会社",
            "工務店 採用サイト 制作会社", "地域工務店 ホームページ制作 専門", "建築会社 デジタルマーケティング",
            "住宅会社 Web運用 支援会社", "工務店 集客代行 会社",
        ],
    },
}

DENY_HOSTS = {
    "google.com", "youtube.com", "facebook.com", "instagram.com", "x.com", "twitter.com", "linkedin.com",
    "prtimes.jp", "wantedly.com", "indeed.com", "mynavi.jp", "doda.jp", "wikipedia.org", "note.com",
    "imitsu.jp", "web-kanji.com", "comparakeit.com", "houjin.jp", "baseconnect.in", "mapion.co.jp",
    "amazon.co.jp", "rakuten.co.jp", "beauty.hotpepper.jp", "jfc.go.jp", "go.jp", "lg.jp",
    "hnavi.co.jp", "staxia.jp", "yuryoweb.com", "webclimb.co.jp", "saisia.co.jp", "thinkbal.co.jp",
    "stock-sun.com", "webdeki.com", "biz.ne.jp", "shopowner-support.net", "cachica.co.jp", "web-kanji.com",
    "quantaxis.jp", "wepage.com", "jiji.com", "fnn.jp", "newscast.jp", "compalyze.co.jp", "zelvia.co.jp",
}

CORP_RE = re.compile(r"(?:株式会社|有限会社|合同会社|合資会社|合名会社)[\s　]*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥々ぁ-んァ-ヶー・･&＆.．\-]{1,36}|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥々ぁ-んァ-ヶー・･&＆.．\-]{1,36}[\s　]*(?:株式会社|有限会社|合同会社|合資会社|合名会社)")
CONTACT_WORDS = ("お問い合わせ", "お問合せ", "問い合わせ", "contact", "inquiry", "ご相談", "無料相談", "資料請求")
COMPANY_WORDS = ("会社概要", "企業情報", "運営会社", "会社案内", "about", "company", "profile")
WEB_WORDS = ("ホームページ制作", "web制作", "ウェブ制作", "サイト制作", "webサイト", "集客支援", "マーケティング", "広告運用", "sns運用", "ブランディング", "開業支援", "開業サポート", "経営支援", "経営サポート", "予約システム", "予約管理", "pos", "モバイルオーダー", "注文システム", "顧客管理", "販促支援", "店舗支援", "店舗運営", "dx支援", "建設dx", "住宅dx", "施工管理", "工程管理", "現場管理", "営業支援", "業務支援", "業務効率化", "マッチング", "saas", "クラウド", "コンサルティング")
PROHIBIT_PATTERNS = [
    re.compile(p, re.I) for p in [
        r"営業(?:目的|活動|メール|の)?[^。]{0,18}(?:お断り|禁止|ご遠慮)",
        r"売り込み[^。]{0,18}(?:お断り|禁止|ご遠慮)",
        r"セールス[^。]{0,18}(?:お断り|禁止|ご遠慮)",
        r"営業・勧誘[^。]{0,18}(?:お断り|禁止|ご遠慮)",
    ]
]
CONTACT_OVERRIDES = {
    "fe-mo.co.jp": "https://fe-mo.co.jp/contact/",
}


def norm(v: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", v or "").lower())


def company_key(v: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|合資会社|合名会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:：\-]", "", norm(v))


def host_key(v: str) -> str:
    h = urlparse(v if "://" in (v or "") else "https://" + (v or "")).hostname or ""
    return re.sub(r"^www\.", "", h.lower()).rstrip(".")


def phone_key(v: str) -> str:
    return re.sub(r"\D", "", v or "")


def registrableish(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2:] in [["co", "jp"], ["ne", "jp"], ["or", "jp"]]:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def denied(host: str) -> bool:
    h = host_key(host)
    return any(h == d or h.endswith("." + d) for d in DENY_HOSTS)


def get(url: str, timeout: int = 8):
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.7"}, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400 or not r.text:
            return None
        ctype = r.headers.get("content-type", "")
        if "html" not in ctype and "xhtml" not in ctype:
            return None
        r.encoding = r.apparent_encoding or r.encoding
        return r
    except requests.RequestException:
        return None


def google_search(query: str, pages: int = 2) -> list[str]:
    urls: list[str] = []
    for page in range(pages):
        u = f"https://www.bing.com/search?q={quote_plus(query)}&count=30&first={page*30+1}&setlang=ja-JP&mkt=ja-JP"
        r = get(u)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("li.b_algo h2 a[href]"):
            href = html.unescape(a.get("href", ""))
            if "bing.com/ck/a" in href:
                enc = parse_qs(urlparse(href).query).get("u", [""])[0]
                if enc.startswith("a1"):
                    try:
                        raw = enc[2:] + "=" * (-len(enc[2:]) % 4)
                        href = base64.urlsafe_b64decode(raw).decode("utf-8")
                    except Exception:
                        continue
            if not href.startswith("http"):
                continue
            h = host_key(href)
            if not h or h.endswith("google.com") or denied(h):
                continue
            if href not in urls:
                urls.append(href)
        time.sleep(0.8)
    return urls


def expand_external_links(seed_urls: list[str], evidence_words: list[str], limit: int = 500) -> list[str]:
    """Comparison/directory pages are discovery seeds only; returned links still pass the official-site audit."""
    out: list[str] = []
    seen = {host_key(x) for x in seed_urls}
    discovery_hosts = ("staxia.jp", "yuryoweb.com", "hnavi.co.jp", "saisia.co.jp", "webclimb.co.jp", "thinkbal.co.jp", "stock-sun.com", "webdeki.com", "biz.ne.jp", "shopowner-support.net", "cachica.co.jp", "web-kanji.com", "imitsu.jp", "quantaxis.jp", "wepage.com")
    for seed in seed_urls:
        if not any(host_key(seed) == h or host_key(seed).endswith("." + h) for h in discovery_hosts):
            continue
        r = get(seed)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        page_text = norm(soup.get_text(" ", strip=True))
        if not any(norm(w) in page_text for w in evidence_words):
            continue
        seed_root = registrableish(host_key(r.url))
        for a in soup.select("a[href]"):
            u = urljoin(r.url, a.get("href", "")).split("#")[0]
            h = host_key(u)
            if not u.startswith("http") or not h or denied(h) or registrableish(h) == seed_root or h in seen:
                continue
            label = norm(a.get_text(" ", strip=True))
            if len(label) < 2:
                continue
            seen.add(h); out.append(u)
            if len(out) >= limit:
                return out
    return out


def clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def links_by_words(soup: BeautifulSoup, base: str, words: tuple[str, ...]) -> list[str]:
    out = []
    root = registrableish(host_key(base))
    for a in soup.select("a[href]"):
        label = norm(a.get_text(" ", strip=True) + " " + a.get("href", ""))
        if not any(norm(w) in label for w in words):
            continue
        u = urljoin(base, a.get("href", "")).split("#")[0]
        if u.startswith("http") and registrableish(host_key(u)) == root and u not in out:
            out.append(u)
    return out


def extract_company(pages: list[tuple[str, BeautifulSoup]]) -> str:
    choices: list[tuple[int, str]] = []
    for url, soup in pages:
        is_company = any(w in norm(url) for w in COMPANY_WORDS)
        for obj in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(obj.string or "null")
                stack = data if isinstance(data, list) else [data]
                for x in stack:
                    if isinstance(x, dict) and str(x.get("@type", "")).lower() in {"organization", "corporation", "localbusiness"}:
                        name = str(x.get("name", "")).strip()
                        if CORP_RE.fullmatch(name):
                            choices.append((20 + is_company * 5, name))
            except Exception:
                pass
        for el in soup.select("title,h1,h2,h3,th,td,dt,dd,p,li,address"):
            t = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip(" |｜-–—")
            if not (2 <= len(t) <= 90):
                continue
            for m in CORP_RE.finditer(t):
                name = m.group(0).strip(" |｜-–—,:：")
                if len(company_key(name)) < 2:
                    continue
                score = (10 if is_company else 0) + (5 if len(t) <= 55 else 0) + (4 if t == name else 0)
                if any(k in norm(t) for k in ("会社名", "法人名", "運営会社", "社名")):
                    score += 8
                choices.append((score, name))
    if not choices:
        return ""
    choices.sort(key=lambda x: (-x[0], len(x[1])))
    name = choices[0][1]
    for marker in ("が選ばれる", "から株式会社", "設立", "様", "を支援する", "運営会社", "開発・運営"):
        if marker in name:
            return ""
    if re.match(r"^(?:by)?\s*株式会社$", name, re.I):
        return ""
    return name


def extract_phone(text: str) -> str:
    m = re.search(r"(?:TEL|電話|tel)[\s:：]*(0\d{1,4}[-‐ー−]\d{1,4}[-‐ー−]\d{3,4})", text, re.I)
    return m.group(1) if m else ""


def extract_address(text: str) -> str:
    m = re.search(r"〒?\s*\d{3}[-‐ー−]\d{4}\s*([^|｜]{3,80}?(?:都|道|府|県)[^|｜]{3,70})", text)
    return (m.group(0)[:100] if m else "").strip()


@dataclass
class Audit:
    decision: str
    company_name: str = ""
    url: str = ""
    contact_url: str = ""
    address: str = ""
    phone: str = ""
    evidence: str = ""
    reason: str = ""
    source_url: str = ""


def audit_site(found_url: str, evidence_words: list[str]) -> Audit:
    host = host_key(found_url)
    if not host or denied(host):
        return Audit("reject", reason="deny_domain", source_url=found_url)
    root_url = f"https://{host}/"
    first = get(found_url) or get(root_url)
    if not first:
        return Audit("reject", reason="fetch_failed", source_url=found_url)
    root_url = f"{urlparse(first.url).scheme}://{urlparse(first.url).netloc}/"
    soup0 = BeautifulSoup(first.text, "html.parser")
    text0 = clean_text(BeautifulSoup(first.text, "html.parser"))
    service_hit = next((w for w in evidence_words if norm(w) in norm(text0)), "")
    web_hit = next((w for w in WEB_WORDS if norm(w) in norm(text0)), "")
    pages: list[tuple[str, BeautifulSoup]] = [(first.url, soup0)]
    company_links = links_by_words(soup0, first.url, COMPANY_WORDS)[:3]
    contact_links = links_by_words(soup0, first.url, CONTACT_WORDS)[:5]
    for p in ("company/", "about/", "profile/", "corporate/", "company.html", "about.html"):
        u = urljoin(root_url, p)
        if u not in company_links:
            company_links.append(u)
    if not contact_links:
        contact_links = [urljoin(root_url, p) for p in ("contact/", "inquiry/", "form/", "contact.html")]
    for u in company_links[:6]:
        rr = get(u)
        if rr:
            pages.append((rr.url, BeautifulSoup(rr.text, "html.parser")))
    if not service_hit or not web_hit:
        for _, sp in pages[1:]:
            tx = clean_text(BeautifulSoup(str(sp), "html.parser"))
            service_hit = service_hit or next((w for w in evidence_words if norm(w) in norm(tx)), "")
            web_hit = web_hit or next((w for w in WEB_WORDS if norm(w) in norm(tx)), "")
    if not service_hit or not web_hit:
        return Audit("reject", url=root_url, reason="service_evidence_missing", source_url=first.url)
    company = extract_company(pages)
    if not company:
        return Audit("reject", url=root_url, reason="official_company_missing", source_url=first.url)
    contact_url = ""
    contact_text = ""
    for u in contact_links:
        rr = get(u)
        if not rr:
            continue
        tx = clean_text(BeautifulSoup(rr.text, "html.parser"))
        if any(x in norm(tx) for x in ("お問い合わせ", "お問合せ", "contact", "相談", "フォーム")):
            contact_url, contact_text = rr.url, tx
            break
    if not contact_url and registrableish(host_key(root_url)) in CONTACT_OVERRIDES:
        contact_url = CONTACT_OVERRIDES[registrableish(host_key(root_url))]
    if not contact_url:
        return Audit("reject", company, root_url, reason="contact_missing", source_url=first.url)
    all_text = " ".join(clean_text(BeautifulSoup(str(sp), "html.parser")) for _, sp in pages)
    return Audit("accept", company, root_url, contact_url, extract_address(all_text), extract_phone(all_text), f"{service_hit}／{web_hit}", source_url=first.url)


def read_live_master():
    client = sheets_io.get_client()
    book = client.open_by_url(SHEET)
    rows = []
    tab_counts = {}
    for ws in book.worksheets():
        values = ws.get_all_values()
        tab_counts[ws.title] = max(0, len(values) - 1)
        if not values:
            continue
        hdr = values[0]
        for vals in values[1:]:
            row = {hdr[i]: vals[i] if i < len(vals) else "" for i in range(len(hdr)) if hdr[i]}
            if vals:
                row.setdefault("company_name", vals[0])
            if len(vals) > 1:
                row.setdefault("url", vals[1])
            if len(vals) > 3:
                row.setdefault("phone", vals[3])
            rows.append(row)
    return rows, tab_counts


def load_enterprise_sets():
    confirmed = list(csv.DictReader((MASTER / "confirmed_enterprise_exclusions.csv").open(encoding="utf-8-sig", newline="")))
    allow = list(csv.DictReader((MASTER / "enterprise_false_positive_allowlist.csv").open(encoding="utf-8-sig", newline="")))
    jpx = list(csv.DictReader((MASTER / "jpx_listed_companies_20260630.csv").open(encoding="utf-8-sig", newline="")))
    rules = list(csv.DictReader((MASTER / "major_group_rules.csv").open(encoding="utf-8-sig", newline="")))
    confirmed_names = {company_key(r.get("company_name", "")) for r in confirmed}
    confirmed_domains = {host_key(r.get("url", "") or r.get("domain", "")) for r in confirmed if r.get("url", "") or r.get("domain", "")}
    allow_pairs = {(company_key(r.get("company_name", "")), host_key(r.get("url", "") or r.get("domain", ""))) for r in allow}
    jpx_names = {company_key(r.get("company_name", "") or r.get("name", "") or r.get("銘柄名", "")) for r in jpx}
    contains = [norm(r.get("match_value", "") or r.get("keyword", "") or r.get("判定語", "")) for r in rules]
    return confirmed_names, confirmed_domains, allow_pairs, jpx_names, [x for x in contains if x]


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segment", required=True, choices=SEGMENTS)
    ap.add_argument("--target", type=int, default=50)
    ap.add_argument("--search-pages", type=int, default=2)
    ap.add_argument("--skip-search", action="store_true")
    args = ap.parse_args()
    cfg = SEGMENTS[args.segment]
    outdir = HERE / args.segment
    outdir.mkdir(parents=True, exist_ok=True)
    live, tab_counts = read_live_master()
    live_names = {company_key(r.get("company_name", "")) for r in live if r.get("company_name")}
    live_domains = {host_key(r.get("url", "")) for r in live if r.get("url")}
    live_phones = {phone_key(r.get("phone", "")) for r in live if phone_key(r.get("phone", ""))}
    confirmed_names, confirmed_domains, allow_pairs, jpx_names, major_contains = load_enterprise_sets()
    found: list[str] = []
    for u in cfg.get("seeds", []):
        h = host_key(u)
        if h and h not in live_domains and h not in confirmed_domains and h not in {host_key(x) for x in found}:
            found.append(u)
    browser_seed_file = outdir / "browser_seed_urls.txt"
    if browser_seed_file.exists():
        for u in browser_seed_file.read_text(encoding="utf-8-sig").splitlines():
            u = u.strip()
            h = host_key(u)
            if h and not denied(h) and h not in live_domains and h not in confirmed_domains and h not in {host_key(x) for x in found}:
                found.append(u)
    query_stats = []
    for i, q in enumerate([] if args.skip_search else cfg["queries"], 1):
        urls = google_search(q, args.search_pages)
        before = len(found)
        for u in urls:
            h = host_key(u)
            if h not in {host_key(x) for x in found} and h not in live_domains and h not in confirmed_domains:
                found.append(u)
        query_stats.append({"query_no": i, "query": q, "results": len(urls), "new_domains": len(found)-before})
        print(json.dumps({"stage":"search", "segment":args.segment, "query":i, "found_domains":len(found)}, ensure_ascii=False), flush=True)
    expanded = expand_external_links(found, cfg["evidence"])
    for u in expanded:
        h = host_key(u)
        if h not in {host_key(x) for x in found} and h not in live_domains and h not in confirmed_domains:
            found.append(u)
    print(json.dumps({"stage":"expand", "segment":args.segment, "expanded":len(expanded), "found_domains":len(found)}, ensure_ascii=False), flush=True)
    audits = []
    accepted = []
    seen_names, seen_domains, seen_phones = set(), set(), set()
    audited_count = 0
    for offset in range(0, len(found), 25):
        chunk = found[offset:offset+25]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda u: audit_site(u, cfg["evidence"]), chunk))
        for a in results:
            audited_count += 1
            ck, dk, pk = company_key(a.company_name), host_key(a.url), phone_key(a.phone)
            if a.decision == "accept":
                if ck in live_names or dk in live_domains or (pk and pk in live_phones):
                    a.decision, a.reason = "reject", "live_duplicate"
                elif ck in seen_names or dk in seen_domains or (pk and pk in seen_phones):
                    a.decision, a.reason = "reject", "batch_duplicate"
                elif (ck, dk) not in allow_pairs and (ck in confirmed_names or dk in confirmed_domains):
                    a.decision, a.reason = "reject", "confirmed_enterprise"
                elif (ck, dk) not in allow_pairs and ck in jpx_names:
                    a.decision, a.reason = "review", "jpx_name_review"
                elif (ck, dk) not in allow_pairs and any(k in norm(a.company_name) for k in major_contains):
                    a.decision, a.reason = "review", "major_group_review"
                else:
                    seen_names.add(ck); seen_domains.add(dk)
                    if pk: seen_phones.add(pk)
                    accepted.append(a)
            audits.append(a.__dict__.copy())
            if len(accepted) >= args.target:
                break
        print(json.dumps({"stage":"audit", "segment":args.segment, "audited":audited_count, "accepted":len(accepted)}, ensure_ascii=False), flush=True)
        if len(accepted) >= args.target:
            break
    fields = list(Audit.__dataclass_fields__)
    write_csv(outdir / "audit_all.csv", audits, fields)
    final_rows = []
    for a in accepted[:args.target]:
        final_rows.append({
            "company_name": a.company_name, "url": a.url, "address": a.address, "phone": a.phone, "maps_url": "",
            "contact_url": a.contact_url, "message": "", "sent_at": "", "status": "", "error_reason": "",
            "screenshot_path": "", "provider_used": "", "提案区分": "", "": "", "区分": "S｜業界特化Web制作",
            "検出ワード": f"{cfg['label']}特化支援：{a.evidence}",
        })
    headers = ["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","","区分","検出ワード"]
    write_csv(outdir / "qualified.csv", final_rows, headers)
    (outdir / "query_stats.json").write_text(json.dumps(query_stats, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "segment": args.segment, "label": cfg["label"], "live_tab_counts": tab_counts,
        "queries": len(query_stats), "found_domains": len(found), "audited": len(audits),
        "accepted": len(final_rows), "decisions": {}, "output": str(outdir / "qualified.csv"),
    }
    for r in audits:
        key = r["decision"] + ":" + (r["reason"] or "ok")
        summary["decisions"][key] = summary["decisions"].get(key, 0) + 1
    (outdir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"stage":"complete", **summary}, ensure_ascii=False), flush=True)
    if len(final_rows) < args.target:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
