import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

NOW_URL = "https://tfl.gov.uk/traffic/status/?dateTypeSelect=Now&corridorIds=Central%20London%20Red%20Routes"
WEEKEND_URL = (
    "https://tfl.gov.uk/traffic/status/?dateTypeSelect=This%20weekend"
    "&startDate=2026-10-10T00%3A00%3A00&endDate=2026-10-11T23%3A59%3A59"
    "&corridorIds=Central%20London%20Red%20Routes"
)


def dump_page(label, url):
    print(f"\n===== {label}: {url} =====")
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        print(f"status_code={res.status_code}, len={len(res.text)}")
        text = res.text
        # Look for any embedded API base URLs / JSON data blobs / script src refs
        api_refs = set(re.findall(r'https?://[a-zA-Z0-9.\-]*tfl\.gov\.uk/[^"\'\s<>]+', text))
        for ref in sorted(api_refs)[:40]:
            print("API_REF:", ref)
        # Look for disruption-related text directly in the HTML (server-rendered?)
        disruption_hits = re.findall(r'.{60}disruption.{60}', text, re.IGNORECASE)
        print(f"disruption text occurrences: {len(disruption_hits)}")
        for h in disruption_hits[:10]:
            print("CONTEXT:", h.replace("\n", " "))
        # Save a snippet to inspect structure
        print("---HTML HEAD SNIPPET---")
        print(text[:1500])
    except Exception as e:
        print(f"ERROR fetching {label}: {e}")


def try_road_api():
    print("\n===== api.tfl.gov.uk/Road/all =====")
    try:
        res = requests.get("https://api.tfl.gov.uk/Road/all", timeout=20)
        print(f"status_code={res.status_code}")
        data = res.json()
        print(f"count of roads: {len(data)}")
        for road in data:
            name = road.get("displayName", "")
            rid = road.get("id", "")
            if "red route" in name.lower() or "central london" in name.lower() or "redroute" in rid.lower():
                print("MATCH:", rid, "|", name)
        print("Sample road ids (first 20):", [r.get("id") for r in data[:20]])
    except Exception as e:
        print(f"ERROR calling Road/all: {e}")

    for guess_id in ["centrallondonredroutes", "red-routes", "redroutes", "central-london"]:
        url = f"https://api.tfl.gov.uk/Road/{guess_id}/Disruption"
        try:
            res = requests.get(url, timeout=20)
            print(f"\nGUESS {guess_id}: status={res.status_code}, body[:300]={res.text[:300]}")
        except Exception as e:
            print(f"GUESS {guess_id}: ERROR {e}")


dump_page("NOW (Central London Red Routes)", NOW_URL)
dump_page("WEEKEND (Central London Red Routes)", WEEKEND_URL)
try_road_api()
