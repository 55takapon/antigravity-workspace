from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent


def compact(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    # Navigation-heavy beginnings are common; retain several separated windows so distinctive service facts survive.
    windows = [text[:700], text[700:1400], text[1400:2200], text[2200:3200]]
    out = " / ".join(w for w in windows if w)
    return out[:3200]


def main() -> int:
    start, end = map(int, sys.argv[1:3])
    path = DATA / f"_tasks_webkanji_rows{start}_{end}_raw.json"
    tasks = json.loads(path.read_text(encoding="utf-8"))
    rows = [{"idx": t["idx"], "row": start + int(t["idx"]), "company": t.get("company_name", ""),
             "url": t.get("url", ""), "evidence": compact(t.get("hp_text", ""))} for t in tasks]
    out = DATA / f"_compact_webkanji_rows{start}_{end}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
