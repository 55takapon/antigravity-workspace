from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
NG_PATTERNS = [
    r"営業(?:活動|目的|メール|のご連絡|に関する|等)?[^。\n]{0,40}(?:お断り|ご遠慮|受け付けておりません|固くお断り)",
    r"売り込み[^。\n]{0,40}(?:お断り|ご遠慮|受け付けておりません)",
    r"セールス[^。\n]{0,40}(?:お断り|ご遠慮|受け付けておりません)",
]


def inspect(url: str) -> dict:
    out = {"url": url, "ok": False, "status_code": None, "final_url": "", "title": "",
           "forms": [], "iframes": [], "contact_links": [], "ng_matches": [],
           "text_excerpt": "", "error": ""}
    if not url or not url.lower().startswith(("http://", "https://")):
        out["error"] = "contact_urlがHTTP(S)ではありません"
        return out
    try:
        r = requests.get(url, headers=UA, timeout=25, allow_redirects=True)
        out["status_code"] = r.status_code
        out["final_url"] = r.url
        r.encoding = r.apparent_encoding or r.encoding
        soup = BeautifulSoup(r.text, "html.parser")
        out["title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        out["text_excerpt"] = text[:2500]
        for form in soup.find_all("form"):
            fields = form.find_all(["input", "textarea", "select"])
            out["forms"].append({
                "action": urljoin(r.url, form.get("action") or ""),
                "method": (form.get("method") or "get").lower(),
                "fields": len(fields),
                "types": [str(x.get("type") or x.name) for x in fields[:20]],
                "text": re.sub(r"\s+", " ", form.get_text(" ", strip=True))[:500],
            })
        out["iframes"] = [urljoin(r.url, x.get("src") or "") for x in soup.find_all("iframe") if x.get("src")]
        for a in soup.find_all("a", href=True):
            label = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
            href = urljoin(r.url, a["href"])
            if re.search(r"contact|inquiry|問.?合|相談|見積", label + " " + href, re.I):
                out["contact_links"].append({"text": label[:120], "href": href})
        for pat in NG_PATTERNS:
            out["ng_matches"].extend(m.group(0) for m in re.finditer(pat, text, re.I))
        out["ok"] = r.status_code < 400
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def main() -> int:
    start, end = map(int, sys.argv[1:3])
    data = Path(__file__).resolve().parent
    snap = json.loads((data / f"_snapshot_webkanji_rows{start}_{end}_current.json").read_text(encoding="utf-8"))
    results = []
    for i, row in enumerate(snap, 1):
        result = inspect((row.get("contact_url") or "").strip())
        result["_row"] = row["_row"]
        result["company_name"] = row.get("company_name", "")
        results.append(result)
        print(f"[{i}/{len(snap)}] row {row['_row']} forms={len(result['forms'])} status={result['status_code']}", file=sys.stderr)
    out = data / f"_contact_scan_webkanji_rows{start}_{end}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(results), "static_forms": sum(bool(x["forms"]) for x in results),
                      "ng": sum(bool(x["ng_matches"]) for x in results),
                      "http_errors": sum((x["status_code"] or 999) >= 400 for x in results)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
