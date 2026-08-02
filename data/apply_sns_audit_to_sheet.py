import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist" / "shared"
sys.path.insert(0, str(SHARED))
import sheets_io  # noqa: E402


def read_csv(path: str) -> tuple[list[str], list[list[str]]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    return rows[0], rows[1:]


def write_table(ws, header: list[str], rows: list[list[str]]) -> None:
    required_rows = len(rows) + 1
    required_cols = len(header)
    if ws.row_count < required_rows or ws.col_count < required_cols:
        ws.resize(rows=max(ws.row_count, required_rows), cols=max(ws.col_count, required_cols))
    ws.clear()
    values = [header, *rows]
    for start in range(0, len(values), 400):
        chunk = values[start:start + 400]
        ws.update(values=chunk, range_name=f"A{start + 1}", value_input_option="RAW")


def get_or_create(sh, title: str, columns: int):
    try:
        return sh.worksheet(title)
    except Exception:
        return sh.add_worksheet(title=title, rows=1000, cols=max(columns, 20))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spreadsheet")
    parser.add_argument("--worksheet", default="SNS運用")
    parser.add_argument("--main", required=True)
    parser.add_argument("--excluded", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--skip-backup", action="store_true")
    args = parser.parse_args()
    main_header, main_rows = read_csv(args.main)
    excluded_header, excluded_rows = read_csv(args.excluded)
    review_header, review_rows = read_csv(args.review)
    print(f"main={len(main_rows)} cols={len(main_header)}")
    print(f"excluded={len(excluded_rows)} cols={len(excluded_header)} -> SNS監査除外")
    print(f"review={len(review_rows)} cols={len(review_header)} -> SNS要確認")
    print(f"main_header={main_header}")
    if args.preview:
        print("preview only: no cells written")
        return 0

    client = sheets_io.get_client()
    sh = client.open_by_url(args.spreadsheet) if args.spreadsheet.startswith("http") else client.open_by_key(args.spreadsheet)
    source = sh.worksheet(args.worksheet)
    backup_title = "skipped"
    if not args.skip_backup:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_title = f"SNS運用_監査前_{stamp}"
        sh.duplicate_sheet(source.id, new_sheet_name=backup_title)
    write_table(source, main_header, main_rows)
    excluded_ws = get_or_create(sh, "SNS監査除外", len(excluded_header))
    review_ws = get_or_create(sh, "SNS要確認", len(review_header))
    write_table(excluded_ws, excluded_header, excluded_rows)
    write_table(review_ws, review_header, review_rows)
    print(f"done backup={backup_title} main={len(main_rows)} excluded={len(excluded_rows)} review={len(review_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
