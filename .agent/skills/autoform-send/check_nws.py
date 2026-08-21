import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','status','error_reason','provider_used','sent_at','message'])

matches = [r for r in rows if 'NWS' in (r.get('company_name') or '')]
for r in matches:
    print("row:", r['_row'])
    print("company:", r['company_name'])
    print("contact_url:", r['contact_url'])
    print("status:", r['status'])
    print("provider_used:", r['provider_used'])
    print("sent_at:", r['sent_at'])
    print("error_reason:", (r.get('error_reason') or '')[:100])
    print("msglen:", len(r.get('message') or ''))
    print("---")
