import sys, datetime
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
sheets_io.write_cells(ws, [{
    "_row": 75,
    "sent_at": now,
    "status": "skipped",
    "error_reason": "フォーム内に「営業目的のお問い合わせはご遠慮ください」の明記あり → 送信せずスキップ",
    "screenshot_path": "",
    "provider_used": "playwright_mcp",
}], columns=["sent_at","status","error_reason","screenshot_path","provider_used"], overwrite=True)
print("row75 recorded", now)
