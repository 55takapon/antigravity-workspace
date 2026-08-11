import sys
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

url = sys.argv[1]
r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
r.encoding = r.apparent_encoding or r.encoding
soup = BeautifulSoup(r.text, "html.parser")
for a in soup.find_all("a", href=True):
    text = " ".join(a.get_text(" ", strip=True).split())
    href = urljoin(r.url, a["href"])
    if any(x in (text + " " + href).lower() for x in ("営業", "提案", "contact", "form", "inquiry")):
        print(text, "=>", href)
