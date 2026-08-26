import csv
import re
import sys


strong = re.compile(r"支援|受託|代行|コンサル|制作|請負|広告代理|提供|運用|保守")
service = re.compile(
    r"WEBデザイン|Webデザイン|ウェブデザイン|ホームページ|WEB製作|Web製作|"
    r"デザイン事務所|広告プロモート|広告企画|販促|プロモーション|"
    r"グラフィックデザイン|印刷|看板|サイン|イベント|ブランディング"
)
internal = re.compile(r"通信販売|自社ブランド|自社商品|不動産賃貸|家具.*販売|製造販売")
client = re.compile(r"承って|受注|顧客|お客様|クライアント|提案|広告|販促")

source, target = sys.argv[1:3]
with open(source, encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
    fields = list(rows[0]) if rows else []

kept = []
for row in rows:
    text = row.get("business_description", "")
    if strong.search(text) or not service.search(text):
        continue
    if internal.search(text) and not client.search(text):
        continue
    kept.append(row)

with open(target, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(kept)
print(f"input={len(rows)} recovered={len(kept)}")
