from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
sys.path.insert(0, str(ROOT / ".agent/skills/simesapo-sales-skills-dist/shared"))
import sheets_io

TABS = ("送信済み251127", "送信済み251222", "Web幹事済み")


def norm_company(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = re.sub(r"株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|\(株\)|\(有\)|\(同\)", "", value)
    return re.sub(r"[\s\u3000・･.,，．_/'\"()（）\[\]［］-]", "", value)


def norm_domain(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if not re.match(r"^https?://", value, re.I):
        value = "https://" + value
    try:
        return re.sub(r"^www\.", "", (urlparse(value).hostname or "").lower().rstrip("."))
    except ValueError:
        return ""


def main() -> None:
    book = sheets_io.get_client(None).open_by_url(sys.argv[1])
    tab_stats = {}
    all_records = []
    sales_block = re.compile(r"(?:営業|売り込み|セールス|勧誘).{0,12}(?:お断り|禁止|不可|ご遠慮|受け付け)|(?:お断り|禁止|不可|ご遠慮).{0,12}(?:営業|売り込み|セールス|勧誘)", re.I)
    for tab in TABS:
        values = book.worksheet(tab).get_all_values()
        header = values[0]
        ix = {name: i for i, name in enumerate(header)}
        rows = []
        for row_number, raw in enumerate(values[1:], 2):
            if not any((v or "").strip() for v in raw):
                continue
            raw += [""] * max(0, len(header) - len(raw))
            get = lambda name: raw[ix[name]].strip() if name in ix else ""
            company, url = get("company_name"), get("url")
            domain, company_norm = norm_domain(url), norm_company(company)
            stable = ("domain", domain) if domain else ("company", company_norm)
            text = " ".join(raw)
            rec = {"tab": tab, "row": row_number, "company": company, "domain": domain, "company_norm": company_norm, "stable": stable}
            rows.append(rec); all_records.append(rec)
        domain_counts = Counter(r["domain"] for r in rows if r["domain"])
        company_counts = Counter(r["company_norm"] for r in rows if r["company_norm"])
        status_counts = Counter((values[n-1][ix["status"]].strip() if "status" in ix and len(values[n-1]) > ix["status"] else "") for n in [r["row"] for r in rows])
        sales_block_rows = sum(1 for r in rows if sales_block.search(" ".join(values[r["row"]-1])))
        tab_stats[tab] = {
            "rows": len(rows),
            "unique_domains": len(domain_counts),
            "duplicate_domain_rows": sum(c-1 for c in domain_counts.values() if c > 1),
            "unique_company_names": len(company_counts),
            "duplicate_company_rows": sum(c-1 for c in company_counts.values() if c > 1),
            "sales_block_text_rows": sales_block_rows,
            "filled": {name: sum(1 for r in rows if name in ix and len(values[r["row"]-1]) > ix[name] and values[r["row"]-1][ix[name]].strip()) for name in ("contact_url", "message", "sent_at", "status", "error_reason")},
            "status_top": status_counts.most_common(12),
            "headers": header,
        }
    stable_tabs = defaultdict(set)
    stable_counts = Counter()
    for r in all_records:
        stable_tabs[r["stable"]].add(r["tab"]); stable_counts[r["stable"]] += 1
    cross_keys = {k for k, tabs in stable_tabs.items() if len(tabs) > 1}
    output = {
        "tabs": tab_stats,
        "total_rows": len(all_records),
        "unique_company_or_domain": len(stable_counts),
        "all_duplicate_rows": sum(c-1 for c in stable_counts.values() if c > 1),
        "cross_tab_duplicate_entities": len(cross_keys),
        "cross_tab_redundant_rows": sum(stable_counts[k]-1 for k in cross_keys),
        "sales_block_text_rows_total": sum(v["sales_block_text_rows"] for v in tab_stats.values()),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
