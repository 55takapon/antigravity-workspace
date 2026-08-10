from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


def inspect(page, label: str, url: str) -> dict:
    out = {"label": label, "url": url, "ok": False, "status": None, "final_url": "", "title": "",
           "forms": [], "frames": [], "links": [], "scripts": [], "page_fields": 0,
           "text": "", "error": ""}
    try:
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
        except PlaywrightTimeoutError as e:
            resp = None
            out["error"] = f"{type(e).__name__}: {e}"
        page.wait_for_timeout(1500)
        out["status"] = resp.status if resp else None
        out["final_url"] = page.url
        out["title"] = page.title()
        for form in page.locator("form").all():
            out["forms"].append({"action": form.get_attribute("action") or "",
                                 "fields": form.locator("input,textarea,select").count(),
                                 "text": re.sub(r"\s+", " ", form.inner_text())[:700]})
        for frame in page.frames[1:]:
            try:
                out["frames"].append({"url": frame.url, "forms": frame.locator("form").count(),
                                      "fields": frame.locator("input,textarea,select").count(),
                                      "text": re.sub(r"\s+", " ", frame.locator("body").inner_text())[:700]})
            except Exception as e:
                out["frames"].append({"url": frame.url, "error": str(e)})
        out["page_fields"] = page.locator("input,textarea,select").count()
        for script in page.locator("script[src]").all():
            src = script.get_attribute("src") or ""
            if re.search(r"form|hubspot|formrun|formzu|mail|contact|inquiry", src, re.I):
                out["scripts"].append(src)
        for a in page.locator("a").all()[:300]:
            try:
                text = re.sub(r"\s+", " ", a.inner_text()).strip()
                href = a.get_attribute("href") or ""
                if re.search(r"contact|inquiry|問.?合|相談|見積", text + " " + href, re.I):
                    out["links"].append({"text": text[:100], "href": href})
            except Exception:
                pass
        out["text"] = re.sub(r"\s+", " ", page.locator("body").inner_text())[:3000]
        out["ok"] = bool(out["forms"] or out["page_fields"] or any(f.get("forms") or f.get("fields") for f in out["frames"]))
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def main() -> int:
    inp, outp = map(Path, sys.argv[1:3])
    urls = json.loads(inp.read_text(encoding="utf-8"))
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True, viewport={"width": 1280, "height": 900})
        for label, url in urls.items():
            page = context.new_page()
            page.set_default_timeout(5000)
            result = inspect(page, label, url)
            results.append(result)
            outp.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{label}: status={result['status']} forms={len(result['forms'])} frames={len(result['frames'])}", file=sys.stderr, flush=True)
            page.close()
        context.close()
        browser.close()
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(outp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
