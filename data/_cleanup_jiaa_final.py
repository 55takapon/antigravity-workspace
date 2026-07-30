import csv
import re
from pathlib import Path
from urllib.parse import quote


path = Path(__file__).with_name("agent_round22_jiaa_members.csv")
with path.open(encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

markers = [
    " 福岡支社",
    " 横浜オフィス",
    " 交通案内",
    " ※",
    " 03-5468-6877",
    " 役員",
    " ©",
    " Branch office",
    " (03)-",
    " VIEW",
    " eREALについて",
    " TOP ABOUT",
    " Sourcing",
    " tko Inc.",
]

for row in rows:
    address = row["address"]
    for marker in markers:
        address = address.split(marker, 1)[0]
    address = address.strip(" ,，。／")
    row["address"] = address
    query = re.sub(r"^〒\d{3}-\d{4}\s*", "", address)
    row["maps_url"] = "https://www.google.com/maps/search/?api=1&query=" + quote(query)

with path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["company_name", "url", "address", "phone", "maps_url", "status"],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"cleaned={len(rows)}")
