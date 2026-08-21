import sys
sys.path.insert(0, '../../../shared')
import sheets_io

client = sheets_io.get_client()
sh = client.open_by_url('https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing')
ws = sh.worksheet('ダッシュボード')
vals = ws.get('A1:G8')
for row in vals:
    print(row)

ws2 = sh.worksheet('送信実績')
print("\n--- 送信実績 last rows ---")
all_vals = ws2.get_all_values()
for row in all_vals[-4:]:
    print(row)
