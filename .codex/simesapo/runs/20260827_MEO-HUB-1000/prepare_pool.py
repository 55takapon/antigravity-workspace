import csv,json,re,unicodedata
from pathlib import Path
from urllib.parse import urlsplit
BASE=Path(__file__).parent
OLD=BASE.parent/'20260826_MEO-HUB-5000'
def nk(s):
 s=unicodedata.normalize('NFKC',s or '').lower()
 for t in ('株式会社','有限会社','合同会社','合資会社','一般社団法人','(株)','(有)'):s=s.replace(t,'')
 return re.sub(r'[^\wぁ-んァ-ン一-龥]','',s)
def dk(s):
 try:return (urlsplit(s or '').hostname or '').lower().removeprefix('www.')
 except ValueError:return ''
def pk(s):return re.sub(r'\D','',s or '')
if __name__=='__main__':
 existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8-sig'))
 names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing};phones={pk(r.get('phone')) for r in existing if len(pk(r.get('phone')))>=9}
 pool={};counts={}
 for path in sorted(OLD.glob('*.csv')):
  if any(s in path.name for s in ('exclusion','rejected','filter_test','retained')):continue
  for r in csv.DictReader(path.open(encoding='utf-8-sig',newline='')):
   n,d,p=nk(r.get('company_name')),dk(r.get('url')),pk(r.get('phone'))
   if not n or not d or n in names or d in domains or (len(p)>=9 and p in phones) or r.get('decision')=='drop':continue
   if any(d==x or d.endswith('.'+x) for x in ('web-kanji.com','yuryoweb.com','houjin.goo.to','grip-cloud.jp','facebook.com','instagram.com','google.com','youtube.com')):continue
   r['pool_source_file']=path.name
   if d not in pool or len(r.get('business_description',''))>len(pool[d].get('business_description','')):pool[d]=r
 rows=list(pool.values());rows.sort(key=lambda r:(not bool(r.get('source_url')),r['company_name']))
 fields=sorted({k for r in rows for k in r})
 with (BASE/'raw_pool.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 print(json.dumps({'existing':len(existing),'new_unique_domains':len(rows)},ensure_ascii=False))
