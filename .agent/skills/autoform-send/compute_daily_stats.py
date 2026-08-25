import sys
sys.path.insert(0, '../../../shared')
import sheets_io
from collections import Counter

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
rows = sheets_io.read_rows(ws, want=["company_name","status","sent_at"])

today_rows = [r for r in rows if (r.get("sent_at") or "")[:10] == "2026-08-25"]
print("count today:", len(today_rows))
c = Counter(r.get("status") for r in today_rows)
print(c)
row_nums = sorted(r["_row"] for r in today_rows)
if row_nums:
    print("row range:", row_nums[0], "-", row_nums[-1])
    print("all rows touched:", row_nums)
