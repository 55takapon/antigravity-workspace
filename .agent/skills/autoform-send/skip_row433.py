import sys, datetime
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

row = {
    '_row': 433,
    'status': 'failed',
    'provider_used': 'playwright_mcp',
    'sent_at': now,
    'error_reason': 'CF7送信時に invalid_json エラーが継続発生し送信不可（サイト側の不具合、複数回リトライしても再発）',
}
sheets_io.write_cells(ws, [row], columns=['status', 'provider_used', 'sent_at', 'error_reason'], overwrite=True)
print('row433 recorded: failed')
