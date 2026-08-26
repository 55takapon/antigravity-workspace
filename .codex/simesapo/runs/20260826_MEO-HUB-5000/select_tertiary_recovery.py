import csv
import re
import sys


source, strict_path, recovered_path, target = sys.argv[1:5]


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


rows = read(source)
used = {row["company_name"] for row in read(strict_path) + read(recovered_path)}
positive = re.compile(
    r"デザイン会社|デザイン事務所|広告デザイン業|広告業|広告・宣伝|広告宣伝|"
    r"広告.*営業|広告.*取り扱|Webメディア事業|インターネット広告事業|"
    r"デジタルマーケティング|マーケティングカンパニー|ブランディング|"
    r"総合印刷業|商業印刷|グラフィックデザイン|パッケージ.*デザイン"
)
negative = re.compile(
    r"鉄道事業|バスターミナル|介護|不動産|通信販売|レストラン|空港|"
    r"自社商品|家具.*販売|建築土木|パイプハウス|ホールディング"
)

kept = [
    row
    for row in rows
    if row.get("company_name") not in used
    and positive.search(row.get("business_description", ""))
    and not negative.search(row.get("business_description", ""))
]
with open(target, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(kept)
print(f"kept={len(kept)}")
