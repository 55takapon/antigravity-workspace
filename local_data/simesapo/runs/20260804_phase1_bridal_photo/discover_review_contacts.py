import csv, json, re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
rows=list(csv.DictReader((HERE/'bridal_final_verified_50.csv').open(encoding='utf-8-sig',newline='')))
review={r['idx'] for r in json.loads((HERE/'bridal_contact_validation.json').read_text(encoding='utf-8')) if r['decision']=='review'}
review.add(48)  # 竹野株式会社: current detector selected a login page
for idx,row in enumerate(rows):
    if idx not in review: continue
    print('\n###',idx,row['company_name'],row['url'])
    try:
        r=requests.get(row['url'],headers={'User-Agent':'Mozilla/5.0'},timeout=20)
        s=BeautifulSoup(r.text,'html.parser'); host=(urlparse(r.url).hostname or '').removeprefix('www.')
        found=[]
        for a in s.find_all('a',href=True):
            href=urljoin(r.url,a['href']); txt=a.get_text(' ',strip=True); signal=(txt+' '+href).lower()
            if any(x in signal for x in ('contact','inquiry','form','toiawase','otoiawase','お問い合わせ','お問合せ','問合せ','ご相談')):
                found.append((txt,href))
        for item in list(dict.fromkeys(found))[:20]: print(item)
    except Exception as e: print(type(e).__name__,e)
