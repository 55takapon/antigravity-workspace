import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'Webマーケ')
rows = sheets_io.read_rows(ws, want=['company_name','status','sent_at','provider_used','error_reason'])
for r in rows:
    if r['_row'] in (3,4,5):
        print(r['_row'], r['company_name'], '|', r['status'], '|', r['provider_used'], '|', r['error_reason'])
