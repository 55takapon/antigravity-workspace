import json
from pathlib import Path
base=Path(__file__).parent
pages=json.loads((base/'full_batch.json').read_text(encoding='utf-8'))
out=base/'chunks';out.mkdir(exist_ok=True)
chunks=[];batch=[];size=2
for page in pages:
    data={k:page[k] for k in ['idx','base_url','links'] if k in page}
    length=len(json.dumps(data,ensure_ascii=False).encode('utf-8'))
    if batch and (size+length>60000 or len(batch)>=40):chunks.append(batch);batch=[];size=2
    batch.append(data);size+=length+1
if batch:chunks.append(batch)
for i,b in enumerate(chunks):
    (out/f'pages_{i:04}.json').write_text(json.dumps(b,ensure_ascii=False),encoding='utf-8')
(base/'chunk_manifest.json').write_text(json.dumps({'pages':len(pages),'chunks':len(chunks),'sizes':[len(b) for b in chunks]}),encoding='utf-8')
print(json.dumps({'pages':len(pages),'chunks':len(chunks),'max_chunk_bytes':max(p.stat().st_size for p in out.glob('pages_*.json'))}))
