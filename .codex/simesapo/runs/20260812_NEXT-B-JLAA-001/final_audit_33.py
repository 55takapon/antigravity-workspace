import csv
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

OUT = Path(__file__).with_name("jlaa_final_audit_33.csv")

# Official URLs and first-pass disposition are based on official-site/company-page verification.
# A blank URL means the official web site could not be established in this audit.
ROWS = [
    ("株式会社リズム・エージェンシー", "http://plus-plus.info/", "send", "地域広告会社。法人情報掲載URLとJLAA社名を突合"),
    ("株式会社アクティブイエロー", "https://www.activeyellow.co.jp/", "send", "広告・出版・地域情報発信"),
    ("株式会社ライトエージェンシー", "https://www.light-agc.co.jp/", "send", "総合広告、Web・SNS支援"),
    ("クロスボーダー株式会社", "https://x-border.co.jp/", "send", "PR・広告・Web・イベント"),
    ("株式会社共和エージェンシー 神奈川支社", "https://www.kyowa-e.co.jp/", "send", "広告・イベント・販促"),
    ("株式会社ライズウィル", "https://rise-will.com/", "send", "飲食店支援、SNS・Googleビジネスプロフィール支援"),
    ("株式会社ウイル・コーポレーション", "https://www.well-corp.jp/", "exclude", "上場会社ウイルコホールディングス系"),
    ("株式会社ストアインク", "https://store-ink.jp/", "send", "地域媒体・広告・マーケティング"),
    ("株式会社アイク", "https://aic-ad.co.jp/", "send", "地域広告会社"),
    ("株式会社東通エィジェンシー", "https://www.totsu-ag.com/", "exclude", "上場会社東建コーポレーショングループ"),
    ("有限会社アド・フューチャー", "https://ad-future.jp/", "send", "子育て情報誌・地域広告"),
    ("株式会社s.create(エスクリエイト)", "https://shiga-create.jp/", "send", "広告・地域媒体・SNS・Web制作"),
    ("株式会社関西ぱど", "https://www.kansaipado.co.jp/", "exclude", "上場会社中広グループ"),
    ("株式会社播磨リビング新聞社", "https://harimaliving.co.jp/", "send", "地域情報誌・Web・広告"),
    ("株式会社エヌ・アイ・プランニング", "https://www.niplanning.jp/", "send", "地域媒体・販促・イベント・Web"),
    ("株式会社コスモプラス", "https://cosmo-plus.co.jp/", "send", "総合広告・Web・映像・販促"),
    ("株式会社ビザビ", "https://vis-a-vis.co.jp/", "send", "地域広告・イベント・出版・マーケティング"),
    ("株式会社RCC文化センター", "https://www.rccbc.co.jp/", "exclude", "中国放送グループ"),
    ("株式会社毎日メディアサービス山口", "https://mainichi-msy.co.jp/", "exclude", "毎日新聞グループ系"),
    ("株式会社オリコ", "https://www.orico-jp.com/", "send", "地域密着の総合広告、Web・SNS・販促"),
    ("朝日エリアコム株式会社", "https://www.asahi-area.com/", "exclude", "朝日新聞グループ"),
    ("株式会社ジェー・ビー・エフ", "https://www.jbf.co.jp/", "send", "広告・印刷・販促パートナー"),
    ("株式会社福広", "https://fuku-kou.com/", "send", "地域広告・屋外広告"),
    ("サンコー・コミュニケーションズ株式会社", "https://sanko-com.jp/", "send", "熊本の総合広告会社"),
    ("合資会社鹿児島広告社", "https://kagoad55.synapse-site.jp/", "send", "地域の看板・屋外広告"),
    ("DMカードジャパン株式会社", "https://www.dmcj.co.jp/", "exclude", "製造業・建築業向け媒体で店舗クライアント接点が薄い"),
    ("株式会社ネクストインターナショナル", "https://nx-inter.com/", "exclude", "総合卸売・輸出入で広告支援受託会社ではない"),
    ("株式会社インターカラー", "https://www.intercolor.co.jp/", "send", "紙媒体中心の広告代理・集客支援"),
    ("恩詩國際行銷有限公司", "https://www.ansming.com/", "exclude", "台湾法人で日本国内店舗支援パートナーの主対象外"),
    ("JC Connect株式会社", "https://www.jc-connect.co.jp/", "send", "訪日・海外向けSNS公式アカウント・広告支援"),
    ("株式会社gr.a.m", "https://gra-m.com/", "exclude", "上場会社クロス・マーケティンググループの関連会社"),
    ("株式会社ときしろ", "https://tokishiro.jp/", "send", "広告撮影・Web制作・販促デザイン"),
    ("株式会社アネックスデジタルジャパン", "https://annex-digital.com/", "send", "PR・映像・商業施設イベント・地方創生"),
]

CONTACT_WORDS = re.compile(r"お問い合わせ|お問合せ|contact|inquiry|ご相談", re.I)

def inspect(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            label = " ".join(a.get_text(" ", strip=True).split())
            href = urljoin(r.url, a["href"])
            if CONTACT_WORDS.search(label + " " + href):
                links.append(href)
        same = [u for u in links if urlparse(u).netloc == urlparse(r.url).netloc]
        candidates = list(dict.fromkeys(same + links))[:8]
        for u in candidates:
            try:
                cr = requests.get(u, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                cs = BeautifulSoup(cr.text, "html.parser")
                if cr.ok and cs.find("form") and any(x.get("name") for x in cs.find_all(["input", "textarea", "select"])):
                    return cr.url, "real_form_confirmed"
            except Exception:
                pass
        return (candidates[0] if candidates else ""), ("contact_link_only" if candidates else "no_contact_link")
    except Exception as e:
        return "", "site_fetch_failed:" + type(e).__name__

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["company_name", "official_url", "classification", "audit_reason", "contact_url", "contact_check", "audit_date"])
    w.writeheader()
    for name, url, decision, reason in ROWS:
        contact, check = inspect(url) if url else ("", "official_site_unconfirmed")
        # A send candidate must have a usable web form. Contact-link-only or no form is not written as send.
        classification = "送付対象" if decision == "send" and check == "real_form_confirmed" else "除外"
        if decision == "send" and check != "real_form_confirmed":
            reason += f"／実在フォーム未確認({check})"
        w.writerow({"company_name": name, "official_url": url, "classification": classification, "audit_reason": reason,
                    "contact_url": contact, "contact_check": check, "audit_date": "2026-08-12"})

print(OUT)
