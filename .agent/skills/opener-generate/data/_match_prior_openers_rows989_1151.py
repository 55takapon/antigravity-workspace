from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


DATA_DIR = Path(__file__).resolve().parent
CURRENT = DATA_DIR / "_snapshot_rows989_1151_current.json"
PAIRS = [
    (DATA_DIR / "_tasks_rows969_1018.json", DATA_DIR / "_results_rows969_1018.json"),
    (DATA_DIR / "_tasks_rows1019_1068.json", DATA_DIR / "_results_rows1019_1068.json"),
]


def norm_company(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "")).lower()


def norm_host(value: str) -> str:
    raw = (value or "").strip()
    if raw and "://" not in raw:
        raw = "https://" + raw
    host = (urlparse(raw).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def paragraphs(value: str) -> int:
    return len([part for part in value.replace("\r\n", "\n").split("\n\n") if part.strip()])


def main() -> int:
    current = json.loads(CURRENT.read_text(encoding="utf-8"))
    candidates = []
    for tasks_path, results_path in PAIRS:
        tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
        results = json.loads(results_path.read_text(encoding="utf-8"))
        for task in tasks:
            opener = (results.get(str(task["idx"])) or "").strip()
            if not opener:
                continue
            candidates.append(
                {
                    "company_key": norm_company(task.get("company_name", "")),
                    "host": norm_host(task.get("url", "")),
                    "company_name": task.get("company_name", ""),
                    "url": task.get("url", ""),
                    "opener": opener,
                    "paragraphs": paragraphs(opener),
                    "source_tasks": tasks_path.name,
                    "source_row": task.get("_row"),
                }
            )

    matches = []
    unmatched = []
    ambiguous = []
    for row in current:
        company_key = norm_company(row["company_name"])
        host = norm_host(row["url"])
        found = [item for item in candidates if item["company_key"] == company_key and item["host"] == host]
        unique = {(item["opener"], item["source_tasks"], item["source_row"]): item for item in found}
        found = list(unique.values())
        if len(found) == 1:
            item = found[0]
            matches.append(
                {
                    "_row": row["_row"],
                    "company_name": row["company_name"],
                    "url": row["url"],
                    "contact_url": row["contact_url"],
                    "opener": item["opener"],
                    "paragraphs": item["paragraphs"],
                    "source_tasks": item["source_tasks"],
                    "source_row": item["source_row"],
                }
            )
        elif len(found) > 1:
            ambiguous.append({"_row": row["_row"], "company_name": row["company_name"], "matches": len(found)})
        else:
            unmatched.append(row)

    output = {
        "matches": matches,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
    }
    out_path = DATA_DIR / "_prior_match_rows989_1151.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "current_rows": len(current),
        "prior_candidates": len(candidates),
        "matches": len(matches),
        "three_paragraph_matches": sum(1 for item in matches if item["paragraphs"] == 3),
        "unmatched": len(unmatched),
        "ambiguous": len(ambiguous),
        "matched_first": [item["_row"] for item in matches[:5]],
        "matched_last": [item["_row"] for item in matches[-5:]],
        "unmatched_first": [item["_row"] for item in unmatched[:10]],
        "output": str(out_path),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not ambiguous else 2


if __name__ == "__main__":
    raise SystemExit(main())
