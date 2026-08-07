import csv
from pathlib import Path
p=Path(__file__).parent
names=["batch2_policy_usable.csv","batch2_web_supplement_usable.csv","batch2_promo_gap_usable.csv"]
rows=[]
for n in names:rows+=list(csv.DictReader((p/n).open(encoding="utf-8-sig",newline="")))
seen=set();unique=[]
for r in rows:
 k=r["url"].rstrip("/").lower()
 if k not in seen:seen.add(k);unique.append(r)
if len(unique)<50:raise SystemExit(f"unique={len(unique)}")
unique=unique[:50]
fields=["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","H1","区分","検出ワード"]
out=p/"batch2_final_verified_50.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(unique)
print({"sources":{n:sum(1 for _ in csv.DictReader((p/n).open(encoding='utf-8-sig',newline=''))) for n in names},"unique":len(unique),"output":str(out)})
