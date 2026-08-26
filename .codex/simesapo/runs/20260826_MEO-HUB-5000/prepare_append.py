import csv
import sys


source, output, limit = sys.argv[1], sys.argv[2], int(sys.argv[3])
fields = ["company_name", "url", "address", "phone", "maps_url", "status"]
with open(source, encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))[:limit]
with open(output, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows({key: row.get(key, "") for key in fields} for row in rows)
print(f"prepared={len(rows)}")
