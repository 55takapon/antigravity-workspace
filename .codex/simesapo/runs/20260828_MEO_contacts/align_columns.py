import sys,json
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\shared')
import sheets_io
old=json.loads((BASE/'MEOハブ候補_before.json').read_text(encoding='utf-8'))
ref=json.loads((BASE/'SNS運用_before.json').read_text(encoding='utf-8'))
headers=ref['values'][0][:16]
extra=[h for h in old['values'][0] if h and h not in headers]
newheaders=headers+extra
matrix=[newheaders]
for row in old['values'][1:]:
    data=dict(zip(old['values'][0],row))
    matrix.append([data.get(h,'') if h else '' for h in newheaders])
ws=sheets_io.open_worksheet('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ','MEOハブ候補')
assert ws.get_all_values()==old['values'],'Live data changed'
assert not any(str(c).startswith('=') for r in old['formulas'] for c in r),'Unexpected formulas'
if ws.col_count<len(newheaders):ws.add_cols(len(newheaders)-ws.col_count)
ws.update(range_name='A1:X7001',values=matrix,value_input_option='RAW')
back=ws.get_all_values()
pad=lambda r:r+['']*(len(newheaders)-len(r))
assert [pad(r) for r in back]==matrix,'Readback mismatch'
for before,after in zip(old['values'][1:],back[1:]):
    a=dict(zip(old['values'][0],before));b=dict(zip(newheaders,after))
    assert all(b.get(k,'')==v for k,v in a.items()),'Original field changed'
(BASE/'aligned.json').write_text(json.dumps(back,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'rows':len(back)-1,'headers':newheaders,'all_original_fields_preserved':True},ensure_ascii=False))
