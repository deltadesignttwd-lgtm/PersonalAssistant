import re
import requests

URL = (
    "https://www.nationalrail.co.uk/journey-planner/?type=single&origin=LEW"
    "&destination=CHX&leavingType=departing&leavingDate=161126&leavingHour=08"
    "&leavingMin=10&adults=1&extraTime=0"
)

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
print("FIRST 500 CHARS:")
print(res.text[:500])
print("---")

for marker in ["__NEXT_DATA__", "application/ld+json", "Charing Cross", "08:10", "cancelled", "delayed",
               "api/", "window.__", "verification", "captcha", "cloudflare", "Just a moment"]:
    count = res.text.lower().count(marker.lower())
    print(f"MARKER {marker!r}: {count} occurrences")

print("---")
scripts = re.findall(r'<script[^>]*src="([^"]+)"', res.text)
print(f"Found {len(scripts)} <script src> tags, first 20:")
for s in scripts[:20]:
    print(" ", s)

print("---")
inline_json_blocks = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', res.text, re.DOTALL)
print(f"Found {len(inline_json_blocks)} inline application/json script blocks")
for b in inline_json_blocks[:3]:
    print("BLOCK (first 500 chars):", b[:500])
