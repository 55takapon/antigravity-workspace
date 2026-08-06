import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
sys.path.insert(0, str(SKILL / "shared"))
import sheets_io  # noqa: E402

sheet, worksheet = sys.argv[1], sys.argv[2]
wanted = {516, 726, *range(1327, 1353), 1769, 1828, 1853, 1909}
ws = sheets_io.open_worksheet(sheet, worksheet)
rows = sheets_io.read_rows(ws, want=["company_name", "url", "contact_url", "phone", "status"])
selected = [row for row in rows if int(row.get("_row") or 0) in wanted]
print(json.dumps([{k: row.get(k, "") for k in ("_row", "company_name", "url", "contact_url", "phone", "status")} for row in selected], ensure_ascii=False))
