import csv
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

RUN=Path(__file__).parent
soup=BeautifulSoup((RUN/'oac_member.html').read_text(encoding='utf-8'),'html.parser')
rows=[]
for kind,cls in [('regular','member-list--regular'),('supporting','member-list--supporting'),('private','member-list--private')]:
    sec=soup.select_one('section.'+cls)
    if not sec: continue
    for card in sec.select(':scope > .member'):
        n=card.select_one('.member__name')
        if not n: continue
        links=[a.get('href','').strip() for a in card.select('a[href]')]
        official=next((u for u in links if urlparse(u).netloc and urlparse(u).netloc not in {'www.oac.or.jp','oac.or.jp'} and not u.startswith(('tel:','mailto:'))),'')
        detail=next((u for u in links if '/member/' in u),'')
        services='｜'.join(x.get_text(' ',strip=True) for x in card.select('.service-item'))
        addr=(card.select_one('.item-address').get_text(' ',strip=True) if card.select_one('.item-address') else '')
        tel=(card.select_one('.item-tel').get_text(' ',strip=True) if card.select_one('.item-tel') else '')
        rows.append({'member_type':kind,'company_name':n.get_text(' ',strip=True),'url':official,'address':addr,'phone':tel,'maps_url':'','oac_detail_url':detail,'oac_services':services})
out=RUN/'oac_members_all.data'
with out.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
from collections import Counter
print({'total':len(rows),'types':dict(Counter(r['member_type'] for r in rows)),'official_url':sum(bool(r['url']) for r in rows)})
