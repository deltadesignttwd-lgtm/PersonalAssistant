import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

BUNDLE_URL = "https://www.nationalrail.co.uk/nreassets/_next/static/chunks/pages/_app-e047dcbc93d317e0.js"

res = requests.get(BUNDLE_URL, headers=HEADERS, timeout=20)
text = res.text
print("Bundle length:", len(text))

for m in re.finditer(re.escape("planjourney/search"), text):
    start = max(0, m.start() - 400)
    end = min(len(text), m.end() + 200)
    print("\n----- occurrence context -----")
    print(text[start:end])
    break  # first occurrence is enough context, they likely repeat the same template

print("\n===== Trying the endpoint directly (GET, mirroring page query params) =====")
params = {
    "type": "single",
    "origin": "LEW",
    "destination": "CHX",
    "leavingType": "departing",
    "leavingDate": "161126",
    "leavingHour": "08",
    "leavingMin": "10",
    "adults": "1",
    "extraTime": "0",
}
try:
    res2 = requests.get(
        "https://ojp.nationalrail.co.uk/service/planjourney/search",
        params=params,
        headers={**HEADERS, "Accept": "application/json", "Referer": "https://www.nationalrail.co.uk/"},
        timeout=20,
    )
    print("STATUS:", res2.status_code)
    print("CONTENT-TYPE:", res2.headers.get("content-type"))
    print("FIRST 1500 CHARS:")
    print(res2.text[:1500])
except Exception as e:
    print("Request failed:", e)
