import csv
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


OFFICIAL_FILES = [Path("data/sns_partner_archive_official.csv")]
OFFICIAL_FILES.extend(Path(f"data/sns_partner_official_wave{i}.csv") for i in range(2, 19))
OFFICIAL_FILES.extend(Path(f"data/sns_secondary_official_{i}.csv") for i in range(4))
AFFINITY_FILES = [Path("data/sns_partner_archive_affinity_v5.csv")]
AFFINITY_FILES.extend(Path(f"data/sns_partner_affinity_wave{i}_v5.csv") for i in range(2, 19))
AFFINITY_FILES.extend(Path(f"data/sns_secondary_affinity_{i}.csv") for i in range(4))
COMPETITOR = re.compile(r"(MEO対策|MEO運用|Googleビジネスプロフィール運用|Googleマップ集客|ローカルSEO専門)", re.I)
local = threading.local()


def host(url):
    return urlparse(url).netloc.lower().removeprefix("www.")


def session():
    if not hasattr(local, "value"):
        local.value = requests.Session()
        local.value.headers["User-Agent"] = "Mozilla/5.0"
    return local.value


def is_noncompetitor(row):
    try:
        response = session().get(row["url"], timeout=(5, 12), allow_redirects=True, stream=True)
        if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
            response.close()
            return None
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            chunks.append(chunk)
            size += len(chunk)
            if size >= 1_000_000:
                break
        content = b"".join(chunks)[:1_000_000]
        response.close()
        soup = BeautifulSoup(content, "html.parser")
        title_text = " ".join(node.get_text(" ", strip=True) for node in soup.select("title,h1")[:4])
        body_text = soup.get_text(" ", strip=True)
        if COMPETITOR.search(title_text) or len(COMPETITOR.findall(body_text)) >= 8:
            return None
        result = dict(row)
        result.update({"affinity_grade": "C", "affinity_score": "0", "local_hits": "0", "competitor_hits": str(len(COMPETITOR.findall(body_text)))})
        return result
    except requests.RequestException:
        return None


official = {}
for path in OFFICIAL_FILES:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            official.setdefault(host(row["url"]), row)
affinity_domains = set()
for path in AFFINITY_FILES:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        affinity_domains.update(host(row["url"]) for row in csv.DictReader(handle))
targets = [row for domain, row in official.items() if domain not in affinity_domains]

kept = []
with ThreadPoolExecutor(max_workers=12) as executor:
    futures = [executor.submit(is_noncompetitor, row) for row in targets]
    for future in as_completed(futures):
        item = future.result()
        if item:
            kept.append(item)

fields = list(next(iter(official.values())).keys()) + ["affinity_grade", "affinity_score", "local_hits", "competitor_hits"]
output = Path("data/sns_partner_recovered_noncompetitors_v11.csv")
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(kept)
print(f"official_unique={len(official)} targets={len(targets)} recovered={len(kept)} output={output}")
