import csv
from pathlib import Path
p=Path(__file__).parent
seed=list(csv.DictReader((p/"batch1_high_affinity_seed.csv").open(encoding="utf-8-sig",newline="")))
audit={r["url"]:r for r in csv.DictReader((p/"batch2_full_high_affinity_audit.csv").open(encoding="utf-8-sig",newline=""))}
allowed={
"S｜地域印刷・販促・Web支援","S｜医科・歯科特化Web・集客支援","S｜不動産会社特化Web・集客支援",
"S｜治療院特化Web・集客支援","S｜美容室・サロン特化Web・集客支援","S｜士業特化Web・集客支援",
}
rows=[r for r in seed if r.get("区分") in allowed and audit.get(r["url"],{}).get("decision")=="accept"]
out=p/"batch2_policy_base.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(seed[0])); w.writeheader(); w.writerows(rows)
print({"selected":len(rows),"output":str(out)})
