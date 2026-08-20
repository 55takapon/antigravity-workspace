# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','message','status'])

TARGET_STATUS = {'failed', 'skipped', ''}
checked, over2000, still_old = 0, [], 0
for r in rows:
    msg = (r.get('message') or '')
    status = (r.get('status') or '').strip()
    if not msg.strip() or status not in TARGET_STATUS:
        continue
    if '今の体制のままでも' not in msg and '追伸' not in msg:
        still_old += 1
    checked += 1
    if len(msg) > 2000:
        over2000.append((r['_row'], r.get('company_name'), len(msg)))

print(f"検査対象(failed/空欄/skipped): {checked}件")
print(f"新本文が未反映(旧のまま): {still_old}件")
print(f"2000字超え（残存）: {len(over2000)}件")
for row in over2000:
    print(" ", row)
