# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, '../../../shared')
import sheets_io

with open('_splice_preview.json', encoding='utf-8') as f:
    updates = json.load(f)

print(f"書き戻し対象: {len(updates)}件")

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
n = sheets_io.write_cells(ws, updates, columns=['message'], overwrite=True)
print(f"{n} セル書き込み完了")
