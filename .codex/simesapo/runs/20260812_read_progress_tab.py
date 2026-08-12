import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
sys.path.insert(0, str(DIST / ".codex_pydeps"))
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client

book = get_client(str(DIST / "shared" / "gcp_service_account.json")).open_by_key("1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ")
ws = book.worksheet("収集進捗管理")
print(json.dumps({"rows": ws.row_count, "cols": ws.col_count, "values": ws.get("A1:N120")}, ensure_ascii=False, indent=2))
