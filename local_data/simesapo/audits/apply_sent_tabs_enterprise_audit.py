from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
sys.path.insert(0, str(ROOT / ".agent/skills/simesapo-sales-skills-dist/shared"))
import sheets_io

TABS = ("送信済み251127", "送信済み251222", "Web幹事済み")

def nc(v):
    v = unicodedata.normalize("NFKC", v or "").lower()
    v = re.sub(r"株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|\(株\)|\(有\)|\(同\)", "", v)
    return re.sub(r"[\s\u3000・･.,，．_/'\"()（）\[\]［］]", "", v)

def nd(v):
    v = (v or "").strip()
    if not v: return ""
    if not re.match(r"^https?://", v, re.I): v = "https://" + v
    try: return re.sub(r"^www\.", "", (urlparse(v).hostname or "").lower().rstrip("."))
    except ValueError: return ""

def key(c, u): return nc(c), nd(u)

def rows(ws):
    vals = ws.get_all_values()
    header = vals[0]
    out = []
    for n, raw in enumerate(vals[1:], 2):
        if not any(x.strip() for x in raw): continue
        raw = raw + [""] * max(0, len(header) - len(raw))
        out.append({"row": n, "raw": raw, "company": raw[0].strip(), "url": raw[1].strip() if len(raw)>1 else ""})
    return header, out

def ranges_desc(nums):
    nums = sorted(set(nums)); result=[]
    if not nums: return result
    s=p=nums[0]
    for n in nums[1:]:
        if n == p+1: p=n; continue
        result.append((s,p)); s=p=n
    result.append((s,p))
    return sorted(result, reverse=True)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("sheet"); ap.add_argument("audit", type=Path); ap.add_argument("--apply", action="store_true"); ap.add_argument("--log", type=Path, required=True)
    a=ap.parse_args()
    audit=list(csv.DictReader(a.audit.open(encoding="utf-8-sig", newline="")))
    delete_audit=[r for r in audit if r["classification"] in {"exclude_confirmed_enterprise","already_in_exclusion_list"}]
    allow_audit=[r for r in audit if r["classification"] == "allow_confirmed_same_name_other_entity"]
    if (len(audit),len(delete_audit),len(allow_audit)) != (105,66,39): raise RuntimeError("audit counts changed")
    client=sheets_io.get_client(None); book=client.open_by_url(a.sheet)
    ex=book.worksheet("除外リスト"); ex_header, ex_rows=rows(ex)
    if ex_header[:2] != ["company_name","url"]: raise RuntimeError(f"除外リストヘッダー不一致: {ex_header[:3]}")
    existing={key(r["company"],r["url"]) for r in ex_rows}; existing_domains={nd(r["url"]) for r in ex_rows if nd(r["url"])}
    targets={(r["worksheet"], int(r["row_number"])):r for r in delete_audit}
    matched={}; before={}; worksheets={}; allow_keys={key(r["company_name"],r["url"]) for r in allow_audit}
    source_by_audit={}
    for tab in TABS:
        ws=book.worksheet(tab); worksheets[tab]=ws; _, rr=rows(ws); before[tab]=len(rr)
        by_num={r["row"]:r for r in rr}
        for (atab,n), ar in targets.items():
            if atab != tab: continue
            sr=by_num.get(n)
            if not sr or key(sr["company"],sr["url"]) != key(ar["company_name"],ar["url"]):
                raise RuntimeError(f"対象行不一致: {tab}!{n} {ar['company_name']}")
            matched.setdefault(tab,[]).append(sr); source_by_audit[id(ar)]=sr
    if sum(map(len,matched.values())) != 66: raise RuntimeError("delete match count mismatch")
    append=[]; seen=set(existing)
    for ar in delete_audit:
        if ar["classification"] != "exclude_confirmed_enterprise": continue
        k=key(ar["company_name"],ar["url"]); domain=k[1]
        if k in seen or (domain and domain in existing_domains): continue
        sr=source_by_audit[id(ar)]; raw=(sr["raw"]+[""]*13)[:13]
        raw[8]="excluded"; raw[9]=f"enterprise_audit:上場企業・大手グループ | {ar['reason']} | source:{ar['worksheet']}!{ar['row_number']}"
        raw[12]="除外確定（上場企業・大手グループ）"; append.append(raw); seen.add(k)
    summary={"mode":"apply" if a.apply else "preview","scanned":sum(before.values()),"before":before,"delete":{t:len(v) for t,v in matched.items()},"delete_total":66,"append_exclusion":len(append),"already_exclusion_occurrences":16,"allow_untouched":39,"exclusion_before":len(ex_rows)}
    if not a.apply: print(json.dumps(summary,ensure_ascii=False,indent=2)); return
    if append: ex.append_rows(append,value_input_option="RAW",insert_data_option="INSERT_ROWS",table_range="A:M")
    _, ex_after=rows(ex)
    if len(ex_after) != len(ex_rows)+len(append): raise RuntimeError("除外リスト追記読み戻し不一致。削除停止")
    backup=[]; requests=[]
    for tab, rr in matched.items():
        backup += [{"worksheet":tab,"row":r["row"],"values":r["raw"]} for r in rr]
        for s,e in ranges_desc([r["row"] for r in rr]): requests.append({"deleteDimension":{"range":{"sheetId":worksheets[tab].id,"dimension":"ROWS","startIndex":s-1,"endIndex":e}}})
    a.log.parent.mkdir(parents=True,exist_ok=True); a.log.write_text(json.dumps({"created_at":datetime.now().astimezone().isoformat(),"backup":backup},ensure_ascii=False,indent=2),encoding="utf-8")
    book.batch_update({"requests":requests})
    after={}; remain=[]; allows=0
    for tab in TABS:
        _, rr=rows(worksheets[tab]); after[tab]=len(rr)
        pairs={key(r["company"],r["url"]) for r in rr}; allows += sum(1 for r in rr if key(r["company"],r["url"]) in allow_keys)
        target_keys={key(r["company_name"],r["url"]) for r in delete_audit if r["worksheet"]==tab}; remain += [(tab,r["row"]) for r in rr if key(r["company"],r["url"]) in target_keys]
    if sum(before.values())-sum(after.values()) != 66 or remain or allows < 39: raise RuntimeError(f"削除後検証不一致 remain={remain[:5]} allows={allows}")
    summary.update({"after":after,"deleted_verified":66,"exclusion_after":len(ex_after),"append_verified":len(append),"remaining_targets":0,"allow_remaining":allows,"log":str(a.log)})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__ == "__main__": main()
