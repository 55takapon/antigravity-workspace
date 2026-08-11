from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"
NG = re.compile(
    r"営業(?:目的|メール|行為|の)?|売り込み|セールス|勧誘|宣伝(?:目的|・広告)?|広告(?:目的|掲載|営業)?|"
    r"営業・勧誘|営業及び勧誘|営業や勧誘|営業目的のお問い合わせ|営業メールお断り",
    re.I,
)


def scan(url: str) -> dict:
    out = {"url": url, "ok": False, "status_code": None, "final_url": "", "title": "", "forms": [],
           "iframes": [], "contact_links": [], "ng_matches": [], "text_excerpt": "", "error": ""}
    if not url:
        out["error"] = "contact_url blank"
        return out
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
        out["status_code"] = r.status_code
        out["final_url"] = r.url
        if not r.encoding or r.encoding.lower() in ("iso-8859-1", "ascii"):
            r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        out["title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
        for form in soup.find_all("form"):
            fields = form.find_all(["input", "textarea", "select"])
            out["forms"].append({
                "action": urljoin(r.url, form.get("action") or ""),
                "method": (form.get("method") or "get").lower(),
                "fields": len(fields),
                "types": [(x.get("type") or x.name or "").lower() for x in fields[:20]],
                "text": re.sub(r"\s+", " ", form.get_text(" ", strip=True))[:1200],
            })
        for frame in soup.find_all("iframe"):
            src = urljoin(r.url, frame.get("src") or "")
            if src:
                out["iframes"].append(src)
        for a in soup.find_all("a", href=True):
            txt = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
            href = urljoin(r.url, a["href"])
            if re.search(r"contact|inquiry|問.?合|相談|form", txt + " " + href, re.I):
                out["contact_links"].append({"text": txt[:160], "href": href})
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        out["text_excerpt"] = text[:5000]
        out["ng_matches"] = sorted(set(m.group(0) for m in NG.finditer(text)))[:50]
        out["ok"] = r.status_code < 400
        if r.status_code >= 400:
            out["error"] = f"HTTP {r.status_code}"
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def main() -> int:
    start, end = map(int, sys.argv[1:3])
    src = HERE / f"_snapshot_webkanji_rows{start}_{end}_current.json"
    rows = json.loads(src.read_text(encoding="utf-8"))
    results = []
    for r in rows:
        x = scan(r.get("contact_url", ""))
        x.update({"row": r["_row"], "company_name": r.get("company_name", "")})
        results.append(x)
        print(f"[{r['_row']}] status={x['status_code']} forms={len(x['forms'])} frames={len(x['iframes'])} ng={len(x['ng_matches'])} {r.get('company_name','')}", file=sys.stderr)
    out = HERE / f"_contact_scan_webkanji_rows{start}_{end}.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "rows": len(results), "http_ok": sum(bool(x["ok"]) for x in results),
        "with_forms": sum(bool(x["forms"]) for x in results),
        "with_iframes": sum(bool(x["iframes"]) for x in results),
        "ng_candidates": [x["row"] for x in results if x["ng_matches"]],
        "errors": [x["row"] for x in results if x["error"]], "out": str(out),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
