import sys,json
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\shared')
import sheets_io
ws=sheets_io.open_worksheet('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ','MEOハブ候補')
before=ws.get_all_values();assert len(before)==7001
pad=lambda r:r+['']*max(0,28-len(r))
expected=[pad(r) for r in before]
assert not any(r[27] for r in expected),'AB already used'
expected[0][27]='original_list_label'
changed=[]
for i,r in enumerate(expected[1:],2):
    if r[8]=='MEOハブ候補':r[27]=r[8];r[8]='';changed.append(i)
assert len(changed)==6728,('Unexpected label count',len(changed))
if ws.col_count<28:ws.add_cols(28-ws.col_count)
ws.batch_update([{'range':'I2:I7001','values':[[r[8]] for r in expected[1:]]},{'range':'AB1:AB7001','values':[[r[27]] for r in expected]}],value_input_option='RAW')
back=ws.get_all_values();assert [pad(r) for r in back]==expected
(BASE/'working_baseline.json').write_text(json.dumps(back,ensure_ascii=False),encoding='utf-8')
(BASE/'list_label_change.json').write_text(json.dumps({'moved_rows':changed,'moved_count':len(changed),'from':'I','to':'AB','manual_status_preserved':sum(r[8]=='手動送信要' for r in expected[1:]),'readback_exact':True},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'labels_moved_to_AB':len(changed),'manual_status_preserved':sum(r[8]=='手動送信要' for r in expected[1:]),'readback_exact':True}))
