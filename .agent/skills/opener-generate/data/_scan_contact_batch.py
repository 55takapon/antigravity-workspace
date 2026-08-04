from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup


UA = "Mozilla/5.0 (compatible; opener-generate-contact-audit/1.0)"
KEYWORDS = re.compile(r"営業|売り込み|セールス|販促|勧誘|迷惑メール|お断り|遠慮|禁止", re.I)


def decode(resp: requests.Response) -> str:
    enc = resp.encoding
    if not enc or enc.lower() in {"iso-8859-1", "ascii"}:
        enc = resp.apparent_encoding or "utf-8"
    return resp.content.decode(enc, errors="replace")


def scan(row: dict[str, str]) -> dict:
    record = {
        "row": int(row["_row"]),
        "company_name": row["company_name"],
        "contact_url": row["contact_url"],
    }
    try:
        resp = requests.get(row["contact_url"], headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
        soup = BeautifulSoup(decode(resp), "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        metrics = {
            "forms": len(soup.find_all("form")),
            "textareas": len(soup.find_all("textarea")),
            "inputs": len(soup.find_all("input")),
            "selects": len(soup.find_all("select")),
            "mailto_links": len(soup.select('a[href^="mailto:"]')),
            "iframes": len(soup.find_all("iframe")),
        }
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        lines = [re.sub(r"\s+", " ", line).strip() for line in soup.get_text("\n").splitlines()]
        lines = [line for line in lines if line]
        contexts = []
        for i, line in enumerate(lines):
            if KEYWORDS.search(line):
                context = " / ".join(lines[max(0, i - 1) : min(len(lines), i + 2)])[:700]
                if context not in contexts:
                    contexts.append(context)
        record.update(
            {
                "status_code": resp.status_code,
                "final_url": resp.url,
                "title": title,
                "text_length": sum(len(line) for line in lines),
                **metrics,
                "keyword_contexts": contexts[:15],
            }
        )
    except Exception as exc:  # noqa: BLE001
        record["error"] = f"{type(exc).__name__}: {exc}"
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    args = ap.parse_args()
    rows = list(csv.DictReader(Path(args.input).open(encoding="utf-8", newline="")))
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(scan, rows))
    results.sort(key=lambda item: item["row"])
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    suspects = [
        item
        for item in results
        if item.get("status_code") != 200
        or item.get("error")
        or item.get("keyword_contexts")
        or (item.get("forms", 0) == 0 and item.get("mailto_links", 0) == 0)
    ]
    report = {
        "rows": len(results),
        "http_200": sum(1 for item in results if item.get("status_code") == 200),
        "errors": sum(1 for item in results if item.get("error")),
        "with_forms": sum(1 for item in results if item.get("forms", 0) > 0),
        "suspects": suspects,
        "output": args.output,
    }
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
