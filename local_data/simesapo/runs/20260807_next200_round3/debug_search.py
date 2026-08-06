import requests
from bs4 import BeautifulSoup

name = "株式会社ビューティープロモーション・サポート"
r = requests.get("https://www.bing.com/search", params={"q": f'"{name}" 美容'}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
s = BeautifulSoup(r.text, "html.parser")
print(r.status_code, r.url, len(r.text), len(s.select("li.b_algo")))
for a in s.select("li.b_algo h2 a[href]")[:5]:
    print(a.get_text(" ", strip=True), a.get("href"))
