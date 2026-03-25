import urllib.request
import os

urls = {
    "hero.jpg": "https://loremflickr.com/1920/1080/japanese,hotpot",
    "concept.jpg": "https://loremflickr.com/800/600/herbal,tea",
    "menu_course.jpg": "https://loremflickr.com/600/400/kaiseki",
    "menu_pot.jpg": "https://loremflickr.com/600/400/nabe",
    "menu_lunch.jpg": "https://loremflickr.com/600/400/bento",
    "map.jpg": "https://loremflickr.com/800/400/map"
}

for name, url in urls.items():
    print(f"Downloading {name}...")
    try:
        # Use a user agent to avoid 403 blocks (just in case)
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req) as response, open(name, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"Success: {name}")
    except Exception as e:
        print(f"Failed {name}: {e}")
