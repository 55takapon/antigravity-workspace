import argparse, csv, re

p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); a=p.parse_args()
with open(a.input,encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
allowed=[]
for row in rows:
    category=row.get("区分","")
    evidence=row.get("検出ワード","")
    if not category.startswith("S｜地域"):
        continue
    if not re.search(r"Web|WEB|広告|販促|マーケティング|ポスティング|クリエイティブ|ホームページ", category+" "+evidence):
        continue
    allowed.append(row)
with open(a.output,"w",encoding="utf-8-sig",newline="") as f:
    fields=list(allowed[0]) if allowed else []
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(allowed)
print({"input":len(rows),"partner_segments":len(allowed),"output":a.output})
