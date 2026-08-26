import csv
import re
import sys


source, target = sys.argv[1:3]
with open(source, encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
    fields = list(rows[0]) if rows else []

cleared = 0
for row in rows:
    phone = row.get("phone", "")
    digits = re.sub(r"\D", "", phone)
    if phone and (not re.fullmatch(r"[\d\s()+\-ー－]+", phone) or not 9 <= len(digits) <= 15):
        row["phone"] = ""
        cleared += 1

with open(target, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f"rows={len(rows)} cleared={cleared}")
