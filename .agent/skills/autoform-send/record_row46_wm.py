import sys, datetime
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
sheets_io.write_cells(ws, [{
    "_row": 46,
    "sent_at": now,
    "status": "message_too_long",
    "error_reason": "お問い合わせ内容欄が文字数制限で「文字数が正しくありません」エラー、本文1930字で収まらず → 要見直し",
    "screenshot_path": "",
    "provider_used": "playwright_mcp",
}], columns=["sent_at","status","error_reason","screenshot_path","provider_used"], overwrite=True)
print("row46 recorded", now)
