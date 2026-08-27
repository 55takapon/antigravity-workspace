import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Web幹事")
all_vals = ws.get_all_values()
headers = all_vals[0]

# find any existing excluded rows (status col I = index 8)
count = 0
for idx, row in enumerate(all_vals[1:], start=2):
    if len(row) > 8 and row[8].strip() == "excluded":
        print("=== existing excluded row", idx, "===")
        for h, v in zip(headers, row):
            if v.strip():
                print(f"  {h}: {v[:150]}")
        count += 1
        if count >= 5:
            break
print("total existing excluded in this sheet:", count)

# the single 業種違い row in col O
for idx, row in enumerate(all_vals[1:], start=2):
    if len(row) > 14 and row[14] == "業種違い":
        print("=== 業種違い row", idx, "===")
        for h, v in zip(headers, row):
            if v.strip():
                print(f"  {h}: {v[:150]}")
