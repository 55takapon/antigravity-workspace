import json
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urlunsplit
base=Path(__file__).parent/'groups';before=after=count=0
for path in sorted(base.glob('group_*.json')):
    if int(path.stem.split('_')[1])<48:continue
    raw=path.read_text(encoding='utf-8');before+=len(raw.encode('utf-8'));group=json.loads(raw)
    for page in group['pages']:
        origin=urlsplit(page['base_url'])
        for link in page['links']:
            href=link.get('href','');u=urlsplit(href)
            if u.scheme==origin.scheme and u.netloc==origin.netloc and u.path.startswith('/'):
                relative=urlunsplit(('','',u.path,u.query,u.fragment))
                if urljoin(page['base_url'],relative)==urljoin(page['base_url'],href):link['href']=relative;count+=1
    result=json.dumps(group,ensure_ascii=False,separators=(',',':'));after+=len(result.encode('utf-8'))
    tmp=path.with_suffix('.tmp');tmp.write_text(result,encoding='utf-8');tmp.replace(path)
print(json.dumps({'bytes_before':before,'bytes_after':after,'equivalent_links_compacted':count,'all_resolved_urls_preserved':True}))
