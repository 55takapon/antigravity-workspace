# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','url','status','error_reason','provider_used'])
count = 0
targets = []
for r in rows:
    if r['_row'] > 168 and r['_row'] <= 527:
        err = (r.get('error_reason') or '')
        status = (r.get('status') or '').strip()
        provider = (r.get('provider_used') or '')
        if 'reCAPTCHA v3' in err and status == 'failed' and provider != 'playwright_mcp':
            targets.append(r['_row'])
            print(r['_row'], '|', r.get('company_name'), '|', r.get('contact_url') or r.get('url'))
            count += 1
    if count >= 10:
        break
