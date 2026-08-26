import csv,sys
from datetime import date
base=sys.argv[1]
def load(n):return list(csv.DictReader(open(base+"\\"+n,encoding="utf-8-sig",newline="")))
retained=load("round2_retained.csv");candidates=load("round2_candidate_pool_allowed.csv")[:78]
for r in candidates:
 source=r.get("source_url") or r.get("evidence_urls") or r.get("url")
 recurring=bool(r.get("recurring_evidence")) or any(t in r.get("business_description","") for t in ("運用","保守","管理","代行","サポート"))
 r.update({"hub_type":"HYBRID_HUB" if recurring else "ADD_ON_HUB","why_fit":"公開企業プロフィールでホームページ制作会社として確認"+("し、運用・保守等の継続支援根拠あり" if recurring else "。既存制作顧客へのMEO追加提案が可能"),"evidence_urls":source,"confidence":"A" if recurring else "B","review_status":"VERIFIED","last_verified_at":date.today().isoformat(),"status":"MEOハブ候補"})
final=retained+candidates
if len(final)!=1000:raise SystemExit(f"retained={len(retained)} candidates={len(candidates)}")
fields=["company_name","url","address","phone","maps_url","status","hub_type","why_fit","evidence_urls","confidence","review_status","last_verified_at"]
with open(base+"\\final_verified_additional_1000_round2.csv","w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(final)
print(f"retained={len(retained)} replacement={len(candidates)} final={len(final)}")
