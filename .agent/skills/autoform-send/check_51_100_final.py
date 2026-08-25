import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
rows = sheets_io.read_rows(ws, want=["company_name","status"])
from collections import Counter
c = Counter()
for r in rows:
    if 51 <= r["_row"] <= 100:
        c[r.get("status") or "(empty)"] += 1
print(c)
