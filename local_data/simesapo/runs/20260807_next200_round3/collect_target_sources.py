import argparse, csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from collect_regional_promo_hubs import source_links, inspect, host

p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('sources',nargs='+'); a=p.parse_args()
raw=[]
with ThreadPoolExecutor(max_workers=8) as ex:
    for links in ex.map(source_links,a.sources): raw.extend(links)
unique={}
for x in raw: unique.setdefault(host(x[0]),x)
rows=[]
with ThreadPoolExecutor(max_workers=16) as ex:
    fs=[ex.submit(inspect,x) for x in unique.values()]
    for f in as_completed(fs):
        v=f.result()
        if v: rows.append(v)
rows.sort(key=lambda r:r['company_name'])
fields=['company_name','url','address','phone','contact_url','区分','検出ワード','source_url','profile_url','company_confirmed','fetch']
with open(a.output,'w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
print({'source_links':len(raw),'unique_domains':len(unique),'qualified_with_form':len(rows)})
