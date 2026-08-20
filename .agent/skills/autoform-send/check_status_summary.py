# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io
from collections import Counter

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['message','status'])
target = [r for r in rows if (r.get('message') or '').strip()]
print(f"message列あり合計: {len(target)}件")
c = Counter((r.get('status') or '(空欄)').strip() or '(空欄)' for r in target)
for status, n in c.most_common():
    print(f"  status={status}: {n}件")
