import re
import requests

html = requests.get(
    "https://www.homepage.work/chiba/",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
).text
print("len", len(html), "http_count", html.count("https://"))
urls = re.findall(r"https?://[^\"'<> \n]+", html)
print(urls[:80])
i = html.find("GOODLIFE")
print("idx", i)
print(html[max(0, i - 500): i + 800])
