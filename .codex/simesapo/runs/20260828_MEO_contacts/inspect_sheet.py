import sys,json
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\shared')
import sheets_io
book=sheets_io.get_client().open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ')
for name in ['SNS運用','MEOハブ候補']:
    ws=book.worksheet(name); values=ws.get_all_values(); formulas=ws.get_all_values(value_render_option='FORMULA')
    dest=BASE/(name+'_before.json')
    if dest.exists():raise RuntimeError('Snapshot already exists: '+str(dest))
    dest.write_text(json.dumps({'id':ws.id,'rows':ws.row_count,'cols':ws.col_count,'values':values,'formulas':formulas},ensure_ascii=False),encoding='utf-8')
    h=values[0]; ci=h.index('contact_url') if 'contact_url' in h else None
    print(json.dumps({'tab':name,'data_rows':len(values)-1,'grid_columns':ws.col_count,'headers':h,'contact_count':sum(bool(len(r)>ci and r[ci]) for r in values[1:]) if ci is not None else None,'formula_count':sum(str(c).startswith('=') for r in formulas for c in r)},ensure_ascii=False),flush=True)
