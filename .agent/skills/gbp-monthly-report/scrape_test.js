const urls = [
  { name: 'あし跡', url: 'https://maps.google.com/?cid=1120919318890702888' },
  { name: 'ととや', url: 'https://maps.google.com/?cid=2214345372730921121' },
  { name: 'とりこ', url: 'https://maps.google.com/?cid=7887144576631899508' }
];

async function run() {
  for (const t of urls) {
    try {
      const res = await fetch(t.url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' } });
      const html = await res.text();
      
      const ratingMatch = html.match(/\[\"([0-9.]+)\",([0-9]+)\]/);
      if (ratingMatch) {
        console.log(t.name, 'Rating:', ratingMatch[1], 'Reviews:', ratingMatch[2]);
      } else {
        const fallbackMatch = html.match(/([0-9.]+)\\",([0-9]+)/);
        if (fallbackMatch) {
          console.log(t.name, 'Rating:', fallbackMatch[1], 'Reviews:', fallbackMatch[2]);
        } else {
          console.log(t.name, 'Not found');
        }
      }
    } catch(e) {
      console.log(t.name, 'Error:', e.message);
    }
  }
}
run();
