import csv
import re
import sys
from pathlib import Path


RELATIONSHIP = re.compile(
    r"支援|受託|代行|コンサル|制作|請負|広告代理|提供|運用|保守"
)


def main() -> None:
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys()) if rows else []

    kept = [
        row
        for row in rows
        if RELATIONSHIP.search(row.get("business_description", ""))
    ]

    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    print(f"input={len(rows)} kept={len(kept)} removed={len(rows) - len(kept)}")


if __name__ == "__main__":
    main()
