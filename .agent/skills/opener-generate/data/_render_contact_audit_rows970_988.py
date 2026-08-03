from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


OUTPUT = Path(__file__).resolve().parent / "_render_contact_audit_rows970_988_current.json"
TARGETS = [
    (970, "https://neo-promotion.co.jp/contact/"),
    (971, "https://www.regionline.jp/#contact"),
    (972, "https://beewave.co.jp/otoiawase"),
    (980, "https://smart-company.co.jp/#contact"),
    (983, "https://jei-one.co.jp/contact/"),
    (985, "https://www.san-ad.co.jp/form/contact/"),
]
KEYWORDS = re.compile(r"営業|売り込み|セールス|販促|勧誘|迷惑メール|お断り|遠慮|禁止", re.I)


def main() -> int:
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        for row_no, url in TARGETS:
            item = {"row": row_no, "url": url}
            try:
                response = page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                response = None
            try:
                body = page.locator("body").inner_text(timeout=5000)
                lines = [re.sub(r"\s+", " ", x).strip() for x in body.splitlines() if x.strip()]
                contexts = []
                for i, line in enumerate(lines):
                    if KEYWORDS.search(line):
                        snippet = " / ".join(lines[max(0, i - 1) : min(len(lines), i + 2)])
                        if snippet not in contexts:
                            contexts.append(snippet[:600])
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
                        "keyword_contexts": contexts[:12],
                        "body_excerpt": " / ".join(lines[:80])[:4000],
                    }
                )
            except Exception as exc:  # noqa: BLE001
                item["error"] = f"{type(exc).__name__}: {exc}"
            results.append(item)
        browser.close()
    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
