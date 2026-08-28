import json,re,unicodedata
from pathlib import Path
from urllib.parse import urlsplit
BASE=Path(__file__).parent
overrides=json.loads((BASE/'contact_review_overrides.json').read_text(encoding='utf-8'))
if 'overrides' in overrides:overrides=overrides['overrides']
if isinstance(overrides,list):overrides={str(r.get('_row',r.get('row'))):r for r in overrides}
updated=0;checks=[]
def normalize(s):
    return re.sub(r'[\W_]+','',unicodedata.normalize('NFKC',s).casefold())
def identity_unconfirmed(r):
    name=re.sub(r'\([^)]*\)','',unicodedata.normalize('NFKC',r['company_name']))
    legal=('株式会社','有限会社','合同会社','合資会社','合名会社')
    core=name
    for term in legal:core=core.replace(term,'')
    core=normalize(core);body=normalize(r.get('text','')+' '+r.get('title',''))
    if len(core)<3 or core not in body:return True
    expected=next((term for term in legal if term in name),None)
    if expected and normalize(expected+core) not in body and normalize(core+expected) not in body:
        if any(normalize(term+core) in body or normalize(core+term) in body for term in legal if term!=expected):return True
    return False
for path in (BASE/'contact_checks').glob('*.json'):
    try:r=json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:continue
    previous=r.copy();t=r.get('text','')
    if r['check']=='FORM_PRESENT':
        r['contact_url']=r.get('final_url') or r['contact_url']
        host=lambda u:(urlsplit(u).hostname or '').lower().removeprefix('www.')
        changed_company_host=host(r.get('detected_url',''))==host(r.get('official_url','')) and host(r['contact_url'])!=host(r.get('official_url',''))
        fault=re.search(r'フォーム[^。]{0,60}(?:機能しません|故障|現在停止|閉鎖|廃止)|対象業種以外[^。]{0,100}|業者様[^。]{0,80}業者様用',t)
        if re.search(r'営業専用|営業[^。\n]{0,40}別[^。\n]{0,20}フォーム',t):r.update(check='PURPOSE_REVIEW',contact_url='',restriction='営業用の専用・別フォームに関する記載があり、現在の窓口でよいか要確認。')
        elif re.search(r'lorem\s+ipsum',t,re.I):r.update(check='FORM_UNCONFIRMED',contact_url='',restriction='本文に未完成テンプレートの可能性がある文章が残り、実用窓口として要確認。')
        elif changed_company_host:r.update(check='PURPOSE_REVIEW',contact_url='',restriction='会社サイトから別ホストへ転送されているため、会社一致の要確認：'+r.get('final_url',''))
        elif fault:r.update(check='PURPOSE_REVIEW',contact_url='',restriction='用途・稼働状況の要確認：'+fault.group(0))
        elif not r.get('textarea'):r.update(check='FORM_UNCONFIRMED',contact_url='',restriction='自由記入欄を確認できず、配信登録等と区別するため要目視。')
        elif re.search('資料請求|採用|求人|予約|注文|ログイン|メルマガ',r.get('title','')):r.update(check='PURPOSE_REVIEW',contact_url='',restriction='ページの用途を要確認：'+r['title'])
        # Row 1644 was independently decoded as EUC-JP and identity verified in contact_sample_3000_audit.json.
        elif r['_row']!=1644 and identity_unconfirmed(r):r.update(check='ENTITY_UNCONFIRMED',contact_url='',restriction='取得したフォーム本文で登録会社名との対応を確認できないため保留。表記違い・文字化け・改称の可能性を含み、別会社とは断定しない。')
    o=overrides.get(str(r['_row']))
    if o:
        r.update(check=o['check'],contact_url=o.get('contact_url',''),restriction=o.get('reason',''))
        if o.get('evidence_url'):r['review_evidence_url']=o['evidence_url']
    r['qa_version']='contact-purpose-v5'
    if r!=previous:
        r.setdefault('prior_check',previous['check']);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(r,ensure_ascii=False),encoding='utf-8');tmp.replace(path);updated+=1
    checks.append(r)
full=json.loads((BASE/'full_batch.json').read_text(encoding='utf-8'))
if {r['_row'] for r in checks}=={r['_row'] for r in full}:
    results=[{'idx':r['idx'],'method':'link' if r['contact_url'] else 'none','contact_url':r['contact_url']} for r in checks]
    (BASE/'checked_results.json').write_text(json.dumps({'results':results},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'reviewed_cache':len(checks),'refined':updated,'expected':len(full)}))
