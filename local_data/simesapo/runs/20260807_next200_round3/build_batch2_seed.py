import csv
from pathlib import Path
p=Path(__file__).parent
src=list(csv.DictReader((p/"batch1_high_affinity_seed.csv").open(encoding="utf-8-sig",newline="")))
rows=[r for r in src if r.get("区分")=="S｜地域印刷・販促・Web支援"]
out=p/"batch2_regional_web_seed.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=list(src[0])); w.writeheader(); w.writerows(rows)
print({"input":len(src),"selected":len(rows),"output":str(out)})
