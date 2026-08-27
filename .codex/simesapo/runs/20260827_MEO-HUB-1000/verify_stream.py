import csv,json,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from verify_official import BASE,examine,write
from prepare_pool import nk,dk,pk
existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8-sig'))
names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing};phones={pk(r.get('phone')) for r in existing if len(pk(r.get('phone')))>=9}
seen=set();out=[];start=time.monotonic()
def read(name):
 p=BASE/name
 if not p.exists():return []
 try:return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
 except (UnicodeDecodeError,csv.Error):return []
while time.monotonic()-start<7200:
 todo=[]
 for filename in ('new_discovered.csv','yuryoweb_discovered.csv'):
  for r in read(filename):
   n,d,p=nk(r.get('company_name')),dk(r.get('url')),pk(r.get('phone'))
   if not n or not d or d in seen or n in names or d in domains or (len(p)>=9 and p in phones):continue
   seen.add(d);todo.append(r)
 if todo:
  with ThreadPoolExecutor(max_workers=8) as pool:
   for f in as_completed([pool.submit(examine,r) for r in todo]):
    out.append(f.result())
    if len(out)%50==0:write(BASE/'stream_audit.csv',out)
  write(BASE/'stream_audit.csv',out);write(BASE/'stream_checked.csv',[r for r in out if r['review_status']=='EVIDENCE_CHECKED'])
  print(json.dumps({'examined':len(out),'evidence_checked':sum(r['review_status']=='EVIDENCE_CHECKED' for r in out)}),flush=True)
 expected_path=BASE/'yuryoweb_expected.json'
 expected=json.loads(expected_path.read_text(encoding='utf-8'))['scheduled'] if expected_path.exists() else 3000
 if len(read('discovery_audit.csv'))>=1943 and len(read('yuryoweb_discovery_audit.csv'))>=expected:
  print(json.dumps({'done':True,'examined':len(out),'evidence_checked':sum(r['review_status']=='EVIDENCE_CHECKED' for r in out)}),flush=True);break
 time.sleep(20)
else:print('STOP: discovery completion not observed within bounded run',flush=True)
