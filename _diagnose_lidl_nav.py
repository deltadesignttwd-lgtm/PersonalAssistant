import re
import requests

BASE_URL = "https://www.lidl.co.uk/c/lidl-plus-offers-current/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

res = requests.get(BASE_URL, headers=HEADERS, timeout=20, allow_redirects=True)
print("Final URL:", res.url)
print("Status:", res.status_code, "Length:", len(res.text))

html_text = res.text

# Look for any link/text mentioning "Weekly offers" or similar
for pattern in [r'[Ww]eekly [Oo]ffers?', r'lidl-plus-offers-current/a\d+', r'href="(/c/[^"]*offers[^"]*)"']:
    matches = re.findall(pattern, html_text)
    print(f"\nPattern {pattern!r}: {len(matches)} matches")
    for m in list(dict.fromkeys(matches))[:10]:
        print(" -", m)

# Print context around any "Weekly" occurrence
positions = [m.start() for m in re.finditer(r'Weekly', html_text)]
print(f"\n'Weekly' occurrences: {len(positions)}")
for pos in positions[:5]:
    print("---")
    print(html_text[max(0, pos-200):pos+200])

# Also check nav links containing "a10053222" (the id we currently hardcode) to see if base page still links to it
if "a10053222" in html_text:
    print("\nBase page still references a10053222")
else:
    print("\nBase page does NOT reference a10053222")
