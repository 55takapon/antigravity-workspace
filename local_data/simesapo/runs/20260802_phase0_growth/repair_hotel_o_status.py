from __future__ import annotations

import csv
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.get_client().open_by_url(SHEET).worksheet("シート1")

expected_o = [["S｜業界特化Web制作"] for _ in range(45)]
with (Path(__file__).parent / "hotel_candidate_pool.csv").open(encoding="utf-8-sig", newline="") as handle:
    source_rows = list(csv.DictReader(handle))[:45]
expected_p = [[row["検出ワード"].strip()] for row in source_rows]
if len(expected_p) != 45 or any(not row[0] for row in expected_p):
    raise SystemExit("source_evidence_invalid")

ws.update(expected_o, "O2216:O2260", value_input_option="RAW")
ws.update(expected_p, "P2216:P2260", value_input_option="RAW")
ws.update([[""]], "I2219", value_input_option="RAW")

actual_o = ws.get("O2216:O2260")
actual_p = ws.get("P2216:P2260")
actual_i = ws.get("I2219")
o_values = [(row[0] if row else "") for row in actual_o]
p_values = [(row[0] if row else "") for row in actual_p]
i_value = actual_i[0][0] if actual_i and actual_i[0] else ""

if o_values != [row[0] for row in expected_o] or p_values != [row[0] for row in expected_p] or i_value != "":
    raise SystemExit({"O_verified": sum(v == "S｜業界特化Web制作" for v in o_values), "P_verified": sum(v == expected_p[i][0] for i, v in enumerate(p_values)), "I2219": i_value})

print({"O_range": "O2216:O2260", "O_verified": 45, "P_range": "P2216:P2260", "P_verified": 45, "I2219": "cleared", "M_changed": 0})
