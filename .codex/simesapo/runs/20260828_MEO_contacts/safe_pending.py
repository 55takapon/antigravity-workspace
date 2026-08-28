import json,re
from urllib.parse import urlsplit,urljoin
from pathlib import Path
BASE=Path(__file__).parent
out=BASE/'generic_contact_groups';out.mkdir(exist_ok=True)
# Never export meeting invitations or authentication-bearing links.
sensitive=re.compile(r'zoom\.(?:us|com)|teams\.microsoft|meet\.google|(?:pwd|password|passwd|token|secret|signature|authorization|access_key|api_key|credential|sessionid|auth)=',re.I)
groups=[];pages=[];sources=[];removed=0;size=0;held=[]
overrides=json.loads((BASE/'contact_review_overrides.json').read_text(encoding='utf-8'))
rowmap={r['idx']:r['_row'] for r in json.loads((BASE/'full_batch.json').read_text(encoding='utf-8'))}
for p in sorted((BASE/'chunks').glob('pages_*.json')):
    name=p.name.replace('pages_','results_')
    if (BASE/'chunks'/name).exists():continue
    part=json.loads(p.read_text(encoding='utf-8'))
    safe=[]
    for r in part:
        base=urlsplit(r['base_url'])
        if base.query or base.username or base.password or sensitive.search(r['base_url']) or base.hostname in ('www.dropbox.com','dropbox.com'):
            held.append({'idx':r['idx'],'method':'none','contact_url':''})
            overrides[str(rowmap[r['idx']])]={'check':'PURPOSE_REVIEW','contact_url':'','reason':'元URLに追加パラメータや共有先等があるため外部処理へ渡さず保留。公式窓口を要確認。'}
            continue
        kept=[];seen=set()
        for link in r.get('links',[]):
            if sensitive.search(json.dumps(link,ensure_ascii=False)):continue
            label=' '.join(str(link.get(k,'')) for k in ('href','text','alt_title'))
            if re.search(r'従業員|社員専用|ログイン|配信|管理|会員|メルマガ|登録|bcp|unsubscribe|subscribe|account|admin|portal|member|mailnews|newsletter|register',label,re.I):continue
            if not re.search(r'contact|inquiry|inquiries|toiawase|otoiawase|お問い合わせ|お問合せ|問い合わせ|問合せ',label,re.I):continue
            href=link.get('href','');u=urlsplit(urljoin(r['base_url'],href))
            if u.scheme not in ('http','https') or u.netloc!=base.netloc or u.query or u.username or u.password:continue
            if re.search(r'auth|login|signin|session|token|password|secret|meeting|reset',u.path,re.I):continue
            href=u.path or '/'
            if not re.search(r'/(?:contact|contact-us|contactus|inquiry|inquiries|toiawase|otoiawase)(?:\.(?:html?|php|aspx))?/?$',href,re.I):continue
            item={'href':href}
            key=json.dumps(item,sort_keys=True)
            if key not in seen:kept.append(item);seen.add(key)
        removed+=len(r.get('links',[]))-len(kept);r['links']=kept
        safe.append(r)
    partsize=len(json.dumps(safe,ensure_ascii=False).encode('utf-8'))
    if pages and (len(pages)+len(part)>60 or size+partsize>150000):
        groups.append({'pages':pages,'sources':sources});pages=[];sources=[];size=0
    pages+=safe;sources.append({'name':name,'indices':[r['idx'] for r in part]})
    size+=partsize
if pages:groups.append({'pages':pages,'sources':sources})
for i,g in enumerate(groups):
    ids={idx for s in g['sources'] for idx in s['indices']}
    g['held_results']=[r for r in held if r['idx'] in ids]
    data=json.dumps(g,ensure_ascii=False)
    assert not sensitive.search(data),'Sensitive content withheld'
    (out/f'group_{i:04}.json').write_text(data,encoding='utf-8')
report={'groups':len(groups),'pages':sum(len(g['pages']) for g in groups),'sensitive_links_removed':removed}
(BASE/'generic_contact_group_manifest.json').write_text(json.dumps(report),encoding='utf-8')
(BASE/'contact_review_overrides.json').write_text(json.dumps(overrides,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report))
