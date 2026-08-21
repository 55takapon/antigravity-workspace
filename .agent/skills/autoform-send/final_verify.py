import sys
sys.path.insert(0, '../../../shared')
import sheets_io

client = sheets_io.get_client()
sh = client.open_by_url('https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing')
ws = sh.worksheet('送信実績')
vals = ws.get_all_values()
print("total rows:", len(vals))
for i, row in enumerate(vals[:13], start=1):
    print(i, row)

print("\n--- checking no leftover data beyond row 12 ---")
for i, row in enumerate(vals[12:], start=13):
    if any(cell.strip() for cell in row):
        print("LEFTOVER at row", i, row[:3])

# Dashboard check
ws2 = sh.worksheet('ダッシュボード')
print("\n--- dashboard ---")
print(ws2.get('A1:G8'))
