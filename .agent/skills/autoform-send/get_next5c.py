# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','url','status','error_reason'])
count = 0
for r in rows:
    if r['_row'] > 97:
        err = (r.get('error_reason') or '')
        if 'reCAPTCHA v3' in err or 'recaptcha' in err.lower():
            print(r['_row'], '|', r.get('company_name'), '|', r.get('contact_url') or r.get('url'), '| status=', r.get('status'))
            count += 1
    if count >= 10:
        break
