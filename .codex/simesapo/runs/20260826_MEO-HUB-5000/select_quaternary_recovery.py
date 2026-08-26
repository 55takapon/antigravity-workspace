import csv
import re
import sys


source, target, *used_paths = sys.argv[1:]


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


rows = read(source)
used = {row["company_name"] for path in used_paths for row in read(path)}
positive = re.compile(
    r"広告主|広告の企画|広告.*代理店|販売促進企画|広告コミュニケーション|"
    r"デジタル広告事業|インターネット.*広告|広告プラン|ポスティング|"
    r"新聞折込広告|マーケティング事業|SNSマーケティング|動画マーケティング|"
    r"企業向け動画|広告の取扱|広告事業|広告に関する事業|グローバル広告|"
    r"交通広告の企画|広告記事等の営業|広告・宣伝|出版・広告"
)
negative = re.compile(
    r"鉄道事業|バスターミナル|介護|不動産|通信販売|レストラン|空港|"
    r"自社商品|製造販売|プラットフォーム事業"
)
excluded_names = {"カルチュア・コンビニエンス・クラブ株式会社"}
explicit_names = {
    "株式会社ヒトクセ",
    "株式会社グッドエレファント",
    "株式会社プリンツ二十一",
    "株式会社ラックランド",
}
kept = [
    row
    for row in rows
    if row.get("company_name") not in used
    and row.get("company_name") not in excluded_names
    and (
        row.get("company_name") in explicit_names
        or (
            positive.search(row.get("business_description", ""))
            and not negative.search(row.get("business_description", ""))
        )
    )
]
with open(target, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(kept)
print(f"kept={len(kept)}")
