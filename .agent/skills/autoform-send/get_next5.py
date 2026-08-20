# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','url','message','status'])
targets = [55,56,65,66,67]
for r in rows:
    if r['_row'] in targets:
        print(r['_row'], '|', r.get('company_name'), '|', r.get('contact_url') or r.get('url'), '| status=', r.get('status'))
        with open(f'data/_msg{r["_row"]}.txt', 'w', encoding='utf-8') as f:
            f.write(r.get('message') or '')
