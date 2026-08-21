import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','message','status','error_reason','provider_used'])
candidates = []
for r in rows:
    if r['_row'] > 527:
        continue
    err = r.get('error_reason') or ''
    status = r.get('status') or ''
    provider = r.get('provider_used') or ''
    if 'reCAPTCHA v3' in err and status == 'failed' and provider != 'playwright_mcp':
        candidates.append(r)

print('total candidates:', len(candidates))
for r in candidates[:10]:
    print(r['_row'], r['company_name'], '|', r['contact_url'], '| msglen=', len(r.get('message') or ''))
