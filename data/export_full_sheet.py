import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist" / "shared"
sys.path.insert(0, str(SHARED))
import sheets_io  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spreadsheet")
    parser.add_argument("--worksheet", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--meta", required=True)
    args = parser.parse_args()

    ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet)
    values = ws.get_all_values()
    header = values[0] if values else []
    width = max((len(row) for row in values), default=len(header))
    header = header + [f"__col_{i + 1}" for i in range(len(header), width)]
    rows = []
    for physical_row, raw in enumerate(values[1:], start=2):
        padded = raw + [""] * (width - len(raw))
        if not any(cell.strip() for cell in padded):
            continue
        row = {header[i]: padded[i] for i in range(width)}
        row["_row"] = physical_row
        rows.append(row)

    output = Path(args.csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["_row", *header])
        writer.writeheader()
        writer.writerows(rows)
    Path(args.meta).write_text(
        json.dumps({"worksheet": ws.title, "rows": len(rows), "columns": width, "header": header}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"rows": len(rows), "columns": width, "header": header}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
