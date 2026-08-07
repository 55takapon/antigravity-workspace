#!/usr/bin/env python3
"""Audit which current Sheet1 rows belong to the Aug 2-7 collection runs."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
RUNS = ROOT / "local_data" / "simesapo" / "runs"
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402


def domain(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    host = (urlparse(value).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def load_domains(path: Path) -> set[str]:
    for encoding in ("utf-8-sig", "cp932"):
        try:
            with path.open("r", encoding=encoding, newline="") as fh:
                rows = list(csv.DictReader(fh))
            break
        except UnicodeDecodeError:
            continue
    else:
        return set()
    if len(rows) not in (50, 200, 300):
        return set()
    result = set()
    for row in rows:
        url = row.get("url") or row.get("URL") or row.get("公式URL") or ""
        d = domain(url)
        if d:
            result.add(d)
    return result


def main() -> None:
    files = []
    for path in RUNS.rglob("*.csv"):
        if not any(token in str(path) for token in ("20260802", "20260803", "20260804", "20260805", "20260806", "20260807")):
            continue
        name = path.name.lower()
        if "final" not in name:
            continue
        if "readback" in name:
            continue
        if not ("50" in name or "verified" in name):
            continue
        ds = load_domains(path)
        if len(ds) >= 45:
            files.append((path, ds))

    union = set().union(*(ds for _, ds in files)) if files else set()
    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key("1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ")
    ws = sh.worksheet("シート1")
    values = ws.get("A1:P", value_render_option="FORMATTED_VALUE")
    current = []
    for row_no, row in enumerate(values[1:], 2):
        d = domain(row[1] if len(row) > 1 else "")
        if d in union:
            current.append((row_no, d, row[0] if row else ""))

    duplicate_domains = [d for d, count in Counter(d for _, d, _ in current).items() if count > 1]
    result = {
        "candidate_final_files": len(files),
        "union_domains": len(union),
        "current_sheet_matches": len(current),
        "current_unique_matches": len({d for _, d, _ in current}),
        "duplicate_domains_in_matches": len(duplicate_domains),
        "first_match_row": min((r for r, _, _ in current), default=None),
        "last_match_row": max((r for r, _, _ in current), default=None),
        "matched_rows_outside_2066_4723": sum(1 for r, _, _ in current if r < 2066 or r > 4723),
        "unmatched_sheet_rows_inside_2066_4723": sum(
            1
            for r, row in enumerate(values[2065:4723], 2066)
            if domain(row[1] if len(row) > 1 else "") not in union
        ),
        "sample_files": [str(path.relative_to(ROOT)) for path, _ in files[:10]],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
