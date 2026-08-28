import csv,json,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\shared')
import sheets_io
old=json.loads((BASE/'aligned.json').read_text(encoding='utf-8'))
pad=lambda r,n:r+['']*max(0,n-len(r))
old=[pad(r,28) for r in old]
old[0][27]='original_list_label'
for r in old[1:]:
    if r[8]=='MEOハブ候補':r[27]=r[8];r[8]=''
checks={r['_row']:r for p in (BASE/'contact_checks').glob('*.json') for r in [json.loads(p.read_text(encoding='utf-8'))]}
assert all(r.get('qa_version')=='contact-purpose-v5' for r in checks.values()),'Purpose review incomplete'
trial=json.loads((BASE/'trial_contact_audit.json').read_text(encoding='utf-8'))['reviews']
for r in trial:
    valid=r['verdict']=='VALID_CONTACT_URL'
    checks[r['row']]={'_row':r['row'],'company_name':r['company_name'],'check':'FORM_PRESENT' if valid else 'SALES_RESTRICTED' if r['verdict']=='SALES_RESTRICTED' else 'PURPOSE_REVIEW','contact_url':r['contact_url'] if valid else '', 'detected_url':r['contact_url'],'checked_at':datetime.now(timezone.utc).isoformat(),'restriction':r.get('reason','')}
assert len(checks)==6192
overrides=json.loads((BASE/'contact_review_overrides.json').read_text(encoding='utf-8'))
for key,o in overrides.items():
    rownum=int(key)
    if rownum in checks:
        checks[rownum].update(check=o['check'],contact_url=o.get('contact_url',''),restriction=o.get('reason',''))
assert set(checks)=={i for i,r in enumerate(old[1:],2) if not r[5]},'Target row set mismatch'
ws=sheets_io.open_worksheet('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ','MEOハブ候補')
live=ws.get_all_values();assert len(live)==len(old)
assert live[0][:24]==old[0][:24],'Header changed'
for i,(a,b) in enumerate(zip(old,live)):
    a,b=pad(a,28),pad(b,28)
    assert all(a[c]==b[c] for c in [*range(24),27] if c!=5),('Unrelated cell changed',i+1)
    if i and a[5]:assert a[5]==b[5],('Existing contact changed',i+1)
expected=[];notes=[['contact_review','contact_checked_at','contact_check_evidence']]
labels={'FORM_PRESENT':'フォーム確認済・営業受入は未確認','SALES_RESTRICTED':'営業等の制限記載あり・要確認','FORM_UNCONFIRMED':'フォーム未確認・要目視','HTTP_ERROR':'ページ取得不可・要再確認','FETCH_ERROR':'通信・証明書等エラー・要再確認','NOT_DETECTED':'002未検出','PURPOSE_REVIEW':'用途・稼働状況の要確認'}
updates=[]
labels['ENTITY_UNCONFIRMED']='会社との対応未確認・要目視'
for rownum,a in enumerate(old[1:],2):
    original=pad(a,24)[5];r=checks.get(rownum)
    value=original if original else r['contact_url']
    actual=pad(live[rownum-1],24)[5]
    if actual!=value:
        assert rownum in checks and not original,('Unexpected new value',rownum,actual,value)
        assert actual in ('',r.get('detected_url',''),r.get('final_url',''),value),('Unknown contact modification',rownum)
        updates.append({'range':f'F{rownum}','values':[[value]]})
    expected.append(value)
    notes.append([labels.get(r['check'],r['check']),r['checked_at'],(r.get('restriction') or r.get('error') or '')+' '+r.get('detected_url','')] if r else ['既存URL・今回未再確認','',''])
if ws.col_count<27:ws.add_cols(27-ws.col_count)
existing_notes=ws.get('Y1:AA7001')
published=json.loads((BASE/'final_sheet.json').read_text(encoding='utf-8')) if (BASE/'final_sheet.json').exists() else None
if any(any(c for c in r) for r in existing_notes):
    assert len(existing_notes)==len(notes),'Unexpected extra-column contents'
    for i,(previous,wanted) in enumerate(zip(existing_notes,notes)):
        previous=pad(previous,3)
        same=previous[0]==wanted[0] and previous[2]==wanted[2]
        if not same:
            assert published and previous==pad(published[i],27)[24:27],('Extra columns changed outside this run',i+1)
            assert pad(live[i],27)[5]==pad(published[i],27)[5],('Contact changed outside this run',i+1)
        elif previous[1]:wanted[1]=previous[1]
updates.append({'range':'Y1:AA7001','values':notes})
ws.batch_update(updates,value_input_option='RAW')
back=ws.get_all_values()
assert [pad(r,27)[5] for r in back[1:]]==expected
assert [pad(r,27)[24:27] for r in back]==notes
for a,b in zip(old,back):
    a,b=pad(a,28),pad(b,28)
    assert all(a[c]==b[c] for c in [*range(24),27] if c!=5)
(BASE/'final_sheet.json').write_text(json.dumps(back,ensure_ascii=False),encoding='utf-8')
counts=Counter(r['check'] for r in checks.values())
report={'total_rows':7000,'previous_contacts':808,'processed_blank_rows':6192,'new_contacts':sum(bool(v) for v in expected)-808,'contacts_total':sum(bool(v) for v in expected),'blank_remaining':sum(not v for v in expected),'checks':dict(counts),'unrelated_values_preserved':True,'list_labels_moved_from_I_to_AB':6728,'manual_send_status_preserved':44,'previous_808_contacts_preserved':True,'readback_exact':True,'outreach_sent':False}
report['limitations']=['フォームと社名表記の機械確認は全件の法人同一性を保証しない','独立目視確認は抜き取りであり全件ではない','営業提案の受入と送信成功は未確認','既存808件の問い合わせ先は今回再検証していない','未確認行は会社自体の除外判定ではない']
(BASE/'completion_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (BASE/'unresolved_contacts.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['row','company_name','url','reason','evidence'])
    for i,v in enumerate(expected,2):
        if not v:writer.writerow([i,old[i-1][0],old[i-1][1],notes[i-1][0],notes[i-1][2]])
print(json.dumps(report,ensure_ascii=False),flush=True)
