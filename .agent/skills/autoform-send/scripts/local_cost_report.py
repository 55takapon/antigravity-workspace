"""Sprint 6 Task 7 — Local cost report.

Reads `skill/data/skill_local.db` (the per-call ai_usage_logs table) and
prints a provider/model breakdown of token + JPY cost.

Usage:
    uv run python scripts/local_cost_report.py
    uv run python scripts/local_cost_report.py --since 2026-06-01
    uv run python scripts/local_cost_report.py --provider general_form
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# Make skill/core/ importable when this script is invoked directly.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILL_CORE_DIR = _REPO_ROOT / "skill" / "core"
for _entry in (_SKILL_CORE_DIR, _REPO_ROOT):
    if str(_entry) not in sys.path:
        sys.path.insert(0, str(_entry))


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="local_cost_report.py")
    parser.add_argument(
        "--since",
        default=None,
        help="ended_at >= ISO-8601 date (e.g. 2026-06-01)",
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=["browser_use", "general_form", "workflow_cache", "http_post", "none"],
        help="Filter by provider_used",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        from skill.core._local_db import init_schema, resolve_db_path
        from skill.core._usage_logger import aggregate_by_provider
    except ImportError:
        from _local_db import init_schema, resolve_db_path  # type: ignore
        from _usage_logger import aggregate_by_provider  # type: ignore

    init_schema()
    db_path = resolve_db_path()
    rows = aggregate_by_provider(since=args.since)
    if args.provider:
        rows = [r for r in rows if r["provider_used"] == args.provider]

    print(f"=== Local AI usage report ({db_path}) ===")
    if args.since:
        print(f"since: {args.since}")
    if args.provider:
        print(f"provider: {args.provider}")
    if not rows:
        print("(no rows)")
        return 0

    header = (
        f"{'provider':<16} {'model':<24} {'calls':>6} "
        f"{'in_tok':>10} {'out_tok':>10} {'USD':>10} {'JPY':>10}"
    )
    print(header)
    print("-" * len(header))
    total_usd = 0.0
    total_jpy = 0.0
    for r in rows:
        usd = r.get("sum_usd") or 0.0
        jpy = r.get("sum_jpy") or 0.0
        total_usd += usd
        total_jpy += jpy
        print(
            f"{r['provider_used']:<16} {r['model']:<24} "
            f"{r['call_count']:>6} "
            f"{int(r.get('sum_input') or 0):>10} "
            f"{int(r.get('sum_output') or 0):>10} "
            f"{usd:>10.4f} {jpy:>10.2f}"
        )
    print("-" * len(header))
    print(f"{'TOTAL':<16} {'':<24} {'':>6} {'':>10} {'':>10} "
          f"{total_usd:>10.4f} {total_jpy:>10.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
