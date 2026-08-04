from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[4]
        / ".agent"
        / "skills"
        / "simesapo-sales-skills-dist"
        / "shared"
    ),
)
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
TARGET = "シート1"

CORRECTIONS = {
    "アイニックス株式会社": {
        "old": "https://www.ainix.co.jp/contact/",
        "new": "https://www.ainix.co.jp/contact/aboutus.html",
        "reason": "会社問い合わせフォームへ具体化",
    },
    "ルミーズ株式会社": {
        "old": "https://www.remise.co.jp/contact.html",
        "new": "https://www.remise.co.jp/form/partnership/index.html",
        "reason": "営業禁止の一般フォームからアライアンスパートナー専用フォームへ変更",
    },
    "株式会社マコトフードサービス": {
        "old": "https://www.makotofood.co.jp/contact/",
        "new": "https://www.makotofood.co.jp/mailform/",
        "reason": "本社への営業・提案を案内する問い合わせフォームへ変更",
    },
}

book = sheets_io.get_client().open_by_url(SHEET)
ws = book.worksheet(TARGET)
values = ws.get_all_values()

located = {}
for company, correction in CORRECTIONS.items():
    matches = [index for index, row in enumerate(values[1:], start=2) if row and row[0].strip() == company]
    if len(matches) != 1:
        raise SystemExit(f"company_match_failed:{company}:{matches}")
    row_number = matches[0]
    row = values[row_number - 1] + [""] * (16 - len(values[row_number - 1]))
    if row[5].strip() != correction["old"]:
        raise SystemExit(
            f"old_url_mismatch:{company}:expected={correction['old']}:actual={row[5].strip()}"
        )
    located[company] = {"row": row_number, "before": row[:16], **correction}

ws.batch_update(
    [
        {"range": f"F{item['row']}", "values": [[item["new"]]]}
        for item in located.values()
    ],
    value_input_option="RAW",
)

results = []
for company, item in located.items():
    after = ws.get(f"A{item['row']}:P{item['row']}")
    if len(after) != 1:
        raise SystemExit(f"readback_missing:{company}:{item['row']}")
    padded = after[0] + [""] * (16 - len(after[0]))
    expected = item["before"].copy()
    expected[5] = item["new"]
    if padded[:16] != expected:
        changed = [index + 1 for index, (a, b) in enumerate(zip(expected, padded[:16])) if a != b]
        raise SystemExit(f"readback_mismatch:{company}:{item['row']}:columns={changed}")
    results.append(
        {
            "company_name": company,
            "row": item["row"],
            "old_contact_url": item["old"],
            "new_contact_url": item["new"],
            "reason": item["reason"],
            "verified_a_to_p": True,
            "changed_columns": ["F"],
        }
    )

print(json.dumps({"updated": len(results), "results": results}, ensure_ascii=False))
