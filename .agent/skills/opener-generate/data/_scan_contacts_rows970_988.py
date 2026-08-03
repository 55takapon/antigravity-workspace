from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).resolve().parent
INPUT = DATA_DIR / "_input_rows970_988_current.csv"
OUTPUT = DATA_DIR / "_contact_scan_rows970_988_current.json"
UA = "Mozilla/5.0 (compatible; opener-generate-contact-audit/1.0)"
KEYWORDS = re.compile(
    r"営業|売り込み|セールス|販促|勧誘|広告宣伝|迷惑メール|お断り|遠慮|禁止",
    re.IGNORECASE,
)


def decode(resp: requests.Response) -> str:
    enc = resp.encoding
    if not enc or enc.lower() in {"iso-8859-1", "ascii"}:
        enc = resp.apparent_encoding or "utf-8"
    return resp.content.decode(enc, errors="replace")


def extract_page(html: str) -> tuple[str, str, dict[str, int]]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    metrics = {
        "forms": len(soup.find_all("form")),
        "textareas": len(soup.find_all("textarea")),
        "inputs": len(soup.find_all("input")),
        "selects": len(soup.find_all("select")),
        "mailto_links": len(soup.select('a[href^="mailto:"]')),
    }
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return title, "\n".join(line for line in lines if line), metrics


def contexts(text: str) -> list[str]:
    lines = text.splitlines()
    hits: list[str] = []
    for i, line in enumerate(lines):
        if not KEYWORDS.search(line):
            continue
        snippet = " / ".join(lines[max(0, i - 1) : min(len(lines), i + 2)])
        if snippet not in hits:
            hits.append(snippet[:500])
    return hits[:12]


def main() -> int:
    rows = list(csv.DictReader(INPUT.open(encoding="utf-8-sig", newline="")))
    results = []
    for row in rows:
        record = {
            "row": int(row["_row"]),
            "company_name": row["company_name"],
            "contact_url": row["contact_url"],
        }
        try:
            resp = requests.get(row["contact_url"], headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
            title, text, metrics = extract_page(decode(resp))
            record.update(
                {
                    "status_code": resp.status_code,
                    "final_url": resp.url,
                    "title": title,
                    "text_length": len(text),
                    **metrics,
                    "keyword_contexts": contexts(text),
                }
            )
        except Exception as exc:  # noqa: BLE001
            record["error"] = f"{type(exc).__name__}: {exc}"
        results.append(record)

    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
