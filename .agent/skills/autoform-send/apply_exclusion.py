import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Web幹事")
all_vals = ws.get_all_values()

target_rows = []
for idx, row in enumerate(all_vals[1:], start=2):
    o_val = row[14] if len(row) > 14 else ""
    if o_val == "HP本文より除外対象":
        p_val = row[15] if len(row) > 15 else ""
        target_rows.append((idx, p_val))

print("target rows:", len(target_rows))

# build I and J updates via batch_update for efficiency
updates = []
for row_num, p_val in target_rows:
    reason = f"営業除外業種違い（{p_val}）" if p_val else "営業除外業種違い"
    updates.append({"range": f"I{row_num}", "values": [["excluded"]]})
    updates.append({"range": f"J{row_num}", "values": [[reason]]})

ws.batch_update(updates)
print("done, updated", len(target_rows), "rows")
