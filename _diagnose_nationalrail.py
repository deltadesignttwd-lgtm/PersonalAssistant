import re
import requests

URL = "https://www.nationalrail.co.uk/live-trains/departures/lewisham/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

res = requests.get(URL, headers=HEADERS, timeout=20)
print("STATUS:", res.status_code)
print("LENGTH:", len(res.text))
print("CONTENT-TYPE:", res.headers.get("content-type"))

text = res.text
print("\nContains 'replacement' (case-insensitive)?", "replacement" in text.lower())
print("Contains 'rail replacement'?", "rail replacement" in text.lower())
print("Contains 'bus'?", "bus" in text.lower())

# Print any lines/context around the word "replacement"
for m in re.finditer(r"replacement", text, re.IGNORECASE):
    start = max(0, m.start() - 150)
    end = min(len(text), m.end() + 150)
    print("\n--- context around 'replacement' ---")
    print(text[start:end])

# Save a snippet of the raw HTML to inspect structure (first 5000 chars)
print("\n--- FIRST 3000 CHARS OF HTML ---")
print(text[:3000])

# Check for any JSON blobs / __NEXT_DATA__ / data attributes commonly used for SSR
for marker in ["__NEXT_DATA__", "application/json", "data-testid", "window.__", "serviceStatus", "disruption", "planned engineering"]:
    idx = text.find(marker)
    print(f"\nMarker '{marker}' found at index: {idx}")
    if idx != -1:
        print(text[max(0, idx - 100):idx + 300])
