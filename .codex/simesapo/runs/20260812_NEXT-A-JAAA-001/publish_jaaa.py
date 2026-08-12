import csv,json,sys
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');RUN=Path(__file__).parent;DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist'
sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
def pad(r,n=16):return r+['']*(n-len(r))
def dom(u):
 if not u:return ''
 if '://' not in u:u='https://'+u
 h=(urlparse(u).hostname or '').lower().strip('.');return h[4:] if h.startswith('www.') else h

pref=list(csv.DictReader((RUN/'jaaa_prefiltered.data').open(encoding='utf-8-sig')))
aud=list(csv.DictReader((RUN/'jaaa_audit_21.data').open(encoding='utf-8-sig')))
manual={
'コモンズ株式会社':('https://business.form-mailer.jp/lp/7a17062f180402','JAAA登録広告会社・Web・SNS・デジタル広告関連会社向け提案専用フォームあり'),
'株式会社 春光社':('https://shunkosha.co.jp/contact','JAAA登録交通広告会社・広告代理店向け商談窓口あり')}
for r in aud:
 if r['company_name'] in manual:
  u,reason=manual[r['company_name']];r.update(classification='送付対象',contact_url=u,contact_check='real_form_confirmed_manual',audit_reason=reason)
 if r['company_name']=='株式会社 大手広告通信社':r.update(classification='除外',contact_check='canonical_filter_no_contact',audit_reason='001正規フィルターで問い合わせ窓口不成立')
 if r['company_name']=='株式会社 アクアスター':r.update(classification='除外',audit_reason='従業員194名・全国4拠点の明確な大手制作会社')
send=[r for r in aud if r['classification']=='送付対象']; audit_ex=[r for r in aud if r['classification']=='除外']
pre_ex=[r for r in pref if r['prefilter']=='exclude' and '既存または除外リスト一致' not in r['prefilter_reason']]
existing=[r for r in pref if '既存または除外リスト一致' in r['prefilter_reason']]
if (len(pref),len(existing),len(pre_ex),len(send),len(audit_ex))!=(136,104,11,5,16):raise SystemExit('STOP reconciliation')

sh=get_client(str(DIST/'shared/gcp_service_account.json')).open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ');ws=sh.worksheet('シート2');exws=sh.worksheet('除外リスト');pws=sh.worksheet('収集進捗管理')
sv=[pad(r) for r in ws.get('A1:P',value_render_option='FORMULA')];ev=[pad(r) for r in exws.get('A1:P',value_render_option='FORMULA')]
first=next(i for i,r in enumerate(sv[1:],2) if r[14].startswith('除外'))
if not all(r[14].startswith('除外') for r in sv[first-1:]):raise SystemExit('STOP Sheet2 exclusion block')
live={dom(r[1]) for r in sv[1:]+ev[1:] if dom(r[1])};dups=[r['company_name'] for r in send if dom(r['url']) in live]
if dups:raise SystemExit('STOP duplicates '+json.dumps(dups,ensure_ascii=False))
with (RUN/'sheet2_before.data').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(sv)
with (RUN/'exclusion_before.data').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(ev)
def srow(r):
 x=['']*16;x[0]=r['company_name'];x[1]=r['url'];x[5]=r['contact_url'];x[12]='広告代理・PR';x[14]='送付対象｜A｜JAAA広告会社';x[15]=f"【採用根拠】{r['audit_reason']}｜【窓口】実在フォーム確認済み：{r['contact_url']}｜【根拠URL】{r['url']}｜【監査日】2026-08-12";return x
def erow(name,url,reason,contact='',check='事前機械判定'):
 x=['']*16;x[0]=name;x[1]=url;x[5]=contact;x[8]='skip監査除外';x[9]=reason;x[12]='JAAA本監査';x[14]='除外｜JAAA本監査';x[15]=f'【除外根拠】{reason}｜【窓口確認】{check}｜【根拠URL】{url}｜【監査日】2026-08-12';return x
ws.insert_rows([srow(r) for r in send],row=first,value_input_option='RAW')
ers=[erow(r['company_name'],r['url'],r['prefilter_reason']) for r in pre_ex]+[erow(r['company_name'],r['url'],r['audit_reason'],r['contact_url'],r['contact_check']) for r in audit_ex]
exws.append_rows(ers,value_input_option='RAW',table_range=f'A{len(ev)+1}:P')
pws.update(range_name='A87:F87',values=[['4','NEXT-A-JAAA-001','日本広告業協会（JAAA）会員社一覧','公式公開136件／既存104／本監査・機械除外32','送付対象5社・新規除外27社を確定','シート2・除外リスト反映済み']],value_input_option='RAW')
pws.update(range_name='A89:F89',values=[['進捗','再計算完了','純増869社','8.69%','有効基準9,110社','残り9,131社']],value_input_option='RAW')
sv2=[pad(r) for r in ws.get('A1:P',value_render_option='FORMULA')];ev2=[pad(r) for r in exws.get('A1:P',value_render_option='FORMULA')];first2=next(i for i,r in enumerate(sv2[1:],2) if r[14].startswith('除外'));domains=[dom(r[1]) for r in sv2[1:] if dom(r[1])]
rep={'source_total':136,'official_overview_count':137,'existing':104,'send_written':5,'exclude_written':27,'reconciled':136==104+5+27,'sheet2_before':len(sv),'sheet2_after':len(sv2),'exclusion_before':len(ev),'exclusion_after':len(ev2),'first_exclusion_row':first2,'exclusions_contiguous_bottom':all(r[14].startswith('除外') for r in sv2[first2-1:]),'sheet2_send_count':sum(r[14].startswith('送付対象') for r in sv2[1:]),'duplicate_domains_sheet2':len(domains)-len(set(domains)),'progress':pws.get('A87:F87')+pws.get('A89:F89')}
if not(rep['sheet2_after']==len(sv)+5 and rep['exclusion_after']==len(ev)+27 and rep['first_exclusion_row']==first+5 and rep['exclusions_contiguous_bottom'] and rep['sheet2_send_count']==869 and rep['duplicate_domains_sheet2']==0):raise SystemExit('STOP verification '+json.dumps(rep,ensure_ascii=False))
(RUN/'publish_verification.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rep,ensure_ascii=False,indent=2))
