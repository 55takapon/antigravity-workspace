# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','url','status','error_reason'])
count = 0
for r in rows:
    if r['_row'] > 132:
        err = (r.get('error_reason') or '')
        status = (r.get('status') or '').strip()
        if 'reCAPTCHA v3' in err and 'playwright_mcp' not in (r.get('provider_used') or '') and status == 'failed':
            print(r['_row'], '|', r.get('company_name'), '|', r.get('contact_url') or r.get('url'))
            count += 1
    if count >= 5:
        break
