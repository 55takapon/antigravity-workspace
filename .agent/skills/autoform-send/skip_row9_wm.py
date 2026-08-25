import sys, datetime
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'Webマーケ')
now = datetime.datetime.now().isoformat()

row = {
    '_row': 9,
    'status': 'failed',
    'provider_used': 'playwright_mcp',
    'sent_at': now,
    'error_reason': 'contact_urlページにお問い合わせフォームが存在せず（電話・メールアドレスのみ掲載）送信不可',
}
sheets_io.write_cells(ws, [row], columns=['status', 'provider_used', 'sent_at', 'error_reason'], overwrite=True)
print('row9 recorded')
