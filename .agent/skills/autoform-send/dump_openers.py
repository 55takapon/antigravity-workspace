# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','message'])
targets = [6, 528, 531]
ANCHORS = ['貴社の取り組みを拝見する中で、', 'サイト制作後も、']
for r in rows:
    if r['_row'] not in targets: continue
    msg = r.get('message') or ''
    idx = -1
    for a in ANCHORS:
        i = msg.find(a)
        if i != -1:
            idx = i; anchor = a; break
    print('='*60)
    print(f"行{r['_row']} | {r.get('company_name')} | 全体{len(msg)}字 | 冒頭文{idx}字 | anchor='{anchor if idx!=-1 else 'なし'}'")
    print('-'*60)
    print(msg[:idx] if idx!=-1 else msg[:600])
