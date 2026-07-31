import argparse
import json
from pathlib import Path


def clipped(value, limit):
    return str(value or "")[:limit]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_dir")
    parser.add_argument("--max-bytes", type=int, default=18000)
    args = parser.parse_args()

    rows = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    reduced = []
    for row in rows:
        reduced.append({
            "idx": row.get("idx"),
            "_row": row.get("_row"),
            "company_name": clipped(row.get("company_name"), 160),
            "base_url": clipped(row.get("base_url"), 500),
            "links": [
                {
                    "href": clipped(link.get("href"), 500),
                    "text": clipped(link.get("text"), 160),
                    "alt_title": clipped(link.get("alt_title"), 160),
                }
                for link in (row.get("links") or [])[:25]
            ],
        })

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("chunk_*.json"):
        old.unlink()

    chunks = []
    current = []
    for row in reduced:
        trial = current + [row]
        size = len(json.dumps(trial, ensure_ascii=False).encode("utf-8"))
        if current and size > args.max_bytes:
            chunks.append(current)
            current = [row]
        else:
            current = trial
    if current:
        chunks.append(current)

    for index, chunk in enumerate(chunks):
        path = output_dir / f"chunk_{index:03d}.json"
        path.write_text(json.dumps(chunk, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "rows": len(reduced),
        "chunks": len(chunks),
        "max_chunk_bytes": max(
            len(json.dumps(chunk, ensure_ascii=False).encode("utf-8"))
            for chunk in chunks
        ),
    }))


if __name__ == "__main__":
    main()
