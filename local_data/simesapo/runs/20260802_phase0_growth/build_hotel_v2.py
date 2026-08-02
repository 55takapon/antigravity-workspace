from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "hotel_final_verified_50.csv"
OUTPUT = HERE / "hotel_final_verified_50_v2.csv"
HEADERS = [
    "company_name", "url", "address", "phone", "maps_url", "contact_url",
    "message", "sent_at", "status", "error_reason", "screenshot_path",
    "provider_used", "提案区分", "H1", "区分", "検出ワード",
]
REMOVE = {
    "株式会社キャディッシュ", "株式会社CORE", "株式会社OMOTENASHI",
    "株式会社宿力", "株式会社宿研",
}
ADD = [
    ("株式会社pod", "https://p-o-d.co.jp/", "https://p-o-d.co.jp/contact/", "宿泊施設・民泊の企画・運営代行"),
    ("カソク株式会社", "https://www.kasoku.co.jp/", "https://www.kasoku.co.jp/contact", "宿泊施設の開発・運用支援"),
    ("株式会社MAKOTOMI", "https://consulting.makotomi.jp/", "https://consulting.makotomi.jp/#contact", "ホテル・旅館専門コンサルティング"),
    ("Hott株式会社", "https://hottassist.com/", "https://hottassist.com/#contact", "民泊・旅館業の運営代行・コンサルティング"),
    ("JS暁宅株式会社", "https://www.akatsukihouse.jp/", "https://akatsukihouse.jp/contact", "民泊施設の開発・運営代行"),
]

with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    rows = [r for r in csv.DictReader(f) if r.get("company_name") not in REMOVE]

for company, url, contact, evidence in ADD:
    row = {h: "" for h in HEADERS}
    row.update({
        "company_name": company,
        "url": url,
        "contact_url": contact,
        "区分": "S｜業界特化Web制作",
        "検出ワード": f"旅館・ホテル・観光特化支援：{evidence}",
    })
    rows.append(row)

if len(rows) != 50:
    raise SystemExit(f"count={len(rows)}")
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)
print(OUTPUT)
