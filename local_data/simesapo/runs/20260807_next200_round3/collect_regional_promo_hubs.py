from __future__ import annotations

import argparse, csv, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SOURCES = [
    "https://ishikawa-pia.jp/member-list/",
    "https://www.nagano-pia.jp/guide/list-nagano.php",
    "https://www.nagano-pia.jp/guide/list-hokushin.php",
    "https://www.nagano-pia.jp/guide/list-toshin.php",
    "https://www.nagano-pia.jp/guide/list-chushin.php",
    "https://www.nagano-pia.jp/guide/list-nanshin.php",
    "https://kapia.jp/member/",
    "https://okiinkyo.or.jp/member/",
    "https://www.k-pia.jp/member-list.php",
    "https://www.aca-j.or.jp/meibo/",
    "https://www.aca-j.or.jp/meibo_test/",
    "https://www.nagasaki-pia.org/index.php?page_id=23",
    "https://www.hyoinko.or.jp/union/organization/branchlist/",
    "https://kyoinko.jp/member/",
    "https://fukuoka-pia.or.jp/list/",
    "https://www.fukuinkyo.or.jp/list/",
    "https://osaka-pia.or.jp/members/",
    "https://www.ai-in-ko.or.jp/organization/member.html",
    "https://hiroshima-pia.jp/register/link/",
    "https://hiroshima-pia.jp/register/kumiaiin/",
    "https://www.opia.or.jp/member/other",
    "https://www.opia.or.jp/member/okayama",
    "https://www.print.or.jp/association/sapporo.html",
    "https://www.print.or.jp/association/douou.html",
    "https://www.print.or.jp/association/dounan.html",
    "https://www.print.or.jp/association/douhoku.html",
    "https://www.print.or.jp/association/doutou.html",
    "https://www.niigata-ad55.jp/member.html",
    "https://haaa.or.jp/member.html",
    "https://sendai-aaa.jp/?page_id=3887",
    "https://www.hiroshima-ad.jp/",
    "https://kanban.or.jp/?page_id=62",
    "https://hebda.jp/member.php",
    "https://nagoya-ad.jp/sp/members.html",
    "https://www.aichi-ad.or.jp/%E4%BC%9A%E5%93%A1%E4%BC%81%E6%A5%AD%E4%B8%80%E8%A6%A7/",
    "https://fukuoka-ad.org/",
    "https://www.shizuoka-ad.jp/",
    "https://www.akb.ne.jp/list.html",
    "https://www.daikokyo.or.jp/meibo.html",
    "https://www.tokobi.or.jp/member/01.html",
    "https://www.tokobi.or.jp/member/02.html",
    "https://www.tokobi.or.jp/member/03.html",
    "https://www.tokobi.or.jp/member/04.html",
    "https://www.tokobi.or.jp/member/05.html",
    "https://www.tokobi.or.jp/member/06.html",
    "https://kyukouren.jp/fukuoka-si/member.html",
    "https://shinkobi.or.jp/%E5%8D%94%E4%BC%9A%E3%81%AE%E4%BC%9A%E5%93%A1",
    "https://www.chikoubi.net/member.php",
    "https://www.kyokobi.jp/",
    "https://www.kyoto-ad.gr.jp/about/companies/",
    "https://shizukobi.com/searches/",
    "https://saikoukyou.jp/union.html",
    "https://f-kanban.jp/member/",
    "https://www.hyokobi.net/union/",
    "https://www.ibakoubi.com/office/",
    "https://www.shinkoubi.jp/okugai_list.html",
    "https://www.taaa.gr.jp/",
    "https://aokoubi.com/member/aomori.html",
    "https://aokoubi.com/member/hachinohe.html",
    "https://aokoubi.com/member/hirosaki.html",
    "https://ishikoukyo.jp/member_2025",
    "https://www.iwate-aaa.jp/member/index.html",
    "https://www.o-kanban.com/union-member.php",
    "https://kakoukyou.com/member/",
    "https://kagoshima-aaa.jp/",
    "https://www.daikokyo.or.jp/meibo_list.php",
]

UA = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
SERVICE = re.compile(r"Web制作|ウェブ制作|ホームページ制作|サイト制作|広告代理|広告企画|集客支援|マーケティング|販促支援|販促企画|ブランディング|動画制作|映像制作|SNS運用|プロモーション|企画.{0,8}デザイン", re.I)
CONTACT = re.compile(r"contact|inquiry|お問い合わせ|お問合せ|問い合わせ|ご相談|相談フォーム", re.I)
SIGN_SERVICE = re.compile(r"看板.{0,12}(?:企画|デザイン)|店舗サイン|屋外広告", re.I)
COMPANY = re.compile(r"会社概要|企業情報|about|company|corporate", re.I)
BAD_HOST = re.compile(r"facebook|instagram|twitter|x\.com|youtube|line\.me|google|yahoo|amazon|rakuten|pia\.jp$|aca-j\.or\.jp$|nagasaki-pia\.org$|\.go\.jp$|city\.|pref\.|mhlw|fujitv|tv-tokyo|j-wave|mainichi|netcommons|jfpi|aj-pia|print\.or\.jp|printing\.or\.jp|insatsu-navi|pjl\.co\.jp|insatsutimes", re.I)
BAD_NAME = re.compile(r"工業組合|協同組合|連合会|中央会|厚生労働省|市役所|県庁|生命保険|コダック|モトヤ|エコスリー|リコー|ハイデルベルグ|ポータルサイト|^HP\b|^URL\b|^Home$|^HOME$|Powered by|^\d+[.．]", re.I)
CORP = re.compile(r"(?:株式会社|有限会社|合同会社|合資会社|一般社団法人|㈱|（株）|\(株\))[^｜|–—\n]{1,45}|[^｜|–—\n]{1,45}(?:株式会社|有限会社|合同会社|㈱|（株）|\(株\))")

def host(u: str) -> str:
    return (urlparse(u).hostname or "").lower().removeprefix("www.")

def get(url: str):
    try:
        r = requests.get(url, headers=UA, timeout=12, allow_redirects=True)
        if r.status_code < 400 and "text/html" in r.headers.get("content-type", ""):
            r.encoding = r.apparent_encoding or r.encoding
            return r
    except Exception:
        pass
    return None

def clean_name(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    m = CORP.search(s)
    if m:
        s = m.group(0).strip(" -–—|｜:：")
    s = s.replace("㈱", "株式会社").replace("（株）", "株式会社").replace("(株)", "株式会社")
    return s[:80]

def official_name(soup: BeautifulSoup, hinted: str) -> str:
    choices = []
    for node in soup.select('script[type="application/ld+json"]'):
        for m in re.finditer(r'"name"\s*:\s*"([^"\\]{2,80})"', node.get_text(" ", strip=True)):
            choices.append(m.group(1))
    og = soup.select_one('meta[property="og:site_name"]')
    if og: choices.append(og.get("content", ""))
    if soup.title:
        choices.extend(re.split(r"[|｜–—]", soup.title.get_text(" ", strip=True)))
    choices.append(hinted)
    body = soup.get_text(" ", strip=True)[:30000]
    corp_pat = re.compile(r"(?:株式会社|有限会社|合同会社)\s*[A-Za-z0-9一-龠ぁ-んァ-ヶー・＆& ]{2,35}|[A-Za-z0-9一-龠ぁ-んァ-ヶー・＆& ]{2,35}\s*(?:株式会社|有限会社|合同会社)")
    choices.extend(m.group(0) for m in corp_pat.finditer(body))
    for c in choices:
        n = clean_name(c)
        if 2 < len(n) <= 60 and n not in {"株式会社","有限会社","合同会社"} and not BAD_NAME.search(n) and not re.search(r"TEL|FAX|〒|https?://", n, re.I):
            return n
    return ""

def source_links(url: str):
    r = get(url)
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    sh = host(r.url)
    for a in soup.select("a[href]"):
        u = urljoin(r.url, a.get("href", ""))
        h = host(u)
        if not h or h == sh or BAD_HOST.search(h): continue
        if urlparse(u).scheme not in ("http", "https"): continue
        context = a.get_text(" ", strip=True)
        par = a.find_parent(["li", "tr", "article", "section", "div"])
        if par: context = par.get_text(" ", strip=True)[:500]
        out.append((u, clean_name(context), url))
    return out

def inspect(item):
    u, hinted, source = item
    r = get(u)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    if not (SERVICE.search(text) or SIGN_SERVICE.search(text)): return None
    final = r.url
    h = host(final)
    if BAD_HOST.search(h): return None
    name = official_name(soup, hinted)
    if len(name) < 3 or BAD_NAME.search(name): return None
    links = []
    profile = ""
    for a in soup.select("a[href]"):
        label = a.get_text(" ", strip=True)
        x = urljoin(final, a.get("href", ""))
        if host(x) != h: continue
        if CONTACT.search(label + " " + x): links.append(x)
        if not profile and COMPANY.search(label + " " + x): profile = x
    for cu in dict.fromkeys(links[:8]):
        cr = get(cu)
        if not cr: continue
        cs = BeautifulSoup(cr.text, "html.parser")
        if cs.select_one("form") and not re.search(r"採用|求人|recruit", cu + cs.get_text(" ", strip=True)[:400], re.I):
            evidence = sorted(set(m.group(0) for m in SERVICE.finditer(text[:25000])))[:6]
            return {"company_name": name, "url": final, "address": "", "phone": "", "contact_url": cr.url,
                    "区分": "A｜地域広告・販促・Web支援", "検出ワード": "公式サイト確認：" + "＋".join(evidence),
                    "source_url": source, "profile_url": profile, "company_confirmed": "yes", "fetch": "ok"}
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", required=True); a = ap.parse_args()
    raw = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for links in ex.map(source_links, SOURCES): raw.extend(links)
    unique = {}
    for x in raw: unique.setdefault(host(x[0]), x)
    rows = []
    with ThreadPoolExecutor(max_workers=16) as ex:
        futures = [ex.submit(inspect, x) for x in unique.values()]
        for f in as_completed(futures):
            v = f.result()
            if v: rows.append(v)
    rows.sort(key=lambda r: r["company_name"])
    fields = ["company_name","url","address","phone","contact_url","区分","検出ワード","source_url","profile_url","company_confirmed","fetch"]
    with open(a.output, "w", encoding="utf-8-sig", newline="") as fh:
        w=csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
    print({"source_links": len(raw), "unique_domains": len(unique), "qualified_with_form": len(rows), "output": a.output})

if __name__ == "__main__": main()
