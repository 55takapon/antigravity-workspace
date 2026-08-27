import sys,json
from pathlib import Path
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist')
sys.path.insert(0,str(ROOT/'shared'))
import sheets_io
BASE=Path(__file__).parent
tabs=['シート1','Webマーケ','MEO業者','SNS運用','除外リスト','251127作成','251222作成','Web幹事','シート2','MEOハブ候補']
out=[]
for tab in tabs:
 ws=sheets_io.open_worksheet('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ',tab)
 if tab in ['除外リスト','MEOハブ候補']:
  p=BASE/('target_before.json' if tab=='MEOハブ候補' else 'exclusions_before.json')
  if p.exists():raise RuntimeError('Snapshot already exists; do not overwrite')
  values=ws.get_all_values();p.write_text(json.dumps(values,ensure_ascii=False),encoding='utf-8')
  print(tab,len(values)-1,flush=True)
 out.extend(sheets_io.read_rows(ws,want=['company_name','url','phone'],aliases={'phone':['連絡先','電話番号']}))
(BASE/'existing_live.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
print('existing',len(out))
