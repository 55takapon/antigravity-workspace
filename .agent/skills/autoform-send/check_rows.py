# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','url','status','sent_at','error_reason','provider_used'])
targets = [3,6,7,10,14,15]
for r in rows:
    if r['_row'] in targets:
        print(r['_row'], '|', r.get('company_name'), '| status=', r.get('status'), '| sent_at=', r.get('sent_at'), '| provider=', r.get('provider_used'), '| err=', r.get('error_reason'))
