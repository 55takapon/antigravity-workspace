import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


CONTACT_RE = re.compile(
    r"contact|inquiry|toiawase|otoiawase|mailform|mail|form|apply|estimate|consult|相談|問合|問い合|お問い合わせ|お問合せ|見積|資料請求|依頼",
    re.IGNORECASE,
)
BAD_RE = re.compile(r"privacy|policy|sitemap|recruit|career|blog|news|tel:", re.IGNORECASE)
COMMON_PATHS = [
    "/contact",
    "/contact/",
    "/contact.html",
    "/contact.php",
    "/inquiry",
    "/inquiry/",
    "/inquiry.html",
    "/form",
    "/form/",
    "/mailform",
    "/mail/",
    "/toiawase",
    "/otoiawase",
    "/estimate",
]


def same_site(base: str, target: str) -> bool:
    try:
        b = urlparse(base)
        t = urlparse(target)
        return not t.netloc or t.netloc.lower().replace("www.", "") == b.netloc.lower().replace("www.", "")
    except Exception:
        return False


def allowed_external(target: str) -> bool:
    host = urlparse(target).netloc.lower()
    return host.endswith("docs.google.com") or host.endswith("forms.gle")


def pick_link(page: dict) -> str:
    base = page.get("base_url") or ""
    best = []
    for link in page.get("links") or []:
        href = str(link.get("href") or "").strip()
        if not href or href.startswith(("tel:", "mailto:", "javascript:")):
            continue
        value = " ".join(str(link.get(k) or "") for k in ("href", "text", "alt_title"))
        if not CONTACT_RE.search(value) or BAD_RE.search(value):
            continue
        url = urljoin(base, href)
        if same_site(base, url) or allowed_external(url):
            score = 10
            if "#contact" in url.lower():
                score += 3
            if "contact" in url.lower() or "inquiry" in url.lower():
                score += 4
            best.append((score, url))
    if best:
        best.sort(reverse=True)
        return best[0][1]
    return ""


def probe(base: str, timeout: float) -> str:
    parsed = urlparse(base)
    if not parsed.scheme or not parsed.netloc:
        return ""
    root = f"{parsed.scheme}://{parsed.netloc}"
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 contact-url-check"}
    for path in COMMON_PATHS:
        url = root + path
        try:
            resp = session.head(url, allow_redirects=True, timeout=timeout, headers=headers)
            if resp.status_code in (405, 403):
                resp = session.get(url, allow_redirects=True, timeout=timeout, headers=headers, stream=True)
            if 200 <= resp.status_code < 400:
                final = resp.url
                final_path = urlparse(final).path.lower().rstrip("/")
                if same_site(base, final) and CONTACT_RE.search(final_path):
                    return final
        except Exception:
            continue
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--timeout", type=float, default=4.0)
    args = parser.parse_args()

    pages = json.loads(Path(args.src).read_text(encoding="utf-8"))
    results = []
    for page in pages:
        url = pick_link(page)
        method = "link" if url else ""
        if not url and args.probe:
            url = probe(page.get("base_url") or "", args.timeout)
            method = "link" if url else ""
        if url:
            results.append(
                {
                    "idx": page.get("idx"),
                    "contact_url": url,
                    "method": method,
                    "confidence": "high" if method == "link" else "medium",
                }
            )

    Path(args.dst).write_text(
        json.dumps({"version": "local-contact-detect", "results": results}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[done] detected={len(results)}/{len(pages)} -> {args.dst}")


if __name__ == "__main__":
    main()
