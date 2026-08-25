import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "送信実績")
all_vals = ws.get_all_values()
for i in range(1, 15):
    print(i, all_vals[i-1])
