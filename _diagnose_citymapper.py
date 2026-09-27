import re
import requests

URL = (
    "https://citymapper.com/directions?lang=en&startcoord=51.452024%2C-0.000944"
    "&endcoord=51.510131%2C-0.121783&startname=Hither+Green&endname=Virgin+Active+Strand"
    "&endaddress=Strand%2C+London%2C+UK"
)
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

for marker in [
    "__NEXT_DATA__", "__NUXT__", "application/json", "window.__",
    "INITIAL_STATE", "routeSummaries", "journeys", "directions_result",
    "<div id=\"root\"", "<div id=\"app\"", "recaptcha", "cf-challenge",
    "Just a moment", "Please enable JS", "noscript",
]:
    idx = text.find(marker)
    print(f"\nMarker '{marker}' found at index: {idx}")
    if idx != -1:
        print(text[max(0, idx - 100):idx + 300])

print("\n--- FIRST 2000 CHARS ---")
print(text[:2000])

print("\n--- LAST 1000 CHARS ---")
print(text[-1000:])

# Look for any script tags and print their src/type/id attributes
print("\n--- SCRIPT TAGS ---")
for m in re.finditer(r"<script[^>]*>", text):
    print(m.group(0))
