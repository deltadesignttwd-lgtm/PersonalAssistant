import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

URL = "https://www.outsavvy.com/calendar/1953"
res = requests.get(URL, headers=HEADERS, timeout=20)
html = res.text
print(f"status: {res.status_code}, length: {len(html)}")
print(f"'Thursday' count: {html.count('Thursday')}")
print(f"'Friday' count: {html.count('Friday')}")

for day in ["Thursday", "Friday"]:
    idx = html.find(day)
    if idx != -1:
        print(f"\nContext around first '{day}' (idx={idx}):")
        print(html[max(0, idx - 600):idx + 400])

print("\n--- First 1500 chars ---")
print(html[:1500])
