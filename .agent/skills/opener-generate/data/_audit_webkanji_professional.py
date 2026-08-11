#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
SKILL_DIR = DATA_DIR.parent
REPO_ROOT = SKILL_DIR.parents[2]
SCRIPTS_DIR = SKILL_DIR / "scripts"
SHARED_DIR = REPO_ROOT / "shared"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SHARED_DIR))

import assemble_openers as assemble  # noqa: E402
import opener_helpers as helpers  # noqa: E402
import sheets_io  # noqa: E402


BANNED = (
    "目が留まりました。",
    "おられるのですね。",
    "のですね。",
    "強く惹かれました。",
)


def nonspace_len(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def ending(paragraph: str) -> str:
    lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def stats(values: list[int]) -> dict:
    return {
        "min": min(values),
        "median": statistics.median(values),
        "mean": round(statistics.mean(values), 1),
        "max": max(values),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--worksheet", required=True)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    start, end = int(config["start"]), int(config["end"])

    ws = sheets_io.open_worksheet(args.sheet, args.worksheet)
    rows = sheets_io.read_rows(
        ws,
        want=["company_name", "url", "contact_url", "message", "status", "error_reason"],
        aliases={
            "status": ["status", "ステータス"],
            "error_reason": ["error_reason", "理由", "エラー理由"],
        },
        require=["company_name", "url", "message"],
    )
    row_map = {int(row["_row"]): row for row in rows if start <= int(row["_row"]) <= end}

    common_body = helpers.load_common_body()
    intro_tmpl = helpers.load_intro()
    sender = helpers.load_sender_info()

    issues: dict[str, list] = {
        "missing_results": [],
        "paragraph_issues": [],
        "length_issues": [],
        "max_line_issues": [],
        "banned_phrase_issues": [],
        "exact_message_mismatches": [],
        "eligible_metadata_nonblank": [],
        "eligible_required_field_blanks": [],
        "blocked_message_nonblank": [],
        "blocked_metadata_mismatches": [],
        "fix_mismatches": [],
        "ending_concentration_issues": [],
    }
    chars: list[int] = []
    max_lines: list[int] = []
    line_counts: list[int] = []
    openers: list[str] = []
    paragraph_endings: list[list[str]] = [[], [], []]

    for task in tasks:
        idx = str(task["idx"])
        row_no = int(task["_row"])
        opener = str(results.get(idx, "")).strip()
        live = row_map.get(row_no, {})
        if not opener:
            issues["missing_results"].append(row_no)
            continue

        paragraphs = [p.strip() for p in re.split(r"(?:\r?\n){2,}", opener) if p.strip()]
        lines = [line.strip() for line in opener.splitlines() if line.strip()]
        char_count = nonspace_len(opener)
        max_line = max(nonspace_len(line) for line in lines)
        chars.append(char_count)
        max_lines.append(max_line)
        line_counts.append(len(lines))
        openers.append(opener)

        if len(paragraphs) != 3:
            issues["paragraph_issues"].append({"row": row_no, "count": len(paragraphs)})
        else:
            for pos, paragraph in enumerate(paragraphs):
                paragraph_endings[pos].append(ending(paragraph))
        if not 100 <= char_count <= 165:
            issues["length_issues"].append({"row": row_no, "chars": char_count})
        if max_line > 34:
            issues["max_line_issues"].append({"row": row_no, "max_line": max_line})
        for phrase in BANNED:
            if phrase in opener:
                issues["banned_phrase_issues"].append({"row": row_no, "phrase": phrase})

        expected = assemble._build_message(
            str(task.get("company_name", "")).strip(), opener, common_body, intro_tmpl, sender
        ).strip()
        if str(live.get("message", "")).strip() != expected:
            issues["exact_message_mismatches"].append(row_no)
        if str(live.get("status", "")).strip() or str(live.get("error_reason", "")).strip():
            issues["eligible_metadata_nonblank"].append(row_no)
        blanks = [key for key in ("company_name", "url", "contact_url") if not str(live.get(key, "")).strip()]
        if blanks:
            issues["eligible_required_field_blanks"].append({"row": row_no, "fields": blanks})

    for row_text, spec in config.get("blocked", {}).items():
        row_no = int(row_text)
        live = row_map.get(row_no, {})
        if str(live.get("message", "")).strip():
            issues["blocked_message_nonblank"].append(row_no)
        actual = (str(live.get("status", "")).strip(), str(live.get("error_reason", "")).strip())
        expected = (str(spec.get("status", "")).strip(), str(spec.get("reason", "")).strip())
        if actual != expected:
            issues["blocked_metadata_mismatches"].append(
                {"row": row_no, "expected": expected, "actual": actual}
            )

    for field, config_key in (
        ("company_name", "company_fixes"),
        ("url", "url_fixes"),
        ("contact_url", "contact_fixes"),
    ):
        for row_text, expected in config.get(config_key, {}).items():
            row_no = int(row_text)
            actual = str(row_map.get(row_no, {}).get(field, "")).strip()
            if actual != str(expected).strip():
                issues["fix_mismatches"].append(
                    {"row": row_no, "field": field, "expected": expected, "actual": actual}
                )

    ending_summary = []
    for pos, values in enumerate(paragraph_endings, start=1):
        counts = Counter(values)
        top_ending, top_count = counts.most_common(1)[0]
        share = round(top_count / len(values), 3)
        ending_summary.append(
            {"paragraph": pos, "distinct": len(counts), "top_ending": top_ending, "top_count": top_count, "top_share": share}
        )
        if share > 0.20:
            issues["ending_concentration_issues"].append(
                {"paragraph": pos, "ending": top_ending, "count": top_count, "share": share}
            )

    unique_openers = len(set(openers))
    if unique_openers != len(openers):
        issues["ending_concentration_issues"].append(
            {"duplicate_openers": len(openers) - unique_openers}
        )

    ok = all(not values for values in issues.values())
    report = {
        "worksheet": args.worksheet,
        "range": [start, end],
        "physical_rows": end - start + 1,
        "eligible_rows": len(tasks),
        "message_nonblank": sum(bool(str(row_map.get(int(t["_row"]), {}).get("message", "")).strip()) for t in tasks),
        "unique_openers": unique_openers,
        "blocked_rows": sorted(int(row) for row in config.get("blocked", {})),
        "opener_chars": stats(chars),
        "max_line_chars": stats(max_lines),
        "nonblank_lines": stats(line_counts),
        "paragraph_ending_diversity": ending_summary,
        **issues,
        "ok": ok,
    }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
