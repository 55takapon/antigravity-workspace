import json
from pathlib import Path
base=Path(__file__).parent/'groups'
before=after=0
for p in sorted(base.glob('group_*.json')):
    if int(p.stem.split('_')[1])<20:continue
    raw=p.read_text(encoding='utf-8');before+=len(raw.encode('utf-8'));group=json.loads(raw)
    for page in group['pages']:
        seen=set();links=[]
        for link in page['links']:
            key=tuple(link.get(k,'') for k in ('href','text','alt_title'))
            if key in seen:continue
            seen.add(key);links.append({k:v for k,v in link.items() if v})
        page['links']=links
    result=json.dumps(group,ensure_ascii=False,separators=(',',':'));after+=len(result.encode('utf-8'))
    tmp=p.with_suffix('.tmp');tmp.write_text(result,encoding='utf-8');tmp.replace(p)
print(json.dumps({'bytes_before':before,'bytes_after':after,'unchanged_company_indices':True,'removed_only_exact_duplicate_links_and_empty_optional_fields':True}))
