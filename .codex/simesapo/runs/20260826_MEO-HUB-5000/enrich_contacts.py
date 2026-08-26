import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests

source, output = sys.argv[1:3]
rows = list(csv.DictReader(open(source, encoding="utf-8-sig", newline="")))
headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja-JP,ja;q=0.9"}

def enrich(row):
    try:
        response = requests.get(row.get("url", ""), headers=headers, timeout=12, allow_redirects=True)
        body = response.text
        for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', body, re.I | re.S):
            text = re.sub(r"<[^>]+>", " ", label)
            if re.search(r"お問い合わせ|問合せ|contact|inquiry", text + " " + href, re.I):
                candidate = urljoin(response.url, href)
                if candidate.startswith("http"):
                    row["contact_url"] = candidate
                    break
        phone = re.search(r"(?<!\d)(0\d{1,4}[- ]\d{1,4}[- ]\d{3,4})(?!\d)", body)
        if not row.get("phone") and phone: row["phone"] = phone.group(1)
    except requests.RequestException:
        pass
    return row

done=[]
with ThreadPoolExecutor(max_workers=20) as pool:
    futures=[pool.submit(enrich,r) for r in rows]
    for i,f in enumerate(as_completed(futures),1):
        done.append(f.result())
        if i%100==0: print(f"done={i}",flush=True)
fields=list(rows[0].keys()) if rows else []
if "contact_url" not in fields: fields.append("contact_url")
with open(output,"w",encoding="utf-8-sig",newline="") as handle:
    writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(done)
print(f"rows={len(done)} contact={sum(bool(r.get('contact_url') or r.get('phone')) for r in done)}")
