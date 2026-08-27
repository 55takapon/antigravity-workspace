import json,csv,re,hashlib,sys
from pathlib import Path
BASE=Path(__file__).parent;CACHE=BASE.parent/'20260827_MEO-HUB-1000'/'official_cache'
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import dk
pattern=re.compile(r'(?:営業目的|営業を目的|営業活動|営業に関する|営業等|営業メール|営業電話|営業のお電話|営業のご連絡|営業・勧誘|営業や勧誘|セールス|売り込み)[^。.!！]{0,75}(?:お断り|禁止|ご遠慮|お控え)|(?:お断り|禁止|ご遠慮)[^。.!！]{0,45}(?:営業目的|営業を目的|営業活動|営業メール|営業電話|セールス)')
pattern=re.compile(pattern.pattern+r'|営業[^。.!！]{0,85}(?:お断り|禁止|ご遠慮|お控え|送信しない)|(?:営業|勧誘)[^。.!！]{0,55}(?:受け付けておりません|対応いたしません)')
flags=json.loads((BASE/'contact_policy_flags.json').read_text(encoding='utf-8')) if (BASE/'contact_policy_flags.json').exists() else {}
for r in csv.DictReader((BASE/'verification_audit.csv').open(encoding='utf-8-sig')):
 if r.get('review_status')!='EVIDENCE_CHECKED':continue
 for u in dict.fromkeys([r.get('url'),r.get('contact_url')]):
  if not u:continue
  p=CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.json')
  if not p.exists():continue
  page=json.loads(p.read_text(encoding='utf-8'));body=re.sub(r'\s+',' ',page.get('text',''));m=pattern.search(body)
  if m:
   flags[dk(r['url'])]={'company_name':r['company_name'],'reason':'公式ページの営業連絡制限を確認するまで保留：'+m.group(0),'evidence_url':page.get('url',u),'exclusion_scope':'RECHECK'};break
(BASE/'contact_policy_flags.json').write_text(json.dumps(flags,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'contact_policy_flags':len(flags)},ensure_ascii=False))
