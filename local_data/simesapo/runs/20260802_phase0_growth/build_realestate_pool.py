from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"C:\Users\hangy\.gemini\antigravity\.codex\simesapo\runs\20260802_phase0_growth\realestate\qualified.csv")
OUTPUT = ROOT / "realestate_candidate_pool.csv"
MASTER = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\custmize\enterprise_filter")
HEADERS = ["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","H1","区分","検出ワード"]

REPAIRS = {
    "https://www.fudoukun.jp/": "不動くん株式会社",
    "https://servithink.co.jp/": "株式会社サービシンク",
    "https://active-rt.com/": "株式会社アクティブリテック",
    "https://info.spacely.co.jp/": "株式会社スペースリー",
}
REMOVE = {"https://growing-scale.com/", "https://www.ielove-group.jp/"}
MANUAL = [
    ("株式会社ディープ","https://www.deep-deep.jp/","https://www.deep-deep.jp/contact/","不動産会社専門Web制作・集客支援"),
    ("株式会社アドクルー","https://www.adcrew.jp/","https://www.adcrew.jp/contact/","不動産業界特化広告運用・Webマーケティング"),
    ("株式会社LightDoor","https://lightdoor.jp/","https://lightdoor.jp/contact/","不動産業界特化SNS・広告・SEO支援"),
    ("株式会社ウルフ","https://realestate.wolf-sns.com/","https://realestate.wolf-sns.com/#contact","不動産会社向けSNS運用・広告支援"),
    ("株式会社Live Search","https://livesearch.co.jp/","https://livesearch.co.jp/contact/","不動産会社向け物件コンテンツ・SNS支援"),
    ("株式会社ウィンクマーク","https://winkmark.co.jp/","https://winkmark.co.jp/contact/","住宅・不動産向けSNS動画マーケティング"),
    ("住宅ブランドコンサルティング株式会社","https://brandconsulting.co.jp/","https://brandconsulting.co.jp/contact/","住宅・不動産の集客・ブランド支援"),
    ("株式会社EIGHT","https://eight-inc.net/","https://eight-inc.net/contact/","不動産・住宅業界特化マーケティング"),
    ("株式会社ラルズネット","https://www.rals.co.jp/","https://www.rals.co.jp/contact/","不動産会社向け集客・Web制作"),
    ("株式会社LEFANA","https://www.lefana.net/","https://www.lefana.net/contact","不動産向けブランディング・SNS・Web制作"),
    ("株式会社KRone","https://www.krone.company/","https://www.krone.company/contact","不動産業向けSNS・Web集客支援"),
    ("株式会社IRODORITO","https://irodorito.com/","https://irodorito.com/contact/","不動産・住宅向けショート動画・SNS支援"),
    ("株式会社ウィズモー","https://withmo.co.jp/","https://withmo.co.jp/contact/","住宅不動産業界向けSNS・営業支援"),
    ("株式会社ミトリア","https://mitoria.jp/","https://mitoria.jp/contact/","不動産業界特化マーケティング支援"),
    ("株式会社Webroom","https://webroom.jp/","https://webroom.jp/contact/","住宅・不動産業界向けWeb広告支援"),
    ("株式会社Delight Hub","https://delight-hub.jp/","https://delight-hub.jp/contact/","住宅・不動産会社向け営業DX支援"),
    ("株式会社ゼルダ","https://fudosan.zeldainc.com/","https://fudosan.zeldainc.com/contact/","不動産会社向けWeb制作・集客支援"),
    ("株式会社クラスココンサルファーム","https://www.class-consul.jp/","https://www.class-consul.jp/contact/","不動産会社向け経営・集客支援"),
    ("株式会社Facilo","https://facilo.jp/","https://facilo.jp/contact/","不動産仲介会社向け営業支援クラウド"),
    ("株式会社カナリー","https://www.canarycloud.jp/","https://www.canarycloud.jp/contact/","不動産仲介会社向け業務支援SaaS"),
    ("株式会社Housmart","https://www.housmart.co.jp/","https://www.housmart.co.jp/contact/","不動産営業支援・顧客管理クラウド"),
    ("株式会社リアルティバンク","https://www.realty-bank.com/","https://www.realty-bank.com/contact/","不動産会社向け販売図面・業務DX"),
    ("リコノミカル株式会社","https://www.reconomical.co.jp/","https://www.reconomical.co.jp/contact/","不動産会社向けシステム導入・DX支援"),
    ("株式会社リーテック","https://www.retech-network.com/","https://www.retech-network.com/contact/","不動産会社向けIT・集客支援"),
    ("株式会社ネオス","https://www.service.neos.ne.jp/","https://www.service.neos.ne.jp/contact/","住宅不動産向け集客・業務DX支援"),
    ("業プロ株式会社","https://noseru.gyo-pro.co.jp/","https://www.gyo-pro.co.jp/contact.html","不動産会社向け物件情報・Web運用支援"),
    ("株式会社T.S.M","https://ts-marketinglab.com/","https://ts-marketinglab.com/contact","不動産・住宅業界向け集客支援"),
    ("株式会社マーサリー","https://marsary.co.jp/","https://marsary.co.jp/#contact","不動産業界向けWeb集客・DX支援"),
    ("WINDOM株式会社","https://windom-kk.co.jp/","https://windom-kk.co.jp/contact/","不動産業界特化SEO・Web集客支援"),
    ("株式会社SMART","https://r-marketing.info/","https://r-marketing.info/contact/","小規模不動産会社向け開業・集客支援"),
    ("レイルリンク株式会社","https://raillink.jp/","https://raillink.jp/contacts/","不動産会社向けDX・Web制作支援"),
    ("株式会社アクティブリテック","https://active-rt.com/","https://active-rt.com/contact/","不動産会社向けDX・システム支援"),
    ("Terra Design株式会社","https://www.terra-design.co.jp/","https://www.terra-design.co.jp/contact/","不動産会社向けMEO・Web・AI支援"),
    ("株式会社商報","https://www.shoho.co.jp/","https://www.shoho.co.jp/contact","不動産業界向け動画・Web・販促支援"),
    ("株式会社ワンノブアカインド","https://www.one-of-a-kind.co.jp/","https://www.one-of-a-kind.co.jp/contact/","不動産会社向けWeb制作・集客支援"),
    ("株式会社SHO-SAN","https://www.sho-san.co.jp/","https://www.sho-san.co.jp/contact/","住宅・不動産業界特化マーケティング支援"),
    ("株式会社クリエイティブバンク","https://www.sales-dx.jp/","https://www.sales-dx.jp/contact","不動産業界向けSEO・MEO・Web集客支援"),
    ("株式会社Acsport","https://acsport.net/","https://acsport.net/contact/","不動産会社向けWeb制作・集客支援"),
    ("株式会社coco","https://www.cocoreview.com/","https://www.cocoreview.com/contact/","不動産店舗向け口コミ・MEO集客支援"),
    ("株式会社クラスコデザインスタジオ","https://www.clasco-ds.jp/","https://www.clasco-ds.jp/contact/","不動産会社向けブランディング・Web支援"),
    ("株式会社リアプロ","https://www.realnetpro.com/","https://www.realnetpro.com/contact/","不動産会社向け物件・業務支援システム"),
    ("株式会社イクラ","https://iqra.co.jp/","https://iqra.co.jp/contact/","不動産会社向け売却集客・業務支援"),
    ("株式会社すむたす","https://sumutasu.co.jp/","https://sumutasu.co.jp/contact/","不動産会社向け査定・売却DX支援"),
    ("株式会社リコシス","https://www.recosys.co.jp/","https://www.recosys.co.jp/contact/","不動産会社向け業務システム・Web支援"),
    ("株式会社アドマックス","https://www.admax.jp/","https://www.admax.jp/contact/","不動産広告・Webマーケティング支援"),
    ("株式会社デジタルゴリラ","https://digital-gorilla.co.jp/","https://digital-gorilla.co.jp/contact/","不動産会社向けSNS運用・集客支援"),
    ("株式会社solezore","https://solezore.co.jp/","https://solezore.co.jp/contact/","不動産業界向けSNS運用支援"),
    ("株式会社ビジュアルリサーチ","https://www.visualresearch.jp/","https://www.visualresearch.jp/contact/","不動産会社向けWeb・SNS・業務DX支援"),
    ("株式会社現次","https://genji-group.com/","https://genji-group.com/contact/","住宅業界向けSNS・イベント集客支援"),
    ("株式会社ジソウ","https://jisou.co.jp/","https://jisou.co.jp/contact/","住宅・不動産企業向けSNS内製化支援"),
    ("株式会社BOTANICO","https://botanico.co.jp/","https://botanico.co.jp/contact/","住宅・不動産向けSNS運用支援"),
    ("株式会社ロカオプ","https://locaop.jp/","https://locaop.jp/contact/","不動産店舗向けMEO・口コミ集客支援"),
    ("株式会社新大陸","https://shintairiku.jp/","https://shintairiku.jp/contact/","住宅・不動産業界向けWeb・SNS集客支援"),
    ("株式会社ゴッタライド","https://www.gotta-ride.com/","https://www.gotta-ride.com/contact/","住宅・不動産会社向けWeb集客支援"),
    ("株式会社コンベックス","https://www.conve-x.jp/","https://www.conve-x.jp/contact/","住宅・不動産会社向け追客・営業支援"),
    ("株式会社リフィード","https://re-feed.jp/","https://re-feed.jp/contact/","住宅・不動産会社向け販促・DX支援"),
    ("株式会社ダンドリワーク","https://dandori-work.com/","https://dandori-work.com/contact/","住宅・不動産会社向け業務DX支援"),
    ("株式会社えびすマート","https://www.ebisumart.com/","https://www.ebisumart.com/contact/","不動産・住宅会社向けデジタル支援"),
    ("株式会社アババイ","https://ababai.co.jp/","https://ababai.co.jp/contact/","住宅・不動産業界向けWeb集客支援"),
    ("株式会社ゴデスクリエイト","https://www.goddess-c.com/","https://www.goddess-c.com/contact/","住宅・不動産会社向けWeb・集客支援"),
    ("株式会社ミカタ","https://mikataga.jp/","https://mikataga.jp/#contact","工務店・建築会社向けWeb制作・広告・SNS運用支援"),
    ("SWODA株式会社","https://swoda.co.jp/","https://swoda.co.jp/contact/","住宅・建築会社向けマーケティング・Web支援"),
    ("株式会社ゼンリン東海","https://zenrin-tokai.co.jp/","https://zenrin-tokai.co.jp/contact/","工務店向けWeb制作・広告・DX支援"),
    ("株式会社チタン","https://www.titun.jp/","https://www.titun.jp/contact","工務店・不動産会社向けWeb制作・広告・SNS支援"),
    ("マスタープラン株式会社","https://www.masterplan-dx.com/","https://www.masterplan-dx.com/contact/","工務店・リフォーム会社向けWeb集客・DX支援"),
    ("株式会社G-Force","https://gforce-inc.co.jp/","https://gforce-inc.co.jp/contact/","住宅会社向けマーケティング・SNS・広告支援"),
    ("UNIIDEO株式会社","https://uniideo.com/","https://info.uniideo.com/inhows/contact/","工務店・不動産会社向けブランド・Web集客支援"),
    ("合同会社ウノマス","https://unomas.jp/","https://unomas.jp/contact/","工務店向けSEO・MEO・Web集客支援"),
    ("株式会社シンミドウ","https://sinmido.com/","https://sinmido.com/contact/","工務店向けWeb集客・SNS・広告支援"),
    ("株式会社ゼロスタートラボ","https://conpro-dx.com/","https://conpro-dx.com/#contact","中小建設会社向け業務DX・導入定着支援"),
    ("株式会社建ログ","https://tatelog.biz/","https://tatelog.biz/contact/","建設会社向けDX実装・業務SaaS支援"),
    ("TechBull株式会社","https://www.techbull.co.jp/","https://www.techbull.co.jp/#contact","建設業界特化DX・SaaS導入支援"),
    ("株式会社ネクシア・プロパティ","https://nexiap.com/","https://nexiap.com/#contact","不動産会社向けDX・業務設計・運用支援"),
    ("株式会社つなぐ","https://keysapo.com/","https://keysapo.com/#contact","建設業向け取引先開拓・業務支援サービス"),
    ("リックス工業株式会社","https://licks.co.jp/marketing/","https://licks.co.jp/marketing/contact/","住宅・建築業界向け集客・Web・IT支援"),
    ("sawan株式会社","https://sawan.ne.jp/","https://sawan.ne.jp/contact/","工務店向けWeb集客・DX支援"),
    ("株式会社CONVY","https://convy.co.jp/","https://convy.co.jp/contact/","工務店向けSEO・MEO・SNS集客支援"),
    ("株式会社ラスト・コンパス","https://lastcompass.co.jp/","https://lastcompass.co.jp/contact/","住宅会社向けマーケティング・営業支援"),
    ("株式会社エンパワー","https://empowerjp.com/","https://empowerjp.com/#contact","建設会社向け技術BPO・DX支援"),
]

def norm(v): return re.sub(r"\s+","",unicodedata.normalize("NFKC",v or "").lower())
def ck(v): return re.sub(r"株式会社|有限会社|合同会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:-]","",norm(v))
def dk(v):
    h=urlparse(v if "://" in (v or "") else "https://"+(v or "")).hostname or ""
    return re.sub(r"^www\.","",h.lower())
def read(p): return list(csv.DictReader(p.open(encoding="utf-8-sig",newline="")))
def new(c,u,q,e):
    r={h:"" for h in HEADERS}; r.update(company_name=c,url=u,contact_url=q,区分="S｜業界特化Web制作",検出ワード=f"不動産業界特化支援：{e}"); return r

rows=[]
for raw in read(SOURCE):
    u=raw.get("url","")
    if u in REMOVE: continue
    r={h:raw.get(h,"") for h in HEADERS}; r["company_name"]=REPAIRS.get(u,r["company_name"]); rows.append(r)
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
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
with OUTPUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=HEADERS);w.writeheader();w.writerows(out)
print({"source":len(rows),"kept":len(out),"removed":removed})
