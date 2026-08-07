import csv
from pathlib import Path

here=Path(__file__).parent
def read(name): return list(csv.DictReader((here/name).open(encoding="utf-8-sig",newline="")))
base=read("batch1_repaired.csv")
supp=read("web_verified_supplement_usable.csv")
quality={r["company_name"]:r for r in read("batch1_quality.csv")}
extras=[]
for name,contact in [
 ("株式会社TONEGAWA","https://www.tonegawa.co.jp/wp_form/wp/contact/"),
 ("株式会社木元省美堂","https://kimoto-sbd.co.jp/contact/contact_sales/"),
 ("株式会社コトブキ企画","https://www.kotonet.co.jp/inquiry/etc/"),
]:
 r=dict(quality[name]); r["contact_url"]=contact; extras.append(r)

supp_all={r["company_name"]:r for r in read("web_verified_supplement_prelim.csv")}
actus=dict(supp_all["アクタスクリエイト株式会社"])
actus["contact_url"]="https://actus-create.com/?p=1"
extras.append(actus)

# 同名上場会社とは公式ドメイン・所在地・事業が異なる民間広告会社として解消済み。
audit=read("web_verified_supplement_seed.csv")
hok=next(dict(r) for r in audit if r["company_name"]=="株式会社ホクシン")
rows=base+supp+extras+[hok]
seen=set(); unique=[]
for r in rows:
 k=r["url"].rstrip("/").lower()
 if k not in seen: seen.add(k); unique.append(r)
if len(unique)!=50: raise SystemExit(f"final_count={len(unique)}")
out=here/"batch1_final_verified_50.csv"
fields=["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","H1","区分","検出ワード"]
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(unique)
print({"base":len(base),"supplement":len(supp),"manual_form_verified":len(extras),"resolved_review":1,"final":len(unique),"output":str(out)})
