import re
import requests

URL = "https://tfl.gov.uk/status-updates/strikes"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

res = requests.get(URL, headers=HEADERS, timeout=20)
print("STATUS:", res.status_code)
print("LENGTH:", len(res.text))
print("FIRST 1000 CHARS:")
print(res.text[:1000])
print("---")

for marker in ["__NEXT_DATA__", "application/ld+json", "strike", "Strike", "verification",
               "captcha", "cloudflare", "Just a moment", "window.__", "api/", "tube strike",
               "Industrial action"]:
    count = res.text.lower().count(marker.lower())
    print(f"MARKER {marker!r}: {count} occurrences")

print("---")
scripts = re.findall(r'<script[^>]*src="([^"]+)"', res.text)
print(f"Found {len(scripts)} <script src> tags, first 20:")
for s in scripts[:20]:
    print(" ", s)

print("---")
json_blocks = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', res.text, re.DOTALL)
print(f"Found {len(json_blocks)} inline application/json script blocks")
for i, b in enumerate(json_blocks):
    print(f"BLOCK {i} length:", len(b))
    if "strike" in b.lower():
        print("  -> contains 'strike', first 1500 chars:")
        print(" ", b[:1500])

ldjson_blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', res.text, re.DOTALL)
print(f"Found {len(ldjson_blocks)} ld+json blocks")
for b in ldjson_blocks[:3]:
    print(b[:800])
