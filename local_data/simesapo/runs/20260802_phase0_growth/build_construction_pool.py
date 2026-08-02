from __future__ import annotations

import csv, re, unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"C:\Users\hangy\.gemini\antigravity\.codex\simesapo\runs\20260802_phase0_growth\construction\qualified.csv")
OUTPUT = ROOT / "construction_candidate_pool.csv"
MASTER = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\custmize\enterprise_filter")
HEADERS = ["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","H1","区分","検出ワード"]

REPAIRS = {
    "https://www.reform-online.jp/": "株式会社リフォーム産業新聞社",
    "https://www.log-build.com/": "株式会社LOG BUILD",
}
REMOVE_DOMAINS = {
    "nikken-times.co.jp", "dxbuild.upbuilder.jp", "sekoukanri-search.com",
    "kenchiku-kyujin.jp", "soken-home.jp",
}
MANUAL = [
    ("株式会社新建新聞社","https://www.s-housing.jp/","https://www.s-housing.jp/contact/","地場工務店向け業界メディア・経営情報支援"),
    ("株式会社住宅新報","https://www.jutaku-s.com/","https://www.jutaku-s.com/contact/","住宅・不動産業界メディア・事業支援"),
    ("株式会社日本住宅新聞社","https://www.jyutaku-news.co.jp/","https://www.jyutaku-news.co.jp/contact/","工務店・住宅業界向け専門メディア"),
    ("株式会社日刊建設工業新聞社","https://www.decn.co.jp/","https://www.decn.co.jp/inquiry","建設業界向け専門メディア・情報支援"),
    ("株式会社日本工業経済新聞社","https://www.nikoukei.co.jp/","https://www.nikoukei.co.jp/contact","建設業界向け専門メディア・入札情報支援"),
    ("株式会社北海道建設新聞社","https://e-kensin.net/","https://e-kensin.plus/databank/e-members.html","地域建設会社向け専門メディア"),
    ("株式会社建設新聞社","https://www.kensetsu-sinbun.co.jp/","https://www.kensetsu-sinbun.co.jp/company/","地域建設業界向け専門メディア"),
    ("株式会社中建日報社","https://www.chukei-news.co.jp/","https://www.chukei-news.co.jp/contact/","中国地方建設業界向け専門メディア"),
    ("株式会社ウェッブアイ","https://www.webi.co.jp/","https://www.webi.co.jp/contact/","建設工程管理・プロジェクト管理支援"),
    ("株式会社アルダグラム","https://aldagram.com/","https://aldagram.com/company/?lng=ja","建設業向け施工管理SaaS支援"),
    ("株式会社ルクレ","https://lecre.jp/","https://lecre.jp/contact/","建設現場向け写真管理・業務DX支援"),
    ("AnyONE株式会社","https://www.any-one.jp/","https://www.any-one.jp/contact/","工務店・リフォーム会社向け業務管理支援"),
    ("コムテックス株式会社","https://www.comtex.co.jp/","https://www.comtex.co.jp/contact/","建設・住宅会社向け施工管理・業務DX支援"),
    ("株式会社A-ZiP","https://a-zip.co.jp/","https://a-zip.co.jp/contact/","建設業向け業務システム・DX支援"),
    ("株式会社Archi Village","https://archi-village.com/","https://archi-village.com/contact/","建材・建設業界向けDXプラットフォーム"),
    ("株式会社KENZO","https://www.kenzo.tech/","https://www.kenzo.tech/contact/","建設業向け受発注・経営DX支援"),
    ("株式会社アステックペイント","https://protimes.jp/","https://protimes.jp/contact/","塗装・リフォーム会社向け加盟・集客支援"),
    ("株式会社オリバー","https://www.gaiso.co/","https://www.gaiso.co/contact/","外装リフォーム会社向けネットワーク・経営支援"),
    ("株式会社住宅産業新聞社","https://www.jyutaku-sangyo.co.jp/","https://www.jyutaku-sangyo.co.jp/contact/","住宅産業向け専門メディア"),
    ("パッチワークス株式会社","https://patchcom.jp/","https://patchcom.jp/#contact","建設業向け施工管理SaaS・人材マッチング"),
    ("合同会社カイリス","https://www.cairis.co.jp/","https://www.cairis.co.jp/#contact","建設業界特化DXコンサルティング"),
    ("Arch株式会社","https://arch-dx.co.jp/","https://arch-dx.co.jp/about","建設現場向けレンタル品管理DX支援"),
    ("Universal Knight合同会社","https://universalknight.com/","https://universalknight.com/#contact","中小建設会社向けAI・CCUS・経営支援"),
    ("AGEC株式会社","https://www.archi-book.com/","https://www.archi-book.com/contact/","建築業界向け情報・業務支援"),
    ("株式会社レクリー","https://sekou-kyujin.com/","https://sekou-kyujin.com/contact/","建設会社向け採用・人材支援"),
    ("株式会社住宅産業研究所","https://www.jyusanken.co.jp/","https://www.jyusanken.co.jp/contact/","住宅会社向け市場調査・経営支援"),
    ("株式会社創樹社","https://www.housing-tribune.com/","https://www.housing-tribune.com/contact/","住宅産業向け専門メディア・情報支援"),
    ("株式会社住宅保証機構","https://www.mamoris.jp/","https://www.mamoris.jp/contact/","住宅事業者向け保証・業務支援"),
    ("株式会社SUMUS","https://sumus-inc.co.jp/","https://sumus-inc.co.jp/contact/","工務店・住宅会社向け経営・組織支援"),
    ("株式会社シップ","https://www.shipinc.co.jp/","https://www.shipinc.co.jp/contact/","リフォーム会社向け経営・集客支援"),
    ("PLEA株式会社","https://www.plea-mm.com/","https://www.plea-mm.com/contact/","工務店向けWebマーケティング・見込客獲得支援"),
    ("TONE株式会社","https://tone-branding.jp/","https://tone-branding.jp/contact/","工務店・住宅会社向けWeb制作・集客支援"),
    ("株式会社コネクターズ","https://www.connectors.jp/","https://www.connectors.jp/contact/","小規模工務店向け集客・事業成長支援"),
    ("トソーマ株式会社","https://tosoma.co.jp/","https://tosoma.co.jp/contact/","リフォーム・建設会社向けWeb集客支援"),
    ("株式会社JACOF","https://jacof.co.jp/","https://jacof.co.jp/contact/","リフォーム会社向けWeb集客・FC支援"),
    ("株式会社ツクノビ","https://tsukunobi.com/","https://tsukunobi.com/ai#contact","建築・建設業界向けAI・BPO・営業支援"),
    ("NO CONTROL株式会社","https://nocontrol-construction.com/","https://nocontrol-construction.com/#contact","建設業界向けAI・DXコンサルティング"),
    ("EthosAI株式会社","https://www.ethosai.co.jp/","https://www.ethosai.co.jp/#contact","製造・建設業向け図面解析AI支援"),
    ("株式会社SUMITSUBO AI","https://sumitsuboai.com/","https://sumitsuboai.com/#contact","建設業向けAI・DXコンサルティング"),
    ("株式会社DeC","https://www.dec-ai.com/","https://www.dec-ai.com/#contact","中小建設会社向けAI導入・業務改善支援"),
    ("株式会社アーキシンフォニー","https://ai.archisymphony.com/","https://ai.archisymphony.com/#contact","建設会社向けAI業務支援・DX人材育成"),
    ("株式会社あかり","https://hikari.akariinc.co.jp/","https://hikari.akariinc.co.jp/#contact","建設業向け生成AI・導入伴走支援"),
    ("Speciate株式会社","https://speciate.co.jp/","https://speciate.co.jp/#contact","建設業向けAI・BIM・DX支援"),
]

def norm(v): return re.sub(r"\s+","",unicodedata.normalize("NFKC",v or "").lower())
def ck(v): return re.sub(r"株式会社|有限会社|合同会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:-]","",norm(v))
def dk(v):
    h=urlparse(v if "://" in (v or "") else "https://"+(v or "")).hostname or ""
    return re.sub(r"^www\.","",h.lower())
def read(p): return list(csv.DictReader(p.open(encoding="utf-8-sig",newline="")))
def new(c,u,q,e):
    r={h:"" for h in HEADERS}; r.update(company_name=c,url=u,contact_url=q,区分="S｜業界特化Web制作",検出ワード=f"建築・工務店特化支援：{e}"); return r

rows=[]
for raw in read(SOURCE):
    d=dk(raw.get("url",""))
    if d in REMOVE_DOMAINS: continue
    r={h:raw.get(h,"") for h in HEADERS}; r["company_name"]=REPAIRS.get(raw.get("url",""),r["company_name"]); rows.append(r)
rows += [new(*x) for x in MANUAL]
confirmed=read(MASTER/"confirmed_enterprise_exclusions.csv"); allow=read(MASTER/"enterprise_false_positive_allowlist.csv"); jpx=read(MASTER/"jpx_listed_companies_20260630.csv"); groups=read(MASTER/"major_group_rules.csv")
cn={ck(r.get("company_name","")) for r in confirmed}; cd={dk(r.get("url","") or r.get("domain","")) for r in confirmed}; ap={(ck(r.get("company_name","")),dk(r.get("url","") or r.get("domain",""))) for r in allow}; jn={ck(r.get("company_name","") or r.get("name","") or r.get("銘柄名","")) for r in jpx}; kw=[norm(r.get("match_value","") or r.get("keyword","") or r.get("判定語","")) for r in groups]
out=[]; seen_n=set(); seen_d=set(); removed=[]
for r in rows:
    n,d=ck(r["company_name"]),dk(r["url"]); pair=(n,d); reason=""
    if not n or not d or not r["contact_url"]: reason="missing"
    elif n in seen_n or d in seen_d: reason="duplicate"
    elif pair not in ap and (n in cn or d in cd): reason="enterprise"
    elif pair not in ap and n in jn: reason="jpx_review"
    elif pair not in ap and any(x and x in norm(r["company_name"]) for x in kw): reason="group_review"
    if reason: removed.append((r["company_name"],reason)); continue
    seen_n.add(n);seen_d.add(d);out.append(r)
with OUTPUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=HEADERS);w.writeheader();w.writerows(out)
print({"source":len(rows),"kept":len(out),"removed":removed})
