import csv
import re
import sys


source, strict_path, recovered_path, target = sys.argv[1:5]


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


rows = read(source)
used = {row["company_name"] for row in read(strict_path) + read(recovered_path)}
first = re.compile(
    r"デザイン会社|デザイン事務所|広告デザイン業|広告業|広告・宣伝|広告宣伝|"
    r"広告.*営業|広告.*取り扱|Webメディア事業|インターネット広告事業|"
    r"デジタルマーケティング|マーケティングカンパニー|ブランディング|"
    r"総合印刷業|商業印刷|グラフィックデザイン|パッケージ.*デザイン"
)
second = re.compile(
    r"相談|提案|デザイン設計業|デザインが|企画デザイン|企画プロデュース|"
    r"デザイン事業|WEB|Web|ホームページ"
)
negative = re.compile(
    r"鉄道事業|バスターミナル|介護|不動産|通信販売|レストラン|空港|"
    r"自社商品|家具.*販売|建築土木|パイプハウス|ホールディング|"
    r"建築設計事務所|建築設計事業|自由設計|インテリアコーディネート"
)
excluded_names = {
    "カルチュア・コンビニエンス・クラブ株式会社",
    "株式会社植野建築設計事務所",
    "株式会社ＪＰ設計",
}

kept = []
for row in rows:
    text = row.get("business_description", "")
    name = row.get("company_name", "")
    if name in used or name in excluded_names:
        continue
    if first.search(text) or not second.search(text) or negative.search(text):
        continue
    kept.append(row)

with open(target, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(kept)
print(f"kept={len(kept)}")
