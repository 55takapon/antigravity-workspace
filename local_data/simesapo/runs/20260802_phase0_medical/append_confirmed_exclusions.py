import sys
from urllib.parse import urlparse

sys.path.insert(0, r".agent\skills\simesapo-sales-skills-dist\shared")
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"


def domain(url):
    host = urlparse(url if "://" in url else "https://" + url).hostname or ""
    return host.lower().removeprefix("www.")


rows = [
    ["株式会社ITreat", "https://itreat.co.jp/", "", "", "", "https://itreat.co.jp/contact", "", "", "excluded", "sales_prohibited:同業のWeb制作会社・フリーランスからの連絡を公式問い合わせページで明示的に禁止。 | source:第0波_歯科医療", "", "", "除外確定（営業禁止）"],
    ["Kurumi株式会社", "https://kurumi.co.jp/", "", "", "", "https://kurumi.co.jp/contact_sales/", "", "", "excluded", "sales_prohibited:営業・協業の相談を公式サイトで明示的に全面拒否。 | source:第0波_歯科医療", "", "", "除外確定（営業禁止）"],
    ["株式会社ゼロメディカル", "https://zeromedical.tv/", "", "", "", "https://zeromedical.tv/zeromedical-web/inquiry/", "", "", "excluded", "enterprise_audit:上場会社リミックスポイントの完全子会社であることを公式会社情報で確認。 | source:第0波_歯科医療", "", "", "除外確定（上場企業・大手グループ）"],
]

ws = sheets_io.open_worksheet(SHEET, "除外リスト")
existing = ws.get_all_values()[1:]
names = {r[0].strip() for r in existing if r}
domains = {domain(r[1]) for r in existing if len(r) > 1 and r[1].strip()}
pending = [r for r in rows if r[0] not in names and domain(r[1]) not in domains]
print("preview_count=", len(pending))
for row in pending:
    print(row[0], row[1], row[12])
if pending:
    ws.append_rows(pending, value_input_option="RAW")
values = ws.get_all_values()
for row in pending:
    hits = [(i + 1, r) for i, r in enumerate(values) if r and (r[0] == row[0] or (len(r) > 1 and domain(r[1]) == domain(row[1])))]
    print("readback", row[0], [(i, r[8], r[12]) for i, r in hits])
print("final_data_rows=", len(values) - 1)
