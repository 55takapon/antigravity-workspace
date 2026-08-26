import csv
import re
import sys
from datetime import date
from urllib.parse import urlparse

base, output = sys.argv[1:3]

def load(name):
    with open(base + "\\" + name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def nk(v): return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (v or "").lower())
def dk(v):
    h=urlparse(v or "").netloc.lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h

added=load("daily_append_1000_ready.csv")
pool=load("daily_approved_pool_1000plus.csv")
details={(nk(x.get("company_name")),dk(x.get("url"))):x for x in pool}
verified=[]
for name in ("daily_sales_support_001_kept.csv","daily_grip_recovered_verified.csv","replacement_old_other_verified.csv"):
    verified.extend(load(name))
good={(nk(x.get("company_name")),dk(x.get("url"))) for x in verified}
direct_terms=("飲食店の運営","不動産賃貸","自動車販売","金融商品","アパレル事業","蓄電・エネルギー事業","介護事業","鉄道事業","旅客・ハンドリング","バスターミナル業")
rows=[]
for row in added:
    key=(nk(row.get("company_name")),dk(row.get("url")))
    if key in good: continue
    d=details.get(key,{})
    text=d.get("business_description","")
    permanent=next((t for t in direct_terms if t in text),"")
    rows.append({
        "company_name":row.get("company_name",""),"url":row.get("url",""),"normalized_domain":dk(row.get("url")),"phone":row.get("phone",""),
        "exclusion_scope":"PERMANENT" if permanent else "RECHECK",
        "reject_reason":f"直接事業者の根拠あり: {permanent}" if permanent else "公式事業本文でMEOハブ適合を再確認できず",
        "evidence_url":d.get("source_url",row.get("url","")),"reviewed_at":date.today().isoformat()
    })
fields=["company_name","url","normalized_domain","phone","exclusion_scope","reject_reason","evidence_url","reviewed_at"]
with open(output,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
print(f"excluded={len(rows)} permanent={sum(r['exclusion_scope']=='PERMANENT' for r in rows)} recheck={sum(r['exclusion_scope']=='RECHECK' for r in rows)}")
