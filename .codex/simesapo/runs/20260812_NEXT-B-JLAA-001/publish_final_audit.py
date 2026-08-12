import csv, hashlib, json, sys, unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(r"C:\Users\hangy\.gemini\antigravity")
DIST=ROOT/".agent"/"skills"/"simesapo-sales-skills-dist"
RUN=Path(__file__).parent
sys.path[:0]=[str(DIST/".codex_pydeps"),str(DIST/"shared")]
from sheets_io import get_client

SHEET_ID="1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
AUDIT=RUN/"jlaa_final_audit_33.csv"

def pad(r,n=16): return r+[""]*(n-len(r))
def norm(s):
    s=unicodedata.normalize("NFKC",s or "").lower()
    for x in ("株式会社","有限会社","合同会社","合資会社","（株）","(株)"," ","　","・",".","-","_"): s=s.replace(x,"")
    return s
def domain(u):
    if not u:return ""
    if "://" not in u:u="https://"+u
    h=(urlparse(u).hostname or "").lower().strip(".")
    return h[4:] if h.startswith("www.") else h
def digest(r): return hashlib.sha256(json.dumps(r,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

rows=list(csv.DictReader(AUDIT.open(encoding="utf-8-sig")))
if len(rows)!=33: raise SystemExit(f"STOP audit rows {len(rows)}")
# Manual confirmation: official site links to a live Google Form.
for r in rows:
    if r["company_name"]=="株式会社アクティブイエロー":
        r["classification"]="送付対象"; r["contact_check"]="real_form_confirmed_manual"
        r["contact_url"]="https://docs.google.com/forms/d/e/1FAIpQLSftAbJCUhElC_0XOb6pp4yosD25ebiqyEtlV2SQvfm3_lIR1Q/viewform?usp=sf_link"
        r["audit_reason"]="広告・出版・地域情報発信／公式サイトからGoogleフォームへの導線を確認"
# Canonical 001 filter dropped this record, so it must not be added as a send target.
for r in rows:
    if r["company_name"]=="株式会社ライズウィル":
        r["classification"]="除外"; r["audit_reason"]+="／001正規除外照合で非採用"

send=[r for r in rows if r["classification"]=="送付対象"]
exc=[r for r in rows if r["classification"]=="除外"]
if (len(send),len(exc))!=(15,18): raise SystemExit(f"STOP class counts {len(send)}/{len(exc)}")

sh=get_client(str(DIST/"shared"/"gcp_service_account.json")).open_by_key(SHEET_ID)
ws=sh.worksheet("シート2"); exws=sh.worksheet("除外リスト"); pws=sh.worksheet("収集進捗管理")
sv=[pad(r) for r in ws.get("A1:P",value_render_option="FORMULA")]
ev=[pad(r) for r in exws.get("A1:P",value_render_option="FORMULA")]
if len(sv)!=2851: raise SystemExit(f"STOP Sheet2 expected 2851 got {len(sv)}")
first_excl=next((i for i,r in enumerate(sv[1:],start=2) if r[14].startswith("除外")),None)
if first_excl!=2550 or not all(r[14].startswith("除外") for r in sv[first_excl-1:]):
    raise SystemExit(f"STOP exclusion block invalid first={first_excl}")

all_domain={domain(r[1]) for r in sv[1:]+ev[1:] if domain(r[1])}
dups=[r["company_name"] for r in rows if domain(r["official_url"]) in all_domain and domain(r["official_url"])!="totsu-ag.com"]
if dups: raise SystemExit("STOP live duplicates: "+json.dumps(dups,ensure_ascii=False))

with (RUN/"sheet2_before_publish.csv").open("w",encoding="utf-8-sig",newline="") as f: csv.writer(f).writerows(sv)
with (RUN/"exclusion_before_publish.csv").open("w",encoding="utf-8-sig",newline="") as f: csv.writer(f).writerows(ev)

def srow(r):
    x=[""]*16; x[0]=r["company_name"]; x[1]=r["official_url"]; x[5]=r["contact_url"]
    x[12]="地域広告・販促支援"; x[14]="送付対象｜B｜JLAA地域広告会社"
    x[15]=f"【採用根拠】{r['audit_reason']}｜【窓口】実在フォーム確認済み：{r['contact_url']}｜【根拠URL】{r['official_url']}｜【監査日】2026-08-12"
    return x
def erow(r):
    x=[""]*16; x[0]=r["company_name"]; x[1]=r["official_url"]; x[5]=r["contact_url"]
    x[8]="skip監査除外"; x[9]=r["audit_reason"]; x[12]="JLAA本監査"
    x[14]="除外｜JLAA本監査"; x[15]=f"【除外根拠】{r['audit_reason']}｜【窓口確認】{r['contact_check']}｜【根拠URL】{r['official_url']}｜【監査日】2026-08-12"
    return x

ws.insert_rows([srow(r) for r in send],row=first_excl,value_input_option="RAW")
# A prior audit left the same official Totsu domain as send target. Correct it in place.
totsu_row=next(i for i,r in enumerate(ws.get("A1:P",value_render_option="FORMULA"),start=1) if len(r)>1 and domain(r[1])=="totsu-ag.com")
ws.update(range_name=f"I{totsu_row}:P{totsu_row}",values=[["skip監査除外","上場会社東建コーポレーショングループ","","","","","除外｜JLAA本監査","【除外根拠】上場会社東建コーポレーショングループ｜【根拠URL】https://www.totsu-ag.com/｜【監査日】2026-08-12"]],value_input_option="RAW")
ex_start=len(ev)+1
exws.append_rows([erow(r) for r in exc],value_input_option="RAW",table_range=f"A{ex_start}:P")

# Keep every O-column exclusion contiguous at the bottom while preserving prior order.
mid=[pad(r) for r in ws.get("A1:P",value_render_option="FORMULA")]
keys=[[1 if r[14].startswith("除外") else 0, i] for i,r in enumerate(mid[1:],start=2)]
sh.batch_update({"requests":[{"appendDimension":{"sheetId":ws.id,"dimension":"COLUMNS","length":2}}]})
try:
    ws.update(range_name=f"Q2:R{len(mid)}",values=keys,value_input_option="RAW")
    sh.batch_update({"requests":[{"sortRange":{"range":{"sheetId":ws.id,"startRowIndex":1,"endRowIndex":len(mid),"startColumnIndex":0,"endColumnIndex":18},"sortSpecs":[{"dimensionIndex":16,"sortOrder":"ASCENDING"},{"dimensionIndex":17,"sortOrder":"ASCENDING"}]}}]})
finally:
    sh.batch_update({"requests":[{"deleteDimension":{"range":{"sheetId":ws.id,"dimension":"COLUMNS","startIndex":16,"endIndex":18}}}]})

# Update the existing JLAA plan line and progress summary; no new tab is created.
pws.update(range_name="A84:F84",values=[["1","NEXT-B-JLAA-001","日本地域広告会社協会（JLAA）","公式63社／既存23／事前除外7／本監査33","送付対象15社・除外18社を確定","シート2・除外リスト反映済み"]],value_input_option="RAW")
pws.update(range_name="A89:F89",values=[["進捗","再計算完了","純増856社","8.56%","有効基準9,097社","残り9,144社"]],value_input_option="RAW")

sv2=[pad(r) for r in ws.get("A1:P",value_render_option="FORMULA")]
ev2=[pad(r) for r in exws.get("A1:P",value_render_option="FORMULA")]
first2=next((i for i,r in enumerate(sv2[1:],start=2) if r[14].startswith("除外")),None)
checks={
 "audit_total":len(rows),"send_written":len(send),"exclude_written":len(exc),
 "sheet2_rows_before":len(sv),"sheet2_rows_after":len(sv2),"exclusion_rows_before":len(ev),"exclusion_rows_after":len(ev2),
 "first_exclusion_row_after":first2,"exclusions_contiguous_bottom":all(r[14].startswith("除外") for r in sv2[first2-1:]),
 "sheet2_send_count_after":sum(r[14].startswith("送付対象") for r in sv2[1:]),"sheet2_exclude_count_after":sum(r[14].startswith("除外") for r in sv2[1:]),
 "send_names_readback":sum(1 for r in send if any(norm(x[0])==norm(r["company_name"]) for x in sv2)),
 "exclude_names_readback":sum(1 for r in exc if any(norm(x[0])==norm(r["company_name"]) for x in ev2)),
 "duplicate_domains_sheet2":len([domain(r[1]) for r in sv2[1:] if domain(r[1])])-len(set(domain(r[1]) for r in sv2[1:] if domain(r[1]))),
 "progress_readback":pws.get("A84:F84")+pws.get("A89:F89")}
if not (checks["sheet2_rows_after"]==len(sv)+15 and checks["exclusion_rows_after"]==len(ev)+18 and checks["first_exclusion_row_after"]==2564 and checks["exclusions_contiguous_bottom"] and checks["sheet2_send_count_after"]==856 and checks["sheet2_exclude_count_after"]==303 and checks["send_names_readback"]==15 and checks["exclude_names_readback"]==18 and checks["duplicate_domains_sheet2"]==0):
    raise SystemExit("STOP post-write verification failed "+json.dumps(checks,ensure_ascii=False))
(RUN/"publish_verification.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(checks,ensure_ascii=False,indent=2))
