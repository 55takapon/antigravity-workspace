import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "送信実績")

row_20260825 = [
    "2026-08-25",
    "SESSION-20260825-Webmarke",
    "Webマーケ",
    "2-99",
    "web-ver03",
    "",
    "90",
    "49",
    "28",
    "13",
    "54.4%",
    "0",
    "0",
    "0.0%",
    "0.0%",
    "005-form-send Tier A(HTTP/汎用フォーム)+Tier B(Playwright MCP)併用／reCAPTCHA v3・Turnstileで自動化不可の行は失敗として記録、営業お断り明記・404・フォーム不備は目視判定でスキップ、文字数超過は要見直しとして失敗に計上／シートstatus・sent_at列(8/25分)実測値",
]

ws.update("A13", [row_20260825])
print("appended row 13")
