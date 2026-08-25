import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
headers = ws.row_values(1)
for i, h in enumerate(headers, start=1):
    col_letter = ""
    n = i
    while n > 0:
        n, r = divmod(n-1, 26)
        col_letter = chr(65+r) + col_letter
    print(col_letter, h)
