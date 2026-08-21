import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','form_url','message','status','error_reason','provider_used','name','email','tel'])
for r in rows:
    if r['_row'] == 243:
        for k,v in r.items():
            print(k, '=', repr(v)[:200])
