import argparse
import sys
from pathlib import Path


REPO = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0, str(REPO / "shared"))
import sheets_io  # noqa: E402


parser = argparse.ArgumentParser()
parser.add_argument("spreadsheet")
parser.add_argument("--worksheet", required=True)
parser.add_argument("--company", required=True)
parser.add_argument("--phone", required=True)
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet)
rows = sheets_io.read_rows(ws, want=["company_name", "phone"])
matches = [
    row
    for row in rows
    if row.get("company_name") == args.company and row.get("phone") == args.phone
]
if len(matches) != 1:
    raise SystemExit(f"expected_one_match={len(matches)}")
row = matches[0]
print(f"target_row={row['_row']} company={row['company_name']} phone={row['phone']}")
if not args.apply:
    print("preview_only=true")
else:
    written = sheets_io.write_cells(
        ws, [{"_row": row["_row"], "phone": ""}], ["phone"], overwrite=True
    )
    print(f"cleared_cells={written}")
