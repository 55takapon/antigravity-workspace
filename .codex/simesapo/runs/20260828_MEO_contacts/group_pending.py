import json
from pathlib import Path
base=Path(__file__).parent;chunks=base/'chunks';out=base/'groups';out.mkdir(exist_ok=True)
groups=[];pages=[];sources=[];size=0
for p in sorted(chunks.glob('pages_*.json')):
    if (chunks/p.name.replace('pages_','results_')).exists():continue
    part=json.loads(p.read_text(encoding='utf-8'))
    if pages and (size+p.stat().st_size>600000 or len(pages)+len(part)>100):
        groups.append({'sources':sources,'pages':pages});pages=[];sources=[];size=0
    pages+=part;sources.append({'name':p.name.replace('pages_','results_'),'indices':[r['idx'] for r in part]});size+=p.stat().st_size
if pages:groups.append({'sources':sources,'pages':pages})
for i,g in enumerate(groups):(out/f'group_{i:04}.json').write_text(json.dumps(g,ensure_ascii=False),encoding='utf-8')
(base/'group_manifest.json').write_text(json.dumps({'groups':len(groups),'pages':sum(len(g['pages']) for g in groups)}),encoding='utf-8')
print(json.dumps({'groups':len(groups),'pages':sum(len(g['pages']) for g in groups)}))
