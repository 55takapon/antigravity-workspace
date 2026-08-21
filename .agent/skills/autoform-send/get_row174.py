# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','url','message'])
for r in rows:
    if r['_row'] == 174:
        msg = r.get('message') or ''
        print("msg_len:", len(msg))
        with open('data/_msg174.txt', 'w', encoding='utf-8') as f:
            f.write(msg)
