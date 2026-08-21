import sys
sys.path.insert(0, '../../../shared')
import sheets_io

client = sheets_io.get_client()
sh = client.open_by_url('https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing')
ws = sh.worksheet('ダッシュボード')
# get formulas
vals = ws.get('A1:G8', value_render_option='FORMULA')
for row in vals:
    print(row)
