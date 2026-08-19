# -*- coding: utf-8 -*-
import sys, datetime
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

rows = [
    {'_row': 45, 'sent_at': now, 'status': 'completed', 'error_reason': '', 'screenshot_path': '', 'provider_used': 'playwright_mcp'},
]
n = sheets_io.write_cells(ws, rows, columns=['sent_at','status','error_reason','screenshot_path','provider_used'], overwrite=True)
print(f"{n} cells written")
