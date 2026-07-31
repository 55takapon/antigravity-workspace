import argparse
import concurrent.futures
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
SCRIPTS = SKILL / ".claude" / "skills" / "002-contact-extract" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SKILL / "shared"))

import fetch_pages  # noqa: E402
import sheets_io  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spreadsheet")
    parser.add_argument("--worksheet", required=True)
    parser.add_argument("--start-row", type=int, required=True)
    parser.add_argument("--end-row", type=int, required=True)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet)
    rows = sheets_io.read_rows(
        ws,
        want=["company_name", "url", "contact_url", "status"],
    )
    targets = [
        row for row in rows
        if args.start_row <= int(row.get("_row") or 0) <= args.end_row
        and row.get("url")
        and not row.get("contact_url")
        and str(row.get("status") or "").strip().lower() != "excluded"
    ]

    batch = [None] * len(targets)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(fetch_pages.extract_links, row["url"]): index
            for index, row in enumerate(targets)
        }
        done = 0
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            try:
                material = future.result()
            except Exception:
                material = {"base_url": targets[index]["url"], "links": []}
            batch[index] = {
                "idx": index,
                "_row": targets[index]["_row"],
                "company_name": targets[index].get("company_name", ""),
                **material,
            }
            done += 1
            if done % 25 == 0 or done == len(targets):
                print(f"progress={done}/{len(targets)}", flush=True)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")
    linked = sum(bool(item and item.get("links")) for item in batch)
    print(json.dumps({
        "target_rows": len(targets),
        "links_obtained": linked,
        "start_row": args.start_row,
        "end_row": args.end_row,
        "output": str(output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
