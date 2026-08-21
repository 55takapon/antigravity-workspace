import sys
sys.path.insert(0, '../../../shared')
import sheets_io

client = sheets_io.get_client()
sh = client.open_by_url('https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing')
ws = sh.worksheet('送信実績')

all_vals = ws.get_all_values()
print("total rows:", len(all_vals))
for i, row in enumerate(all_vals, start=1):
    if row and any(cell.strip() for cell in row):
        print(i, row[:3])
