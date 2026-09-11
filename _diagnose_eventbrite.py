import requests

URL = "https://www.eventbrite.co.uk/d/united-kingdom--london/lesbian-events/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

print("=== Plain requests.get (no headers) ===")
try:
    res = requests.get(URL, timeout=15)
    print("Status:", res.status_code)
    print("Length:", len(res.text))
    print(res.text[:2000])
except Exception as e:
    print("Error:", e)

print("\n=== requests.get with browser-like headers ===")
try:
    res = requests.get(URL, headers=HEADERS, timeout=15)
    print("Status:", res.status_code)
    print("Length:", len(res.text))
    print(res.text[:3000])
    # Look for JSON-LD or embedded JSON that might contain event data
    if '__SERVER_DATA__' in res.text:
        print("\n--- Found __SERVER_DATA__ marker ---")
    if 'application/ld+json' in res.text:
        print("\n--- Found ld+json marker ---")
except Exception as e:
    print("Error:", e)

print("\n=== Trying Eventbrite's internal search API endpoint ===")
try:
    api_url = "https://www.eventbrite.co.uk/api/v3/destination/search/"
    payload = {
        "event_search": {
            "dates": "current_future",
            "dedup": True,
            "online_events_only": False,
            "tags": ["EventbriteOrganizerHasOtherEvents"],
        },
        "expand.destination_event": [
            "primary_venue", "image", "ticket_availability", "saves", "event_sales_status",
            "primary_organizer", "public_collections",
        ],
    }
    res = requests.post(api_url, json=payload, headers=HEADERS, timeout=15)
    print("Status:", res.status_code)
    print(res.text[:2000])
except Exception as e:
    print("Error:", e)
