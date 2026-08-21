# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','url','message','status','error_reason'])
for r in rows:
    if r['_row'] in (128,129,132):
        print(r['_row'], '|', r.get('company_name'), '|', r.get('contact_url') or r.get('url'))
        print('  status=', r.get('status'), '| err=', r.get('error_reason'))
        print('  msg_len=', len(r.get('message') or ''))
