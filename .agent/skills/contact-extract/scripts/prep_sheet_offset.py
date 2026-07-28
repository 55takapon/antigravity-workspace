import argparse
import concurrent.futures
import json
from pathlib import Path

import fetch_pages

import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared"))
import sheets_io  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spreadsheet")
    parser.add_argument("out")
    parser.add_argument("--worksheet", default="シート1")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()

    ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet)
    rows = sheets_io.read_rows(ws, want=["company_name", "url", "contact_url"])
    targets = [r for r in rows if r.get("url") and not r.get("contact_url")]
    selected = targets[args.offset : args.offset + args.limit]

    pages = [None] * len(selected)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(fetch_pages.extract_links, r.get("url", "")): i for i, r in enumerate(selected)}
        for f in concurrent.futures.as_completed(fut):
            i = fut[f]
            try:
                data = f.result()
            except Exception:
                data = {"base_url": selected[i].get("url", ""), "links": []}
            pages[i] = {
                "idx": i,
                "_row": selected[i].get("_row"),
                "company_name": selected[i].get("company_name", ""),
                **data,
            }

    Path(args.out).write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    got = sum(1 for p in pages if p.get("links"))
    print(f"[done] offset={args.offset} selected={len(selected)} links={got} remaining={len(targets)} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
