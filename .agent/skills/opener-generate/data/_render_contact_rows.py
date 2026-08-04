from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


KEYWORDS = re.compile(r"営業|売り込み|セールス|販促|勧誘|迷惑メール|お断り|遠慮|禁止", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("rows")
    ap.add_argument("output")
    args = ap.parse_args()
    wanted = {int(value) for value in args.rows.split(",") if value.strip()}
    source = list(csv.DictReader(Path(args.input).open(encoding="utf-8", newline="")))
    targets = [row for row in source if int(row["_row"]) in wanted]
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        for row in targets:
            item = {"row": int(row["_row"]), "company_name": row["company_name"], "url": row["contact_url"]}
            try:
                response = page.goto(row["contact_url"], wait_until="networkidle", timeout=30000)
            except Exception:
                response = None
            try:
                body = page.locator("body").inner_text(timeout=5000)
                lines = [re.sub(r"\s+", " ", line).strip() for line in body.splitlines() if line.strip()]
                contexts = []
                for i, line in enumerate(lines):
                    if KEYWORDS.search(line):
                        context = " / ".join(lines[max(0, i - 1) : min(len(lines), i + 2)])[:700]
                        if context not in contexts:
                            contexts.append(context)
                links = page.locator("a").evaluate_all(
                    "els => els.map(e => ({href:e.href,text:(e.innerText||'').trim()}))"
                    ".filter(x => /contact|inquiry|form|問合|問い合|相談|営業/i.test(x.href+' '+x.text)).slice(0,30)"
                )
                item.update(
                    {
                        "status_code": response.status if response else None,
                        "final_url": page.url,
                        "title": page.title(),
                        "forms": page.locator("form").count(),
                        "visible_forms": page.locator("form:visible").count(),
                        "textareas": page.locator("textarea").count(),
                        "visible_textareas": page.locator("textarea:visible").count(),
                        "inputs": page.locator("input").count(),
                        "visible_inputs": page.locator("input:visible").count(),
                        "iframes": page.locator("iframe").count(),
                        "mailto_links": page.locator('a[href^="mailto:"]').evaluate_all(
                            "els => els.map(e => e.getAttribute('href'))"
                        ),
                        "keyword_contexts": contexts[:15],
                        "contact_links": links,
                        "body_excerpt": " / ".join(lines[:120])[:5000],
                    }
                )
            except Exception as exc:  # noqa: BLE001
                item["error"] = f"{type(exc).__name__}: {exc}"
            results.append(item)
        browser.close()
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
