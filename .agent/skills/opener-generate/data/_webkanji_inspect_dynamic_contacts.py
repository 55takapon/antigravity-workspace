from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"


def inspect(page, label: str, url: str) -> dict:
    out = {"label": label, "url": url, "ok": False, "status": None, "final_url": "", "title": "",
           "forms": [], "frames": [], "links": [], "scripts": [], "page_fields": [], "text": "", "error": ""}
    try:
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            out["status"] = resp.status if resp else None
        except PlaywrightTimeoutError as e:
            out["error"] = f"TimeoutError: {e}"
        page.wait_for_timeout(3000)
        out["final_url"] = page.url
        out["title"] = page.title()
        out["forms"] = page.locator("form").count()
        out["page_fields"] = page.locator("input:not([type=hidden]), textarea, select").evaluate_all(
            "els => els.slice(0,80).map(e => ({tag:e.tagName,type:e.type||'',name:e.name||'',placeholder:e.placeholder||''}))"
        )
        out["links"] = page.locator("a").evaluate_all(
            "els => els.map(e => ({text:(e.innerText||'').trim(),href:e.href||''})).filter(x => /contact|inquiry|問.?合|相談|form/i.test(x.text+' '+x.href)).slice(0,50)"
        )
        out["scripts"] = page.locator("script[src]").evaluate_all(
            "els => els.map(e=>e.src).filter(x => /form|hubspot|formrun|formzu|mail|contact|inquiry/i.test(x)).slice(0,50)"
        )
        for frame in page.frames[1:]:
            try:
                out["frames"].append({"url": frame.url, "forms": frame.locator("form").count(),
                                      "fields": frame.locator("input:not([type=hidden]), textarea, select").count()})
            except Exception as e:
                out["frames"].append({"url": frame.url, "error": str(e)})
        out["text"] = re.sub(r"\s+", " ", page.locator("body").inner_text(timeout=5000))[:10000]
        frame_ok = any((x.get("forms", 0) or x.get("fields", 0)) for x in out["frames"])
        out["ok"] = bool(out["forms"] or out["page_fields"] or frame_ok)
    except Exception as e:
        out["error"] = ((out["error"] + " | ") if out["error"] else "") + f"{type(e).__name__}: {e}"
    return out


def main() -> int:
    src, dest = Path(sys.argv[1]), Path(sys.argv[2])
    items = json.loads(src.read_text(encoding="utf-8"))
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True, user_agent=UA, viewport={"width": 1365, "height": 1000})
        for item in items:
            page = context.new_page()
            r = inspect(page, str(item.get("label", "")), item["url"])
            page.close()
            results.append(r)
            dest.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{r['label']}] ok={r['ok']} status={r['status']} forms={r['forms']} fields={len(r['page_fields'])} frames={len(r['frames'])}", file=sys.stderr)
        context.close()
        browser.close()
    print(json.dumps({"items": len(results), "ok": sum(bool(x["ok"]) for x in results), "out": str(dest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
