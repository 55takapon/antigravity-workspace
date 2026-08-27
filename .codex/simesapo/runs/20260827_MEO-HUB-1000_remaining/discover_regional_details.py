import json,csv,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from discover_details import BASE,detail,dk
existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'));domains={dk(r.get('url')) for r in existing}
done=set();out={}
for cycle in range(200):
 if (BASE/'stop_collection.flag').exists():break
 p=BASE/'regional_pending.json'
 rows=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
 todo=[r for r in rows if r['source_url'] not in done]
 if not todo:
  if (BASE/'regional_lists_complete.flag').exists():break
  time.sleep(20);continue
 with ThreadPoolExecutor(max_workers=6) as pool:
  for i,f in enumerate(as_completed([pool.submit(detail,r) for r in todo]),1):
   r=f.result();done.add(r['source_url']);d=dk(r.get('url'))
   if d and d not in domains:out.setdefault(d,r)
   if i%25==0 or i==len(todo):
    p=BASE/'regional_raw.tmp';fields=sorted({k for r in out.values() for k in r})
    with p.open('w',encoding='utf-8-sig',newline='') as h:
     w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(out.values())
    p.replace(BASE/'regional_raw.csv');print('details',len(done),'new_raw',len(out),flush=True)
print('done',len(out),flush=True)
