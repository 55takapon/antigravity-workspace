from __future__ import annotations

import csv, html, json, re, sys, time, unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

ROOT=Path(r"C:\Users\hangy\.gemini\antigravity")
RUN=ROOT/".codex"/"simesapo"/"runs"/"20260812_NEXT-B-JLAA-001"
SRC=RUN/"jlaa_members_prefiltered.csv"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
sys.path.insert(0,str(ROOT/".agent"/"skills"/"simesapo-sales-skills-dist"/".codex_pydeps"))
import requests
from bs4 import BeautifulSoup

BAD_DOMAINS=("jlaa2003.com","facebook.com","instagram.com","x.com","twitter.com","youtube.com","linkedin.com","houjin.jp","buffett-code.com","baseconnect.in","biz.ne.jp","mapion.co.jp","navitime.co.jp","wantedly.com","indeed.com","hellowork.mhlw.go.jp","prtimes.jp","dreamnews.jp","wikipedia.org")
SERVICE=("広告","販促","プロモーション","マーケティング","web","ウェブ","ホームページ","sns","ブランディング","pr","広報","デザイン","クリエイティブ","メディア","媒体","集客")
NEGATIVE=("システム販売のみ","商材販売のみ","設備工事のみ")
HOSTED=("forms.gle","docs.google.com","form.run","tayori.com","form-mailer.jp","formzu.net","kintoneapp.com")

def norm(s): return re.sub(r"[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+","",unicodedata.normalize("NFKC",s or "").lower().replace("株式会社","").replace("有限会社","").replace("合資会社",""))
def domain(u):
    try:
        h=(urlparse(u).hostname or "").lower(); return h[4:] if h.startswith("www.") else h
    except: return ""
def text(raw):
    s=BeautifulSoup(raw,"html.parser")
    for x in s(["script","style","noscript","svg"]): x.decompose()
    return re.sub(r"\s+"," ",s.get_text("。",strip=True))
def get(url,timeout=12):
    try:
        r=requests.get(url,headers={"User-Agent":UA},timeout=timeout,allow_redirects=True)
        return r.status_code,r.url,r.text if "html" in r.headers.get("content-type","").lower() or not r.headers.get("content-type") else ""
    except: return 0,url,""
def search(name,area):
    q=quote_plus(f'"{name}" {area} 公式')
    st,u,raw=get("https://www.google.com/search?q="+q,15)
    links=[]
    if raw:
        soup=BeautifulSoup(raw,"html.parser")
        for a in soup.select("a[href]"):
            href=a.get("href","")
            if href.startswith("/url?q="): href=parse_qs(urlparse(href).query).get("q",[""])[0]
            if href.startswith("http") and domain(href) and not any(domain(href).endswith(x) for x in BAD_DOMAINS) and href not in links: links.append(href)
    if not links:
        st,u,raw=get("https://html.duckduckgo.com/html/?q="+q,15)
        soup=BeautifulSoup(raw,"html.parser")
        for a in soup.select("a.result__a[href]"):
            href=a.get("href","")
            if "uddg=" in href: href=unquote(parse_qs(urlparse(href).query).get("uddg",[href])[0])
            if href.startswith("http") and not any(domain(href).endswith(x) for x in BAD_DOMAINS): links.append(href)
    return links[:6]
def has_form(raw,url):
    if any(domain(url).endswith(x) for x in HOSTED): return True
    if not raw:return False
    for f in re.findall(r"(?is)<form\b.*?</form>",raw):
        n=f.lower()
        if "textarea" in n or "type=\"email\"" in n or "お問い合わせ" in f or "送信" in f:return True
    return bool(re.search(r"(?i)contact-form-7|mw_wp_form|formrun|hubspot|form-mailer|formzu",raw))
def audit(r):
    candidates=search(r["company_name"],r["area"])
    official=""; raw=""; body=""; status=0
    nn=norm(r["company_name"])
    for u in candidates:
        st,fu,rr=get(u)
        tt=text(rr) if rr else ""
        if st<400 and rr and (nn in norm(tt[:12000]) or nn in norm((BeautifulSoup(rr,"html.parser").title.string if BeautifulSoup(rr,"html.parser").title and BeautifulSoup(rr,"html.parser").title.string else ""))):
            official=fu;raw=rr;body=tt;status=st;break
    links=[]
    if raw:
        soup=BeautifulSoup(raw,"html.parser")
        for a in soup.select("a[href]"):
            label=(a.get_text(" ",strip=True)+" "+a.get("href","")).lower()
            u=urljoin(official,a.get("href",""))
            if domain(u)==domain(official) and any(k in label for k in ("contact","inquiry","お問い合わせ","お問合せ","会社概要","company","service","事業")) and u not in links:links.append(u)
    pages=[(official,raw,body)] if official else []
    for u in links[:4]:
        st,fu,rr=get(u); pages.append((fu,rr,text(rr) if rr else ""))
    combined="。".join(p[2] for p in pages)
    service_hits=[k for k in SERVICE if k.lower() in combined.lower()]
    contact="";form=False
    for u,rr,tt in pages:
        if has_form(rr,u):contact=u;form=True;break
    if not contact:
        for u in links:
            if any(k in u.lower() for k in ("contact","inquiry","form")):
                st,fu,rr=get(u); 
                if has_form(rr,fu): contact=fu;form=True;break
    if not official: decision="確認不能";reason="公式サイトを確定できず"
    elif not service_hits: decision="除外";reason="広告・Web・SNS・販促・PR等の受託根拠を確認できず"
    elif not form: decision="除外";reason="実在する問い合わせフォーム未確認"
    else: decision="送付対象";reason="JLAA会員かつ関連受託サービス・実フォーム確認"
    comment=f"【判定根拠】{reason}｜受託={('・'.join(service_hits[:8]) if service_hits else '確認できず')}｜窓口={('実フォーム確認' if form else '実フォーム未確認')}｜継続支援の明記有無は送付可否に不使用｜【営業仮説・未確認】GBP運用を追加施策・外注として提案できる可能性｜根拠URL={official or 'なし'}"+(f" ; {contact}" if contact else "")+"｜監査日=2026-08-12"
    return {**r,"url":official,"contact_url":contact,"service_hits":" / ".join(service_hits),"decision":decision,"reason":reason,"comment":comment,"http_status":status,"search_candidates":" / ".join(candidates)}

rows=list(csv.DictReader(SRC.open(encoding="utf-8-sig",newline="")))
targets=[r for r in rows if r["existing_match"]=="no" and r["enterprise_prefilter"]=="pass" and "中広" not in r["company_name"]]
out=[]
with ThreadPoolExecutor(max_workers=10) as ex:
    fs={ex.submit(audit,r):r for r in targets}
    for i,f in enumerate(as_completed(fs),1):out.append(f.result());print(f"progress={i}/{len(targets)}",flush=True)
out.sort(key=lambda r:r["company_name"])
fields=list(out[0])
with (RUN/"jlaa_deep_audit_33.csv").open("w",encoding="utf-8-sig",newline="") as fh:w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(out)
c={k:sum(r["decision"]==k for r in out) for k in ("送付対象","除外","確認不能")}
rep={"targets":len(out),"counts":c,"blank_decision":sum(not r["decision"] for r in out),"blank_comment":sum(not r["comment"] for r in out),"audit":str(RUN/"jlaa_deep_audit_33.csv")}
(RUN/"deep_audit_summary.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(rep,ensure_ascii=False,indent=2))
