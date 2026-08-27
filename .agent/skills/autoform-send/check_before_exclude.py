import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Web幹事")
all_vals = ws.get_all_values()

conflicts = []
for idx, row in enumerate(all_vals[1:], start=2):
    o_val = row[14] if len(row) > 14 else ""
    if o_val == "HP本文より除外対象":
        status_val = row[8] if len(row) > 8 else ""
        sent_at_val = row[7] if len(row) > 7 else ""
        if status_val.strip() or sent_at_val.strip():
            conflicts.append((idx, status_val, sent_at_val))

print("conflicts (already have status/sent_at):", len(conflicts))
for c in conflicts[:20]:
    print(c)
