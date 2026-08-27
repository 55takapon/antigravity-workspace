import sys,json,csv,argparse,re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
import official_engine as v
from prepare_pool import dk,nk,pk
def atomic_write(path,rows):
 fields=sorted({k for r in rows for k in r});temp=path.with_suffix(path.suffix+'.tmp')
 with temp.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 temp.replace(path)
v.write=atomic_write
if not hasattr(v,'BASE_SERVICE_PATTERN'):v.BASE_SERVICE_PATTERN=v.SERVICE.pattern
v.SERVICE=re.compile(v.BASE_SERVICE_PATTERN)
v.SERVICE=re.compile(v.SERVICE.pattern+r'|(?:販売促進|販促|店舗集客|ブランディング)[のを・/／企画提案制作\s]{0,8}(?:支援|サポート|コンサルティング)|(?:総合広告代理店|広告代理業|広告代理店事業)|(?:広告|販促)(?:の)?(?:企画・制作|企画制作|企画から制作)|(?:販促|販売促進)(?:用)?(?:物|ツール|グッズ)[のを・企画提案制作製造販売\s]{0,10}(?:制作|製造|販売|提案)|(?:チラシ|ポスター|のぼり旗|看板)(?:の)?(?:印刷|製作|制作|デザイン)')
v.SERVICE=re.compile(v.SERVICE.pattern+r'|広告代理店|広告運用|(?:セールスプロモーション|店舗デザイン)|(?:広告|販促|販売促進|ノベルティ|店舗)[物品の・/／企画デザイン印刷製作制作支援提案など、及び\s]{0,18}(?:企画|提案|支援|デザイン|制作)|(?:看板|サイン)[の・/／企画デザイン設計製作制作施工\s]{0,12}(?:製作|制作|デザイン)|(?:ホームページ|[Ww][Ee][Bb](?:サイト)?)[の・/／企画\s]{0,8}デザイン')

def examine(r):
 status=r.get('status','')
 result=v.examine(r)
 if status=='手動送信要':result['status']=status
 result['verification_version']='20260827-service-pages-v4'
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--recheck-weak',action='store_true');args=ap.parse_args()
 existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'))
 names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing}
 raw={}
 for p in BASE.glob('*_raw.csv'):
  for r in csv.DictReader(p.open(encoding='utf-8-sig')):raw.setdefault(dk(r['url']),r)
 rows={}
 for p in BASE.glob('*_core_*.json'):
  d=json.loads(p.read_text(encoding='utf-8'))
  for r in d['kept']:
   domain=dk(r['url'])
   if domain in domains or nk(r['company_name']) in names:continue
   rows[domain]={**raw.get(domain,{}),**r}
 path=BASE/'verification_audit.csv'
 out=list(csv.DictReader(path.open(encoding='utf-8-sig'))) if path.exists() else []
 reconsider={dk(r['url']) for r in out if args.recheck_weak and r.get('review_status')!='EVIDENCE_CHECKED' and r.get('verification_version')!='20260827-service-pages-v4' and any(x in r.get('reject_reason','') for x in ['問い合わせ先','根拠なし'])}
 done={dk(r['url']) for r in out}-reconsider;todo=[r for d,r in rows.items() if d not in done]
 out=[r for r in out if dk(r['url']) not in reconsider]
 print('todo',len(todo),'previous',len(out),flush=True)
 with ThreadPoolExecutor(max_workers=10) as pool:
  for i,f in enumerate(as_completed([pool.submit(examine,r) for r in todo]),1):
   out.append(f.result())
   if i%20==0:
    v.write(path,out);print('examined',i,'checked',sum(r.get('review_status')=='EVIDENCE_CHECKED' for r in out),flush=True)
 v.write(path,out)
 v.write(BASE/'verified_candidates.csv',[r for r in out if r.get('review_status')=='EVIDENCE_CHECKED'])
 print('done',len(out),'checked',sum(r.get('review_status')=='EVIDENCE_CHECKED' for r in out),flush=True)
