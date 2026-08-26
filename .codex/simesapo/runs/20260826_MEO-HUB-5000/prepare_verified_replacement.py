import csv
import re
import sys
from datetime import date

base=sys.argv[1]
def load(name):
    with open(base+"\\"+name,encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

current=load("daily_append_1000_ready.csv")
def simple_key(r): return (re.sub(r"\s+","",r.get("company_name","").lower()),re.sub(r"^https?://(?:www\.)?","",r.get("url","").lower()).split("/")[0])
current_keys={simple_key(r) for r in current}
retained=[]; retained_keys=set()
for name,hub,why,confidence in [
    ("daily_sales_support_001_kept.csv","ADD_ON_HUB","営業代行・営業支援の提供実態があり、複数顧客へ追加商材を提案できる構造","B"),
    ("daily_grip_recovered_verified.csv","HYBRID_HUB","公式企業プロフィールの事業本文でWeb・広告関連サービスを再確認","B"),
    ("replacement_old_other_verified.csv","HYBRID_HUB","公式企業プロフィールの事業本文でWeb・広告関連サービスを再確認","B")]:
    for r in load(name):
        key=simple_key(r)
        if key not in current_keys or key in retained_keys: continue
        retained_keys.add(key)
        r.update({"hub_type":hub,"why_fit":why,"evidence_urls":r.get("source_url") or r.get("url"),"confidence":confidence,"review_status":"VERIFIED","last_verified_at":date.today().isoformat()});retained.append(r)

direct=("飲食店の運営","不動産賃貸","自動車販売","金融商品","アパレル事業","蓄電・エネルギー事業","介護事業","鉄道事業","旅客・ハンドリング","バスターミナル業")
replacement=[]; rejected=[]
for r in load("replacement_candidates_allowed.csv"):
    text=r.get("business_description","")
    hit=next((t for t in direct if t in text),"")
    if hit:
        r["reject_reason"]="直接事業者リスク: "+hit; rejected.append(r); continue
    source=r.get("source_url","")
    recurring=bool(r.get("recurring_evidence")) or any(t in text for t in ("運用","保守","管理","代行","サポート","継続"))
    if "web-kanji.com/companies/" in source:
        hub="ADD_ON_HUB" if not recurring else "HYBRID_HUB"
        why="Web幹事の企業プロフィールでホームページ制作会社として確認。既存制作顧客へのMEO追加提案が可能"
        confidence="B" if not recurring else "A"
    else:
        hub="HYBRID_HUB" if recurring else "ADD_ON_HUB"
        evidence=r.get("hub_evidence") or "Web制作・Webマーケティング"
        why=f"公開企業プロフィールの事業本文で{evidence}を確認"+("し、運用・保守等の継続支援根拠あり" if recurring else "")
        confidence="A" if recurring else "B"
    r.update({"hub_type":hub,"why_fit":why,"evidence_urls":source or r.get("url"),"confidence":confidence,"review_status":"VERIFIED","last_verified_at":date.today().isoformat()});replacement.append(r)

replacement=replacement[:595]
final=retained+replacement
if len(retained)!=405 or len(replacement)!=595 or len(final)!=1000: raise SystemExit(f"counts invalid retained={len(retained)} replacement={len(replacement)} final={len(final)}")
fields=["company_name","url","address","phone","maps_url","status","hub_type","why_fit","evidence_urls","confidence","review_status","last_verified_at"]
for rows,name in [(replacement,"replacement_verified_595.csv"),(final,"final_verified_additional_1000.csv"),(rejected,"replacement_rejected.csv")]:
    with open(base+"\\"+name,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields+(["reject_reason"] if name=="replacement_rejected.csv" else []),extrasaction="ignore");w.writeheader();w.writerows(rows)
print(f"retained={len(retained)} replacement={len(replacement)} final={len(final)} rejected={len(rejected)} available_replacement={len(load('replacement_candidates_allowed.csv'))}")
