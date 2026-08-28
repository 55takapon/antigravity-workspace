import json,re,sys
from collections import Counter
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\shared')
import sheets_io
ws=sheets_io.open_worksheet('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ','MEOハブ候補')
before=ws.get_all_values()
assert before[0][8:10]==['status','error_reason']
pad=lambda r:r+['']*max(0,28-len(r))
targets=[(i,pad(r)) for i,r in enumerate(before[1:],2) if len(r)>8 and r[8]=='手動送信要']
assert len(targets)==44,('Target set changed',len(targets))
updates=[];records=[]
for row,r in targets:
    assert not r[9],('Existing reason must be preserved',row)
    phone=bool(re.fullmatch(r'[+\d()（）\-\s]{9,22}',r[3]))
    email=bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',r[22]))
    if not r[5]:
        kind='FORM_UNAVAILABLE'
        reason='フォーム送信不可：contact_urlが空欄。'+r[24]+'。'
        if row==6528:reason+='過去の公式確認記録に問い合わせフォーム削除の告知あり。'
        channels=('電話・メール' if phone and email else '電話' if phone else 'メール' if email else '')
        reason+=('台帳上の連絡先は'+channels+'のみ。別手段の営業連絡可否は未確認。' if channels else '台帳上に有効な電話・メールもなく、連絡先の確認が必要。')
        reason+='「手動ならフォーム送信できる」という判定ではありません。'
    elif r[24]=='フォーム確認済・営業受入は未確認':
        kind='FORM_CHECKED_MANUAL_CAUSE_UNKNOWN'
        reason='フォームは確認済み。ただし元の「手動送信要」判定には理由記録がなく、手動操作が必須かは未確認。営業提案の受付条件・自動入力可否を確認してから送信判断。'
    else:
        kind='URL_ONLY_MANUAL_CAUSE_UNKNOWN'
        reason='contact_urlは登録済みだが、フォーム実在・稼働・営業受付条件・自動入力可否は未確認。元の「手動送信要」判定に理由記録がないため、手動送信可能とは判断できません。先に窓口確認が必要。'
    if r[3] and not phone:reason+='D列の値は電話番号として確認できないため、電話連絡先にも使わないでください。'
    reason+='【2026-08-28 台帳・既存確認記録の照合／送信試行なし】'
    updates.append({'range':f'J{row}','values':[[reason]]})
    records.append({'row':row,'company_name':r[0],'category':kind,'reason':reason,'contact_url':r[5],'phone_recorded':phone,'email_recorded':email})
(BASE/'manual_reason_before.json').write_text(json.dumps(before,ensure_ascii=False),encoding='utf-8')
(BASE/'manual_reason_expected.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
if '--write' not in sys.argv:
    print(json.dumps({'targets':len(records),'categories':dict(Counter(r['category'] for r in records))}));sys.exit()
ws.batch_update(updates,value_input_option='RAW')
after=ws.get_all_values()
expected=[pad(r[:]) for r in before]
for r in records:expected[r['row']-1][9]=r['reason']
assert [pad(r) for r in after]==expected,'Readback mismatch'
(BASE/'manual_reason_after.json').write_text(json.dumps(after,ensure_ascii=False),encoding='utf-8')
report={'changed_cells':len(updates),'categories':dict(Counter(r['category'] for r in records)),'only_J_changed':True,'all_other_values_preserved':True,'outreach_sent':False,'readback_exact':True}
(BASE/'manual_reason_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
