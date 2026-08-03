from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).resolve().parent
INPUT = DATA_DIR / "_input_rows970_988_current.csv"
OUTPUT = DATA_DIR / "_contact_links_rows970_988_current.json"
UA = "Mozilla/5.0 (compatible; opener-generate-contact-audit/1.0)"
HINT = re.compile(r"contact|inquiry|otoiawase|toiawase|form|お問い合わせ|問い合わせ|問合せ|ご相談|mail", re.I)


def main() -> int:
    rows = list(csv.DictReader(INPUT.open(encoding="utf-8-sig", newline="")))
    results = []
    for row in rows:
        item = {"row": int(row["_row"]), "company_name": row["company_name"], "source_url": row["url"]}
        try:
            resp = requests.get(row["url"], headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
            soup = BeautifulSoup(resp.content, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = urljoin(resp.url, a.get("href", "").strip())
                text = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
                title = re.sub(r"\s+", " ", str(a.get("title") or a.get("aria-label") or "").strip())
                haystack = " ".join([href, text, title])
                if HINT.search(haystack):
                    record = {"href": href, "text": text[:160], "title": title[:160]}
                    if record not in links:
                        links.append(record)
            item.update({"status_code": resp.status_code, "final_url": resp.url, "links": links[:50]})
        except Exception as exc:  # noqa: BLE001
            item["error"] = f"{type(exc).__name__}: {exc}"
        results.append(item)
    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
