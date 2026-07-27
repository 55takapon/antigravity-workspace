import re
import requests

url = "https://www.biz.ne.jp/list/web/14_kanagawa/"
html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20).text
print("len", len(html))
print(html[:100])
urls = re.findall(r'https?://[^\s<>, "\']+', html)
print(urls[:80])
