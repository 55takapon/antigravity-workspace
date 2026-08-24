import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'Webマーケ')
headers = ws.row_values(1)
print("headers:", headers)
rows = sheets_io.read_rows(ws, want=['company_name','url','contact_url','message','status','sent_at','error_reason'])
for r in rows:
    if r['_row'] == 2:
        for k,v in r.items():
            print(k, '=', repr(v)[:300])
