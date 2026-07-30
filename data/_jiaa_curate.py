import csv
import re
from pathlib import Path
from urllib.parse import quote, urlparse


ROOT = Path(__file__).resolve().parents[1]
INFILE = ROOT / "data" / "_jiaa_verified_audit.csv"
OUTFILE = ROOT / "data" / "_jiaa_precore.csv"

DENY = {
    "Cinarra Systems Japan株式会社",
    "Index Exchange Japan株式会社",
    "JICDAQ (デジタル広告品質認証機構)",
    "Priv Tech株式会社",
    "SMN株式会社",
    "Supership株式会社",
    "イオンマーケティング株式会社",
    "イー・ガーディアン株式会社",
    "チョークデジタル株式会社",
    "ニールセン デジタル株式会社",
    "バリューコマース株式会社",
    "パブマティック株式会社",
    "ユナイテッドマーケティングテクノロジーズ株式会社",
    "ログリー株式会社",
    "株式会社 CMerTV",
    "株式会社 ContentAge",
    "株式会社 FLUX",
    "株式会社 PTD",
    "株式会社 Skyfall",
    "株式会社 TimeTree",
    "株式会社 アイデム",
    "株式会社 アイモバイル",
    "株式会社 アド・プロ",
    "株式会社 インテージ",
    "株式会社 イード",
    "株式会社 ウエディングパーク",
    "株式会社 クライド",
    "株式会社 クロスリスティング",
    "株式会社 グレイプ",
    "株式会社 ジーニー",
    "株式会社 ダイヤモンド社",
    "株式会社 データ・ワン",
    "株式会社 ビデオリサーチ",
    "株式会社 ファンコミュニケーションズ",
    "株式会社 フリークアウト",
    "株式会社 プレイド",
    "株式会社 マイベスト",
    "株式会社 マクロミル",
    "株式会社 メディアジーン",
    "株式会社 日本ビジネスプレス",
    "株式会社 日経BP",
    "株式会社 東洋経済新報社",
    "株式会社 産経デジタル",
}


def clean_address(value):
    value = re.sub(
        r"\s+(?:MAP|Map|GOOGLE MAP|Service|サービス紹介|Privacy Policy|プライバシーポリシー|"
        r"HOME|NEWS|X Facebook|Facebook Twitter|Copyright|©|代表取締役|代表者|電 話|事業所|"
        r"加盟団体|認証登録番号|お問い合わせ先|サイトマップ|2\.)\b.*$",
        "",
        value,
        flags=re.I,
    )
    value = re.split(r"\s+(?:【|■|＜|-->)", value, maxsplit=1)[0]
    return value.strip(" ,，。")


def normalized_url(value):
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/") or value


with INFILE.open(encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

out = []
for row in rows:
    if row["company_name"] in DENY:
        continue
    address = clean_address(row["address"])
    if len(address) > 95 or not re.search(r"(都|道|府|県).+(市|区|郡).*\d", address):
        continue
    address_query = re.sub(r"^〒\d{3}-\d{4}\s*", "", address)
    out.append(
        {
            "company_name": row["company_name"],
            "url": normalized_url(row["url"]),
            "address": address,
            "phone": row["phone"],
            "maps_url": "https://www.google.com/maps/search/?api=1&query=" + quote(address_query),
            "status": "",
        }
    )

with OUTFILE.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["company_name", "url", "address", "phone", "maps_url", "status"],
    )
    writer.writeheader()
    writer.writerows(out)

print(f"curated={len(out)} out={OUTFILE}")
