import csv,json,sys,unicodedata,re
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');RUN=Path(__file__).parent;DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist';sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
def pad(r,n=16):return r+['']*(n-len(r))
def dom(u):
 if not u:return ''
 if '://' not in u:u='https://'+u
 h=(urlparse(u).hostname or '').lower().strip('.');return h[4:] if h.startswith('www.') else h
pref=list(csv.DictReader((RUN/'oac_prefiltered.data').open(encoding='utf-8-sig')))
aud=list(csv.DictReader((RUN/'oac_audit_10.data').open(encoding='utf-8-sig')))
for r in aud:
 if r['company_name']=='株式会社第一製版':r.update(classification='送付対象',contact_url='https://www.di-seihan.co.jp/contact.html',contact_check='real_form_confirmed_manual',audit_reason='OAC広告制作法人会員・新聞雑誌広告制作・SPツール・印刷受託')
send=[r for r in aud if r['classification']=='送付対象'];audit_ex=[r for r in aud if r['classification']=='除外']
pre_ex=[r for r in pref if r['prefilter']=='exclude' and '既存または除外リスト一致' not in r['prefilter_reason']]
existing=[r for r in pref if '既存または除外リスト一致' in r['prefilter_reason']]
if (len(pref),len(existing),len(send),len(pre_ex)+len(audit_ex))!=(106,71,2,33):raise SystemExit('STOP reconciliation')
sh=get_client(str(DIST/'shared/gcp_service_account.json')).open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ');ws=sh.worksheet('シート2');exws=sh.worksheet('除外リスト');pws=sh.worksheet('収集進捗管理')
sv=[pad(r) for r in ws.get('A1:P',value_render_option='FORMULA')];ev=[pad(r) for r in exws.get('A1:P',value_render_option='FORMULA')]
first=next(i for i,r in enumerate(sv[1:],2) if r[14].startswith('除外'))
if not all(r[14].startswith('除外') for r in sv[first-1:]):raise SystemExit('STOP Sheet2 exclusion block')
live_domains={dom(r[1]) for r in sv[1:]+ev[1:] if dom(r[1])}
dups=[r['company_name'] for r in send if dom(r['url']) in live_domains]
if dups:raise SystemExit('STOP duplicates '+json.dumps(dups,ensure_ascii=False))
with (RUN/'sheet2_before.data').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(sv)
with (RUN/'exclusion_before.data').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(ev)
def srow(r):
 x=['']*16;x[0]=r['company_name'];x[1]=r['url'];x[2]=r.get('address','');x[3]=r.get('phone','');x[5]=r['contact_url'];x[12]='広告制作・クリエイティブ';x[14]='送付対象｜E｜OAC広告制作会社';x[15]=f"【採用根拠】{r['audit_reason']}｜【窓口】実在フォーム確認済み：{r['contact_url']}｜【根拠URL】{r['url']}｜【監査日】2026-08-12";return x
def erow(name,url,reason,contact='',check='事前機械判定'):
 x=['']*16;x[0]=name;x[1]=url;x[5]=contact;x[8]='skip監査除外';x[9]=reason;x[12]='OAC本監査';x[14]='除外｜OAC本監査';x[15]=f'【除外根拠】{reason}｜【窓口確認】{check}｜【根拠URL】{url}｜【監査日】2026-08-12';return x
ws.insert_rows([srow(r) for r in send],row=first,value_input_option='RAW')
ers=[erow(r['company_name'],r['url'],r['prefilter_reason']) for r in pre_ex]+[erow(r['company_name'],r['url'],r['audit_reason'],r['contact_url'],r['contact_check']) for r in audit_ex]
exws.append_rows(ers,value_input_option='RAW',table_range=f'A{len(ev)+1}:P')
pws.update(range_name='A85:F85',values=[['2','NEXT-E-OAC-001','日本広告制作協会（OAC）','公式106件／既存71／本監査・機械除外35','送付対象2社・新規除外33社を確定','シート2・除外リスト反映済み']],value_input_option='RAW')
pws.update(range_name='A89:F89',values=[['進捗','再計算完了','純増858社','8.58%','有効基準9,099社','残り9,142社']],value_input_option='RAW')
sv2=[pad(r) for r in ws.get('A1:P',value_render_option='FORMULA')];ev2=[pad(r) for r in exws.get('A1:P',value_render_option='FORMULA')];first2=next(i for i,r in enumerate(sv2[1:],2) if r[14].startswith('除外'))
rep={'source_total':106,'existing':71,'send_written':2,'exclude_written':33,'reconciled':106==71+2+33,'sheet2_before':len(sv),'sheet2_after':len(sv2),'exclusion_before':len(ev),'exclusion_after':len(ev2),'first_exclusion_row':first2,'exclusions_contiguous_bottom':all(r[14].startswith('除外') for r in sv2[first2-1:]),'sheet2_send_count':sum(r[14].startswith('送付対象') for r in sv2[1:]),'duplicate_domains_sheet2':len([dom(r[1]) for r in sv2[1:] if dom(r[1])])-len(set(dom(r[1]) for r in sv2[1:] if dom(r[1]))),'progress':pws.get('A85:F85')+pws.get('A89:F89')}
if not(rep['sheet2_after']==len(sv)+2 and rep['exclusion_after']==len(ev)+33 and rep['first_exclusion_row']==first+2 and rep['exclusions_contiguous_bottom'] and rep['sheet2_send_count']==858 and rep['duplicate_domains_sheet2']==0):raise SystemExit('STOP verification '+json.dumps(rep,ensure_ascii=False))
(RUN/'publish_verification.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rep,ensure_ascii=False,indent=2))
