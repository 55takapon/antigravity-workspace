import re
import requests

q = "神戸市 ホームページ制作会社 Web制作 公式"
html = requests.get(
    "https://www.bing.com/search?q=" + requests.utils.quote(q),
    headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"},
    timeout=20,
).text
print("len", len(html), "b_algo", html.find("b_algo"), "h2", html.find("<h2"))
for pat in [
    r'<a href="(https?://[^"]+)"',
    r'href="(https?://[^"]+)"',
    r'url&quot;:&quot;(https?://[^&]+)&quot;',
]:
    m = re.findall(pat, html)
    print("PAT", pat, len(m), m[:20])
