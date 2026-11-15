import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def probe(label, url):
    print(f"\n===== {label} =====")
    print("URL:", url)
    res = requests.get(url, headers=HEADERS, timeout=20)
    print("STATUS:", res.status_code)
    print("LENGTH:", len(res.text))

    for marker in ["Charing Cross", "08:10", "0810", "cancelled", "delayed", "On time",
                   "__NEXT_DATA__", "api.nationalrail", "ldbws", "darwin"]:
        count = res.text.lower().count(marker.lower())
        print(f"MARKER {marker!r}: {count} occurrences")

    idx = res.text.find("window.__")
    if idx != -1:
        print("CONTEXT around 'window.__':")
        print(res.text[max(0, idx - 50):idx + 400])

    json_blocks = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', res.text, re.DOTALL)
    for i, b in enumerate(json_blocks):
        print(f"JSON BLOCK {i} length: {len(b)}")
        if "0810" in b or "08:10" in b or "harin" in b.lower():
            print("  -> contains journey-relevant text! first 1000 chars:")
            print(" ", b[:1000])

    return res.text


journey_html = probe(
    "Journey planner (LEW->CHX 08:10)",
    "https://www.nationalrail.co.uk/journey-planner/?type=single&origin=LEW"
    "&destination=CHX&leavingType=departing&leavingDate=161126&leavingHour=08"
    "&leavingMin=10&adults=1&extraTime=0",
)

departures_html = probe(
    "Live departures board (Lewisham)",
    "https://www.nationalrail.co.uk/live-trains/departures/lewisham/",
)

# Search script bundle filenames referenced in the journey planner page for anything
# that looks like it might be a data/api loader, then fetch one or two to grep for
# fetch()/endpoint strings.
script_srcs = re.findall(r'<script[^>]*src="([^"]+)"', journey_html)
candidate = next((s for s in script_srcs if "app" in s or "journey" in s.lower()), None)
print("\n===== Candidate JS bundle =====")
print(candidate)
if candidate:
    full_url = candidate if candidate.startswith("http") else f"https://www.nationalrail.co.uk{candidate}"
    try:
        res = requests.get(full_url, headers=HEADERS, timeout=20)
        print("STATUS:", res.status_code, "LENGTH:", len(res.text))
        for m in re.findall(r'https://[a-zA-Z0-9\.\-]*nationalrail[a-zA-Z0-9\.\-]*/[a-zA-Z0-9/_\-]*', res.text)[:20]:
            print("  FOUND URL FRAGMENT:", m)
    except Exception as e:
        print("fetch failed:", e)
