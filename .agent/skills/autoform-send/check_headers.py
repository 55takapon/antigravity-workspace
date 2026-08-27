import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Web幹事")
all_vals = ws.get_all_values()

target = "HP本文より除外対象"
found = []
for idx, row in enumerate(all_vals, start=1):
    for cidx, cell in enumerate(row, start=1):
        if target in cell:
            found.append((idx, cidx, cell[:100]))

print("matches:", len(found))
for m in found[:20]:
    print(m)

# also print unique values seen in column O across whole sheet
from collections import Counter
o_vals = Counter()
for row in all_vals[1:]:
    if len(row) > 14:
        o_vals[row[14]] += 1
print("O column value counts:", o_vals.most_common(20))
