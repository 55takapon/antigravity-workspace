import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

URLS = [
"https://clinic-promotion.com/", "https://www.seitai-homepage.com/", "https://media-hack.co.jp/",
"https://www.clinic-seoplus.com/", "https://medical-grits.jp/", "https://www.souki-inc.co.jp/hp/dental/",
"https://gourmet.z-it.jp/", "https://clinic.z-it.jp/", "https://www.method-innovation.co.jp/",
"https://graciauto.jp/services/salon-hp/", "https://salone-web.com/", "https://halope.co.jp/halope-web.html",
"https://www.medico-consulting.jp/", "https://clinic-mkt.com/", "https://bau-marketing.jp/",
"https://prime-concept.co.jp/service/yoyaku.php",
]
PAT = re.compile(r"(?:株式会社|有限会社|合同会社)\s*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]+\s*(?:株式会社|有限会社|合同会社)")
for url in URLS:
    try:
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=25); r.encoding=r.apparent_encoding
        s=BeautifulSoup(r.text,"html.parser"); texts=[s.get_text(" ",strip=True)]
        for a in s.select("a[href]"):
            href=urljoin(r.url,a.get("href","")); sig=a.get_text(" ",strip=True)+" "+href
            if (urlparse(href).hostname or "").removeprefix("www.") != (urlparse(r.url).hostname or "").removeprefix("www."):
                continue
            if re.search(r"会社|運営|about|company|corporate|profile",sig,re.I):
                try:
                    q=requests.get(href,headers={"User-Agent":"Mozilla/5.0"},timeout=20); q.encoding=q.apparent_encoding
                    texts.append(BeautifulSoup(q.text,"html.parser").get_text(" ",strip=True))
                except Exception: pass
        found=[]
        for m in PAT.finditer(" ".join(texts)):
            v=m.group(0).strip()
            if v not in found: found.append(v)
        print(url, found[:12])
    except Exception as e: print(url,type(e).__name__)
