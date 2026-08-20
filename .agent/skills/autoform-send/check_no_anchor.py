# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','message','status'])
targets = [528,529,530,531,532,533,534,535,536]
for r in rows:
    if r['_row'] in targets:
        msg = r.get('message') or ''
        print(r['_row'], '|', r.get('company_name'), '| status=', r.get('status'), '| len=', len(msg))
        print('  末尾200字:', repr(msg[-200:]) if msg else '(空)')
        print()
