import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist" / "shared"
sys.path.insert(0, str(SHARED))
import sheets_io  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spreadsheet")
    parser.add_argument("worksheet")
    parser.add_argument("csv_path")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    with Path(args.csv_path).open(encoding="utf-8-sig", newline="") as handle:
        values = list(csv.reader(handle))
    print(f"rows={len(values) - 1} cols={len(values[0])}")
    if args.preview:
        return 0

    client = sheets_io.get_client()
    sh = client.open_by_url(args.spreadsheet)
    ws = sh.worksheet(args.worksheet)
    if ws.row_count < len(values) or ws.col_count < len(values[0]):
        ws.resize(rows=max(ws.row_count, len(values)), cols=max(ws.col_count, len(values[0])))
    ws.clear()
    for start in range(0, len(values), 400):
        ws.update(values=values[start:start + 400], range_name=f"A{start + 1}", value_input_option="RAW")
    print("write_complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
