from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_NEXT-B-JLAA-001"
RUN.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(DIST / ".codex_pydeps"))
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client
import requests
from bs4 import BeautifulSoup

SHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
SOURCE_URL = "https://jlaa2003.com/company/"


def normalize_name(value: str) -> str:
    s = unicodedata.normalize("NFKC", value or "").strip().lower()
    s = s.replace("㈱", "株式会社").replace("㈲", "有限会社")
    s = re.sub(r"[（(].*?(?:支社|支店).*?[）)]", "", s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^(株式会社|有限会社|合同会社|合資会社|一般社団法人|公益社団法人)", "", s)
    s = re.sub(r"(株式会社|有限会社|合同会社|合資会社)$", "", s)
    return re.sub(r"[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+", "", s)


resp = requests.get(SOURCE_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")
records = []
section = "正会員"
last_area = ""
for tr in soup.select("table tr"):
    cells = [unicodedata.normalize("NFKC", c.get_text(" ", strip=True)) for c in tr.select("th,td")]
    if not cells:
        continue
    joined = " | ".join(cells)
    if "賛助会員" in joined:
        section = "賛助会員"
    company = next((c for c in cells if re.search(r"(?:\(株\)|\(有\)|株式会社|有限会社|合資会社|合同会社|有限公司)", c) and "入会希望" not in c), "")
    if not company:
        continue
    company = company.replace("(株)", "株式会社").replace("(有)", "有限会社").strip()
    if any(x in company for x in ("日本地域広告会社協会", "正会員として")):
        continue
    area_candidates = [c for c in cells if re.fullmatch(r"(?:北海道|青森|秋田|岩手|山形|宮城|福島|茨城|栃木|群馬|埼玉|千葉|東京|神奈川|新潟|富山|石川|山梨|長野|静岡|岐阜|愛知|福井|三重|滋賀|京都|大阪|兵庫|奈良|和歌山|鳥取|島根|岡山|広島|山口|香川|徳島|愛媛|高知|福岡|佐賀|長崎|大分|宮崎|熊本|鹿児島|沖縄|台湾)", c)]
    if area_candidates:
        last_area = area_candidates[-1]
    records.append({"source": "JLAA", "source_url": SOURCE_URL, "member_type": section, "area": last_area, "company_name": company, "company_norm": normalize_name(company)})

# Stable unique by normalized company; branch duplicates remain visible in the raw file via source rows.
seen = set()
unique = []
for r in records:
    if r["company_norm"] and r["company_norm"] not in seen:
        seen.add(r["company_norm"])
        unique.append(r)

book = get_client(str(DIST / "shared" / "gcp_service_account.json")).open_by_key(SHEET_ID)
existing = {}
for ws in book.worksheets():
    vals = ws.get_all_values()
    if not vals:
        continue
    headers = [unicodedata.normalize("NFKC", x).strip().lower() for x in vals[0]]
    try:
        ci = headers.index("company_name")
    except ValueError:
        try:
            ci = headers.index("会社名")
        except ValueError:
            continue
    for rn, row in enumerate(vals[1:], start=2):
        name = row[ci].strip() if ci < len(row) else ""
        key = normalize_name(name)
        if key:
            existing.setdefault(key, []).append({"tab": ws.title, "row": rn, "company_name": name})

for r in unique:
    matches = existing.get(r["company_norm"], [])
    r["existing_match"] = "yes" if matches else "no"
    r["existing_locations"] = " / ".join(f"{m['tab']}!{m['row']}" for m in matches[:10])

fields = ["source", "source_url", "member_type", "area", "company_name", "company_norm", "existing_match", "existing_locations"]
with (RUN / "jlaa_members_source_diff.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader(); w.writerows(unique)

report = {
    "source_rows_parsed": len(records),
    "unique_companies": len(unique),
    "member_type_counts": {t: sum(r["member_type"] == t for r in unique) for t in sorted({r["member_type"] for r in unique})},
    "existing_exact_company_matches": sum(r["existing_match"] == "yes" for r in unique),
    "unseen_by_company_name": sum(r["existing_match"] == "no" for r in unique),
    "output": str(RUN / "jlaa_members_source_diff.csv"),
}
(RUN / "source_diff_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
