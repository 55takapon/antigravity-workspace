import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
sys.path.insert(0, str(DIST / ".codex_pydeps")); sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client

book = get_client(str(DIST / "shared" / "gcp_service_account.json")).open_by_key("1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ")
ws = book.worksheet("収集進捗管理")
expected = [["1", "NEXT-B-JLAA-001", "日本地域広告会社協会（JLAA）", "63社取得 / 既存23 / 大手等7 / 残存33", "過去57バッチにJLAA利用記録なし", "33社の公式URL・実フォーム監査へ進む"]]
ws.update(range_name="A84:F84", values=expected, value_input_option="RAW")
got = ws.get("A84:F84")
if got != expected:
    raise SystemExit("STOP: reread mismatch " + json.dumps(got, ensure_ascii=False))
print(json.dumps({"written": 1, "verified": 1, "range": "収集進捗管理!A84:F84"}, ensure_ascii=False))
