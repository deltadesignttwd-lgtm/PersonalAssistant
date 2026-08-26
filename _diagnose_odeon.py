"""Throwaway diagnostic script - not part of the app. Deleted once the real
Odeon integration is built. Prints structural clues about the Odeon Greenwich
page so we can figure out how to actually get showtime data from a GH Actions
runner (which has real internet access, unlike the dev sandbox)."""
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

URLS_TO_TRY = [
    "https://www.odeon.co.uk/cinemas/greenwich/",
    "https://api.odeon.co.uk/3.0/api/all-cinemas/",
]

MARKERS = [
    "__NEXT_DATA__", "window.__NUXT__", 'id="__next"', 'id="root"',
    "Incapsula", "Just a moment", "cf-browser-verification", "captcha",
    "application/json", "greenwich", "showtimes", "Book Tickets",
]

for url in URLS_TO_TRY:
    print(f"\n===== {url} =====")
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"status_code: {res.status_code}")
        print(f"content-type: {res.headers.get('content-type')}")
        print(f"content-length: {len(res.content)}")
        body_lower = res.text.lower()
        for m in MARKERS:
            count = body_lower.count(m.lower())
            if count:
                print(f"  marker '{m}': found x{count}")
        print("--- first 1500 chars of body ---")
        print(res.text[:1500])
        print("--- last 800 chars of body ---")
        print(res.text[-800:])
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
