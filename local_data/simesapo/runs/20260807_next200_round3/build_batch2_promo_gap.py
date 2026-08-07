import csv,re
from pathlib import Path
p=Path(__file__).parent
seed=list(csv.DictReader((p/"batch1_high_affinity_seed.csv").open(encoding="utf-8-sig",newline="")))
audit={r["url"]:r for r in csv.DictReader((p/"batch2_full_high_affinity_audit.csv").open(encoding="utf-8-sig",newline=""))}
manufacturing=re.compile(r"製袋|紙器|製作所|紙化工|インキ|封筒|グラビヤ|製本|商会|サプライ|化工|パッケージ")
rows=[]
for r in seed:
 if r.get("区分")!="S｜地域印刷・販促物・ポスティング支援":continue
 if audit.get(r["url"],{}).get("decision")!="accept":continue
 if manufacturing.search(r["company_name"]):continue
 r=dict(r);r["区分"]="A｜地域販促・広告クリエイティブ支援";r["検出ワード"]="公式組合会員＋商業印刷＋販促物・企画制作";rows.append(r)
out=p/"batch2_promo_gap_seed.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(seed[0]));w.writeheader();w.writerows(rows)
print({"selected":len(rows),"output":str(out)})
