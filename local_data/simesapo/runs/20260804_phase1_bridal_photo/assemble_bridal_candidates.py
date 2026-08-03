from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).parent

NAME_OVERRIDES = {
    "Do": "株式会社Do",
    "FUNSEE": "株式会社FUNSEE",
    "J-MZ!!": "株式会社J-MZ",
    "NORTH": "合同会社NORTH",
    "PKBソリューション": "株式会社PKBソリューション",
    "PIEM（パイエム）": "PIEM株式会社",
    "CAN EAT": "株式会社CAN EAT",
    "WeBridge": "株式会社WeBridge",
    "ニュー・バリュー・フロンティア": "株式会社ニュー・バリュー・フロンティア",
    "Speria": "株式会社Speria",
    "rusk": "株式会社rusk",
    "vircre": "株式会社Vircre",
    "あつまる": "株式会社あつまる",
    "アンドディファレンス": "株式会社＆Difference",
    "エスキュービズム": "株式会社プリマベーラ",
    "オリジナルあい": "株式会社オリジナルあい",
    "セントラルテクノ": "株式会社セントラルテクノ",
    "タイムレス": "株式会社タイムレス",
    "トライスパイド": "株式会社トライスパイド",
    "バリューブリッジ": "株式会社バリューブリッジ",
    "パプレア": "株式会社パプレア",
    "ビーハイライト": "ビーハイライト株式会社",
    "フォーディメンション": "株式会社フォーディメンション",
    "メモリード・ライフ": "メモリード・ライフ株式会社",
    "ユニオンビズ": "ユニオンビズ株式会社",
    "リ・プロダクツ": "リ・プロダクツ株式会社",
    "一般社団法人ブライダルアライアンス": "一般社団法人ブライダルアライアンス",
    "創和プロジェクト": "創和プロジェクト株式会社",
    "安本武司商店": "株式会社安本武司商店",
    "藤電設工業": "有限会社藤電設工業",
    "ゆめじん": "ゆめじん有限会社",
    "ヒカル・オーキッド": "有限会社ヒカル・オーキッド",
    "めおと": "株式会社プラスワイズ",
    "孝芳堂": "孝芳堂株式会社",
    "山崎実業": "山崎実業株式会社",
    "ベル食品工業": "ベル食品工業株式会社",
}

BAD_CONTACT_PARTS = ("/basic/", "/information", "instagram.com")
CONTACT_OVERRIDES = {
    "PIEM（パイエム）": "https://tayori.com/f/piem-contact/",
    "安本武司商店": "https://www.yasumoto.jp/contact",
}
DOMAIN_CONTACT_OVERRIDES = {
    "www.noritsu-precision.com": "https://www.noritsu-precision.com/contact/",
    "tolami.co.jp": "https://tolami.co.jp/contact/",
    "www.tomicolor.co.jp": "http://www.tomicolor.co.jp/contact/entry-form/",
    "www.asanumashoukai.co.jp": "https://www.asanumashoukai.co.jp/f/contact",
}
SKIP_JPIA_DOMAINS = {"www.n-pri.jp", "www.shop-takeno.net"}


def read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


rows = []
for row in read(HERE / "bridal_crawled.csv"):
    name = NAME_OVERRIDES.get(row["brand"])
    contact = CONTACT_OVERRIDES.get(row["brand"], row.get("contact_url", "").strip())
    if not name or not contact or any(x in contact for x in BAD_CONTACT_PARTS):
        continue
    exhibit = row.get("exhibit", "").strip() or "ブライダル業界向け商品・運営支援"
    rows.append({
        "company_name": name,
        "url": row["url"],
        "contact_url": contact,
        "区分": "S｜業界特化Web制作・店舗支援ハブ",
        "検出ワード": f"ブライダル・写真業界ハブ：{exhibit}",
        "source_url": row["source_url"],
    })

for row in read(HERE / "jpia_candidates.csv"):
    from urllib.parse import urlparse
    host = (urlparse(row["url"]).hostname or "").lower()
    if host in SKIP_JPIA_DOMAINS:
        continue
    if not row.get("contact_url", "").strip():
        continue
    rows.append({
        "company_name": row["company_name"],
        "url": row["url"],
        "contact_url": DOMAIN_CONTACT_OVERRIDES.get(host, row["contact_url"]),
        "区分": "S｜業界特化Web制作・店舗支援ハブ",
        "検出ワード": "写真業界ハブ：写真・アルバム・撮影関連支援",
        "source_url": row["source_url"],
    })

fields = ["company_name", "url", "contact_url", "区分", "検出ワード", "source_url"]
with (HERE / "bridal_candidate_seed.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
print({"pdf": sum(r["source_url"].endswith(".pdf") for r in rows), "jpia": sum("jpia.jp" in r["source_url"] for r in rows), "total": len(rows)})
