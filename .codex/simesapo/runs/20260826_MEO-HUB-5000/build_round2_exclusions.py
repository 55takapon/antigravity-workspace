import csv,re,sys,unicodedata
from datetime import date
from urllib.parse import urlparse
base=sys.argv[1]
def load(n):return list(csv.DictReader(open(base+"\\"+n,encoding="utf-8-sig",newline="")))
def dk(v):
 h=urlparse(v or "").netloc.lower().split(":")[0];return h[4:] if h.startswith("www.") else h
final=load("final_verified_additional_1000.csv");raw=[]
for n in ("daily_grip_recovered_verified.csv","replacement_old_other_verified.csv"):raw+=load(n)
desc={r.get("source_url"):r.get("business_description","") for r in raw}
pat=re.compile(r"web|ウェブ|ウエブ|ホームページ|サイト|hp作成|ecサイト|インターネット|デジタル|マーケティング|広告|販促|プロモーション|sns|seo|meo|印刷",re.I)
bad=[];kept=[]
for r in final:
 t=desc.get(r.get("evidence_urls"),"")
 weak_grip="grip.website" in r.get("evidence_urls","") and not pat.search(unicodedata.normalize("NFKC",t))
 named=r.get("company_name") in ("株式会社クラベール",)
 if weak_grip or named:
  x=dict(r);x.update({"normalized_domain":dk(r.get("url")),"exclusion_scope":"PERMANENT","reject_reason":"再監査でWeb制作・Webマーケティング・営業支援の公開根拠なし","evidence_url":r.get("evidence_urls") or r.get("url"),"reviewed_at":date.today().isoformat()});bad.append(x)
 else:kept.append(r)
fields=["company_name","url","normalized_domain","phone","exclusion_scope","reject_reason","evidence_url","reviewed_at"]
with open(base+"\\round2_exclusion_registry.csv","w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(bad)
with open(base+"\\round2_retained.csv","w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=list(final[0]),extrasaction="ignore");w.writeheader();w.writerows(kept)
print(f"excluded={len(bad)} retained={len(kept)}")
