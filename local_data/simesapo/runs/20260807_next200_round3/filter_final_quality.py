import argparse, csv, re
from urllib.parse import urlparse

p=argparse.ArgumentParser(); p.add_argument("--seed",required=True); p.add_argument("--audit",required=True); p.add_argument("--output",required=True); a=p.parse_args()
def host(u): return (urlparse(u).hostname or "").lower().removeprefix("www.")
with open(a.audit,encoding="utf-8-sig",newline="") as f: audit={host(r["url"]):r for r in csv.DictReader(f)}
with open(a.seed,encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
blocked_domains={
"gamo.co.jp","gamo-w.jp","kikuya-bisyodo.co.jp","senbi-beauty.com","dental-web.jp",
"fudoukun.jp","healthwebcreations.com","gymcloud.jp","pagepro.jp","j-s-p.com",
"dym.asia","digital-gorilla.co.jp",
}
noise=re.compile(r"様|確認画面|日本国内で|会社名|会社概要|企業情報|法人概要|社名|住所|所在地|ご提供|ホームページ・株式会社|Google|GOOGLE|店舗・|大阪の")
accepted=[]; reasons={}
for row in rows:
    domain=host(row.get("url","")); decision=audit.get(domain,{}).get("decision","")
    if decision!="accept": continue
    if domain in blocked_domains: reasons["blocked_domain_or_major"]=reasons.get("blocked_domain_or_major",0)+1; continue
    if noise.search(row.get("company_name","")): reasons["name_noise"]=reasons.get("name_noise",0)+1; continue
    accepted.append(row)
with open(a.output,"w",encoding="utf-8-sig",newline="") as f:
    fields=list(accepted[0]) if accepted else []
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(accepted)
print({"accepted_before":sum(r.get('decision')=='accept' for r in audit.values()),"quality_pass":len(accepted),"removed":reasons,"output":a.output})
