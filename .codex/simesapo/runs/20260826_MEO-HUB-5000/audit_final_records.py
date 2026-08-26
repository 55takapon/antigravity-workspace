import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


def norm_name(value):
    return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (value or "").lower())


def norm_domain(value):
    host = urlparse(value or "").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def norm_phone(value):
    digits = re.sub(r"\D", "", value or "")
    return digits if len(digits) >= 9 else ""


rows = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))


def duplicates(values):
    counts = Counter(value for value in values if value)
    return sorted((value, count) for value, count in counts.items() if count > 1)


report = {
    "rows": len(rows),
    "blank_company_name": sum(not row.get("company_name") for row in rows),
    "blank_url": sum(not row.get("url") for row in rows),
    "duplicate_names": duplicates(norm_name(row.get("company_name")) for row in rows),
    "duplicate_domains": duplicates(norm_domain(row.get("url")) for row in rows),
    "duplicate_phones": duplicates(norm_phone(row.get("phone")) for row in rows),
}
Path(sys.argv[2]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({key: len(value) if isinstance(value, list) else value for key, value in report.items()}, ensure_ascii=False))
