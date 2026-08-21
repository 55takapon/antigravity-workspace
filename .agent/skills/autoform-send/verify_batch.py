import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','status','provider_used','error_reason'])
target = [174,175,197,213,215,216,217,227,242,243]
for r in rows:
    if r['_row'] in target:
        print(r['_row'], r['company_name'], '|', r['status'], '|', r['provider_used'], '|', (r['error_reason'] or '')[:40])
