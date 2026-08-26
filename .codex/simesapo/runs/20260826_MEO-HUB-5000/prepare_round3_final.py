import csv,sys
from datetime import date
from pathlib import Path

base=Path(sys.argv[1])
def load(n):return list(csv.DictReader(open(base/n,encoding="utf-8-sig",newline="")))
bad={
 "株式会社SAMPO":"登録URLが別ブランドサイトで公式企業URLの裏付けなし",
 "株式会社ＤＧインデックス":"登録URLが404で公式根拠を確認できない",
 "株式会社moji":"登録URLが別法人のゲーム公式サイト",
 "株式会社G-KIT":"登録URLが別法人の採用ページ",
 "ＭＮインターファッション株式会社":"繊維・アパレル調達販売で顧客向けWeb・広告支援根拠なし",
}
round2=load("final_verified_additional_1000_round2.csv")
removed=[r for r in round2 if r["company_name"] in bad];retained=[r for r in round2 if r["company_name"] not in bad]
if len(removed)!=5 or len(retained)!=995:raise SystemExit(f"removed={len(removed)} retained={len(retained)}")
used={r["url"] for r in round2};replacements=[r for r in load("round2_candidate_pool_allowed.csv") if r["url"] not in used]
if len(replacements)!=5:raise SystemExit(f"replacements={len(replacements)}")
verified={
 "株式会社アックスコンサルティング":("https://www.accs-c.co.jp/webmarketing/","士業向けWeb制作実績1,000件以上と継続的なWebマーケティング支援を公式サイトで確認","HYBRID_HUB","A"),
 "スパークジャパン株式会社":("https://www.sparkjapan.co.jp/works/","公式サイトでWebマーケティングと店舗型企業を含む多数の制作・運用実績を確認","HYBRID_HUB","A"),
 "株式会社ウィスト":("http://wist-inc.com/works/works.html","公式サイトの制作実績ページでホームページ制作事業を確認","ADD_ON_HUB","B"),
 "OPS株式会社":("https://www.op-s.co.jp/","公式サイトでWeb制作・運用・管理、集客支援、代理店事業を確認","HYBRID_HUB","A"),
 "サンライトウェブ":("http://www.sls-web.com/","公式サイトでホームページ制作とSEO対策サービスを確認","ADD_ON_HUB","B"),
}
for r in replacements:
 evidence,why,hub,conf=verified[r["company_name"]];r.update({"status":"MEOハブ候補","hub_type":hub,"why_fit":why,"evidence_urls":evidence,"confidence":conf,"review_status":"VERIFIED","last_verified_at":date.today().isoformat()})
final=retained+replacements
fields=["company_name","url","address","phone","maps_url","status","hub_type","why_fit","evidence_urls","confidence","review_status","last_verified_at"]
with open(base/"final_verified_additional_1000_round3.csv","w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(final)
ex_fields=["company_name","url","phone","reject_reason","exclusion_scope","source_batch","evidence_urls"]
with open(base/"round3_exclusion_registry.csv","w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=ex_fields);w.writeheader()
 for r in removed:w.writerow({"company_name":r["company_name"],"url":r["url"],"phone":r["phone"],"reject_reason":bad[r["company_name"]],"exclusion_scope":"PERMANENT","source_batch":"round3_independent_audit","evidence_urls":r.get("evidence_urls","")})
print(f"retained={len(retained)} replacements={len(replacements)} final={len(final)} excluded={len(removed)}")
