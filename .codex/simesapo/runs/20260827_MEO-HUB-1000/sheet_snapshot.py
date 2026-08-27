import sys,json
from pathlib import Path
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist');sys.path.insert(0,str(ROOT/'shared'));import sheets_io
BASE=Path(__file__).parent
for tab,filename in [('MEOハブ候補','target_before.json'),('除外リスト','exclusions_before.json')]:
 ws=sheets_io.open_worksheet('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ',tab)
 values=ws.get_all_values()
 (BASE/filename).write_text(json.dumps(values,ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'tab':tab,'rows':len(values)-1,'header':values[0]},ensure_ascii=False))
