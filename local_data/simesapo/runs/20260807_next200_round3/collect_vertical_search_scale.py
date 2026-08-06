from __future__ import annotations

import base64, csv, json, re, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
OUT=HERE/"vertical_search_scale_raw.csv"; SEED=HERE/"vertical_search_scale_seed.csv"; AUDIT=HERE/"vertical_search_scale_audit.csv"
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
TARGETS={
"医科・歯科":["歯科医院 専門","クリニック 専門"],
"美容室・サロン":["美容室 サロン 専門"],
"治療院":["整骨院 整体院 専門"],
"動物病院・ペット":["動物病院 ペットサロン 専門"],
"学習塾・スクール":["学習塾 スクール 専門"],
"旅館・ホテル":["旅館 ホテル 専門"],
"飲食店":["飲食店 レストラン 専門"],
"フィットネス":["パーソナルジム フィットネス 専門"],
"保育園・幼稚園":["保育園 幼稚園 専門"],
"不動産会社":["不動産会社 専門"],
"士業":["士業 税理士 行政書士 専門"],
}
REGIONS=["北海道","東北","東京","関東","北陸","名古屋","大阪","中国地方","四国","福岡"]
BLOCKED={"youtube.com","facebook.com","instagram.com","x.com","wikipedia.org","prtimes.jp","wantedly.com","indeed.com","en-gage.net","note.com","ameblo.jp","reddit.com","amazon.co.jp","rakuten.co.jp"}
LEGAL=re.compile(r"(?:株式会社|有限会社|合同会社|税理士法人|社会保険労務士法人|司法書士法人|行政書士法人)\s*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+\s*(?:株式会社|有限会社|合同会社)")
NOISE=re.compile(r"会社名|会社概要|社名|住所|所在地|ご提供|ホームページ|Google|GOOGLE|お客様|取引先|採用|確認画面|株式会社様|様株式会社")
PROFILE=re.compile(r"会社概要|会社情報|企業情報|運営会社|法人概要|about|company|corporate|profile",re.I)
CONTACT=re.compile(r"contact|inquiry|toiawase|otoiawase|form|お問い合わせ|お問合せ|問合せ|ご相談|見積",re.I)

def host(u): return (urlparse(u).hostname or "").lower().removeprefix("www.")
def unwrap(u):
    if host(u)=="bing.com":
        x=parse_qs(urlparse(u).query).get("u",[""])[0]
        if x.startswith("a1"):
            try:return base64.b64decode(x[2:]+"===").decode()
            except Exception:return ""
    return u
def search(item):
    label,target,region=item; q=f"{target} ホームページ制作 Web集客 運用 {region} 会社"
    try:r=requests.get("https://www.bing.com/search",params={"q":q,"count":"15"},headers=HEADERS,timeout=25); r.raise_for_status()
    except Exception:return []
    s=BeautifulSoup(r.text,"html.parser"); out=[]
    for a in s.select("li.b_algo h2 a[href]"):
        u=unwrap(a.get("href","")); d=host(u)
        if u.startswith("http") and d and not any(d==b or d.endswith("."+b) for b in BLOCKED): out.append((d,u,label,q))
    return out[:10]
def fetch(u):
    r=requests.get(u,headers=HEADERS,timeout=22,allow_redirects=True); r.raise_for_status()
    if "html" not in r.headers.get("content-type","").lower(): raise ValueError("non_html")
    r.encoding=r.apparent_encoding; return r.url,BeautifulSoup(r.text,"html.parser")
def plausible(v):
    v=re.sub(r"\s+","",v.strip())
    return v if 4<=len(v)<=45 and LEGAL.fullmatch(v) and not NOISE.search(v) else ""
def json_names(obj):
    found=[]
    if isinstance(obj,dict):
        typ=obj.get("@type",[]); typ=[typ] if isinstance(typ,str) else typ
        if any(t in {"Organization","Corporation","LocalBusiness","ProfessionalService"} for t in typ):
            for k in ["legalName","name"]:
                if isinstance(obj.get(k),str): found.append(obj[k])
        for v in obj.values(): found.extend(json_names(v))
    elif isinstance(obj,list):
        for v in obj: found.extend(json_names(v))
    return found
def extract_name(pages):
    candidates=[]
    for _,s in pages:
        for node in s.select('script[type="application/ld+json"]'):
            try:
                for v in json_names(json.loads(node.get_text())):
                    m=LEGAL.search(v); candidates.append(plausible(m.group(0)) if m else "")
            except Exception: pass
        for tr in s.select("tr"):
            cells=tr.find_all(["th","td"])
            if len(cells)>=2 and re.fullmatch(r"会社名|社名|法人名|運営会社",cells[0].get_text(" ",strip=True)):
                m=LEGAL.search(cells[1].get_text(" ",strip=True)); candidates.append(plausible(m.group(0)) if m else "")
        for dt in s.select("dt"):
            if re.fullmatch(r"会社名|社名|法人名|運営会社",dt.get_text(" ",strip=True)) and dt.find_next_sibling("dd"):
                m=LEGAL.search(dt.find_next_sibling("dd").get_text(" ",strip=True)); candidates.append(plausible(m.group(0)) if m else "")
        text=s.get_text(" ",strip=True)
        for m in re.finditer(r"(?:会社名|社名|法人名|運営会社)\s*[：:]?\s*(.{0,60})",text):
            n=LEGAL.search(m.group(1)); candidates.append(plausible(n.group(0)) if n else "")
    candidates=[c for c in candidates if c]
    if not candidates:return ""
    counts=Counter(candidates); name,count=counts.most_common(1)[0]
    return name if count>=1 and (len(counts)==1 or count>=2) else ""
def validate(item):
    _,u,label,q=item
    audit={"searched_url":u,"domain":host(u),"label":label,"query":q,"result":"","company_name":"","support_terms":"","continuous":"","contact_url":""}
    try: base,page=fetch(u)
    except Exception as e:
        audit["result"]="fetch_error:"+type(e).__name__; return None,audit
    pages=[(base,page)]; prof=[]; contacts=[]
    for a in page.select("a[href]"):
        href=urljoin(base,a.get("href","")); sig=a.get_text(" ",strip=True)+" "+href
        if host(href)!=host(base):continue
        if PROFILE.search(sig):prof.append(href)
        if CONTACT.search(sig) and not re.search(r"採用|recruit|privacy|ログイン",sig,re.I):contacts.append(href.split("#",1)[0])
    for href in list(dict.fromkeys(prof))[:5]:
        try: pages.append(fetch(href))
        except Exception:pass
    name=extract_name(pages)
    if not name:
        audit["result"]="company_name_unconfirmed"; return None,audit
    audit["company_name"]=name
    text=" ".join(s.get_text(" ",strip=True) for _,s in pages)
    support=[w for w in ["Web集客","WEB集客","ホームページ制作","Web制作","WEB制作","広告運用","SNS運用","SEO","MEO","Googleマップ"] if w in text]
    continuous=any(w in text for w in ["運用","保守","継続","伴走","サポート","月額"])
    audit["support_terms"]="・".join(support); audit["continuous"]="1" if continuous else "0"
    if len(support)<2:
        audit["result"]="digital_evidence_short"; return None,audit
    if not continuous:
        audit["result"]="continuous_evidence_missing"; return None,audit
    contact=list(dict.fromkeys(contacts))[0] if contacts else ""
    audit["contact_url"]=contact
    if not contact:
        audit["result"]="contact_missing"; return None,audit
    audit["result"]="accepted"
    return {"company_name":name,"url":base,"address":"","phone":"","contact_url":contact,"区分":f"S｜{label}特化Web・集客支援","検出ワード":f"公式サイト確認：{label}顧客＋"+"・".join(support[:3])+"＋継続支援","source_url":q},audit

items=[(label,target,region) for label,targets in TARGETS.items() for target in targets for region in REGIONS]
hits=[]
with ThreadPoolExecutor(max_workers=8) as pool:
    for group in pool.map(search,items):hits.extend(group)
unique={d:(d,u,label,q) for d,u,label,q in hits}
results=[]; audits=[]
with ThreadPoolExecutor(max_workers=16) as pool:
    futures=[pool.submit(validate,item) for item in unique.values()]
    for f in as_completed(futures):
        r,a=f.result(); audits.append(a)
        if r:results.append(r)
results=list({host(r["url"]):r for r in results}.values()); results.sort(key=lambda r:r["company_name"])
for path,rows in [(OUT,results),(SEED,results)]:
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        fields=["company_name","url","address","phone","contact_url","区分","検出ワード","source_url"]
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
with AUDIT.open("w",encoding="utf-8-sig",newline="") as f:
    fields=["searched_url","domain","label","query","result","company_name","support_terms","continuous","contact_url"]
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(audits)
print({"queries":len(items),"search_domains":len(unique),"strict_candidates":len(results),"reasons":dict(Counter(a["result"] for a in audits)),"seed":str(SEED)})
