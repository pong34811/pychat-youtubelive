import httpx
import re

r = httpx.get("https://www.youtube.com/watch?v=jGIneEjKYU8", headers={"Accept-Language": "th"})
live = re.search(r'"isLive"\s*:\s*true', r.text)
print(f"isLive: {bool(live)}")
if live:
    print("This is a live stream")
else:
    print("Not a live stream (or ended)")
