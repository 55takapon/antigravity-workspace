# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['message'])
lens = [len(r.get('message') or '') for r in rows if (r.get('message') or '').strip()]
lens.sort()
n = len(lens)
print(f"message列あり: {n}件")
print(f"  最短 {lens[0]}字 / 中央 {lens[n//2]}字 / 最長 {lens[-1]}字")
BODY_NOW, BODY_NEW = 1933, 1732
op = [l - BODY_NOW for l in lens]
print(f"冒頭文の推定長: 最短 {op[0]}字 / 中央 {op[n//2]}字 / 最長 {op[-1]}字")
over_now = sum(1 for l in lens if l > 2000)
over_new = sum(1 for l in lens if l - (BODY_NOW-BODY_NEW) > 2000)
print(f"2000字超え: 現状 {over_now}件 ({over_now/n*100:.0f}%) → 201字削減後 {over_new}件 ({over_new/n*100:.0f}%)")
