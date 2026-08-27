import csv,json,sys
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import nk,dk,pk
done=set()
for p in BASE.glob('*_core_*.json'):
 d=json.loads(p.read_text(encoding='utf-8'))
 for r in d.get('kept',[])+d.get('dropped',[]):done.add(dk(r.get('url')))
e=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'))
names={nk(r.get('company_name')) for r in e};domains={dk(r.get('url')) for r in e};phones={pk(r.get('phone')) for r in e if len(pk(r.get('phone')))>=9}
out=[]
for filename in ['kimete_raw.csv','detail_raw.csv','regional_raw.csv','advertising_raw.csv','association_raw.csv']:
 p=BASE/filename
 if not p.exists():continue
 for r in csv.DictReader(p.open(encoding='utf-8-sig')):
  n,d,t=nk(r.get('company_name')),dk(r.get('url')),pk(r.get('phone'))
  if not n or not d or d in done or d in domains or n in names or (len(t)>=9 and t in phones):continue
  out.append({k:r.get(k,'') for k in ['company_name','url','phone','address']});done.add(d)
  if len(out)>=100:break
 if len(out)>=100:break
print(json.dumps(out,ensure_ascii=False))
