import sys
sys.path.insert(0, '../../../shared')
import sheets_io

client = sheets_io.get_client()
sh = client.open_by_url('https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing')
ws = sh.worksheet('送信実績')

# Clear the misplaced rows 251 and 252
ws.batch_clear(['A251:P252'])

row_20 = ['2026-08-20', 'SESSION-20260820-SNSunyo', 'SNS運用', '10-145', 'sns', '', '14', '14', '0', '0', '100.0%', '0', '0', '0.0%', '0.0%', '005-form-send Tier B(Playwright MCP)／reCAPTCHA v3未再試行分を個別再送／シートstatus・sent_at列(8/20分)実測値']
row_21 = ['2026-08-21', 'SESSION-20260821-SNSunyo', 'SNS運用', '3-525', 'sns', '', '99', '81', '12', '6', '81.8%', '0', '0', '0.0%', '0.0%', '005-form-send Tier B(Playwright MCP)中心／reCAPTCHA v3で未再試行だった行を10件バッチで反復再送／文字数超過・専用フォーム不適合はスキップ、CF7サーバーエラー等は失敗として記録／シートstatus・sent_at列(8/21分)実測値']

ws.update('A11', [row_20], value_input_option='USER_ENTERED')
ws.update('A12', [row_21], value_input_option='USER_ENTERED')
print("done")
