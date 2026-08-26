import csv
import re
import sys

source, output = sys.argv[1:3]
service = ("Web制作", "WEB制作", "ウェブ制作", "ホームページ制作", "Webサイト制作", "サイト制作", "サイト構築", "マーケティング", "広告", "販促", "SNS", "SEO", "MEO", "ブランディング", "デザイン", "印刷")
relationship = ("制作", "構築", "支援", "代行", "運用", "保守", "管理", "コンサル", "代理", "企画", "提供")
deny = ("不動産賃貸", "飲食店の運営", "自動車販売", "金融商品", "人材派遣のみ")
rows=list(csv.DictReader(open(source,encoding="utf-8-sig",newline="")))
scored=[]
for row in rows:
    text=row.get("business_description","")
    sh=sum(t.lower() in text.lower() for t in service); rh=sum(t in text for t in relationship)
    if sh and rh and not any(t in text for t in deny):
        scored.append((sh*3+rh,row))
scored.sort(key=lambda x:x[0],reverse=True)
fields=list(rows[0].keys())
with open(output,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(r for _,r in scored)
print(f"selected={len(scored)}")
