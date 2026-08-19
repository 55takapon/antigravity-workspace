# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','url','contact_url','message'])
for r in rows:
    if r['_row'] == 25:
        with open('data/_msg25.txt', 'w', encoding='utf-8') as f:
            f.write(r.get('message') or '')
        print("company:", r.get('company_name'))
        print("msg length:", len(r.get('message') or ''))
