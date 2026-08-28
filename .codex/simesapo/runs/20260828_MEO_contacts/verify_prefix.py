import json,sys
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\shared')
import sheets_io
ws=sheets_io.open_worksheet('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ','MEOハブ候補')
before=ws.get_all_values();pad=lambda r:r+['']*max(0,28-len(r))
batch={r['idx']:r for r in json.loads((BASE/'full_batch.json').read_text(encoding='utf-8'))}
results=json.loads((BASE/'top_prefix_results.json').read_text(encoding='utf-8'))['results']
updates=[]
for row,url in [(4,'https://hamon-z.com/contact/'),(6,'https://www.gamu-shara.com/contact-8')]:
    current=pad(before[row-1])[5]
    assert current in ('',url)
    if current:updates.append({'range':f'F{row}','values':[['']]})
for r in results:
    row=batch[r['idx']]['_row'];actual=pad(before[row-1])[5]
    if not r['contact_url'] and actual:
        check=json.loads((BASE/'contact_checks'/f'{row}.json').read_text(encoding='utf-8'))
        assert actual in (check['detected_url'],check.get('final_url')),('Unknown contact value',row)
        updates.append({'range':f'F{row}','values':[['']]})
if updates:ws.batch_update(updates,value_input_option='RAW')
back=ws.get_all_values();original=json.loads((BASE/'aligned.json').read_text(encoding='utf-8'))
assert len(back)==len(original)==7001
for a,b in zip(original[1:],back[1:]):
    a,b=pad(a),pad(b)
    for c in range(24):
        if c in (5,8):continue
        assert a[c]==b[c]
    assert b[8]==('' if a[8]=='MEOハブ候補' else a[8])
    if a[5]:assert a[5]==b[5]
for r in results:assert pad(back[batch[r['idx']]['_row']-1])[5]==r['contact_url']
report={'last_checked_row':max(batch[r['idx']]['_row'] for r in results),'prefix_results':len(results),'prefix_found':sum(bool(r['contact_url']) for r in results),'current_contacts':sum(bool(pad(r)[5]) for r in back[1:]),'previous_808_preserved':True,'I_list_labels':sum(pad(r)[8]=='MEOハブ候補' for r in back[1:]),'I_manual':sum(pad(r)[8]=='手動送信要' for r in back[1:]),'readback_exact':True}
(BASE/'prefix_readback.json').write_text(json.dumps(report,ensure_ascii=False),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
