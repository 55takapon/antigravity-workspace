import concurrent.futures
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
SCRIPTS = SKILL / ".claude" / "skills" / "002-contact-extract" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SKILL / "shared"))
import fetch_pages  # noqa: E402
import sheets_io  # noqa: E402


def site_root(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/", "", ""))


sheet, worksheet, output_path = sys.argv[1:4]
wanted = {516, 726, *range(1327, 1353), 1769, 1828, 1853, 1909}
ws = sheets_io.open_worksheet(sheet, worksheet)
rows = sheets_io.read_rows(ws, want=["company_name", "url", "contact_url", "phone", "status"])
targets = [row for row in rows if int(row.get("_row") or 0) in wanted and row.get("url")]
batch = [None] * len(targets)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(fetch_pages.extract_links, site_root(row["url"])): i for i, row in enumerate(targets)}
    for future in concurrent.futures.as_completed(futures):
        i = futures[future]
        try:
            material = future.result()
        except Exception:
            material = {"base_url": site_root(targets[i]["url"]), "links": []}
        batch[i] = {"idx": i, "_row": targets[i]["_row"], "company_name": targets[i].get("company_name", ""), "current_contact_url": targets[i].get("contact_url", ""), **material}
Path(output_path).write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"rows": len(batch), "links": sum(bool(x.get("links")) for x in batch)}))
