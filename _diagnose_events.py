import re
import json
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

SITES = {
    "commonpress": "https://www.commonpress.co.uk/upcoming-events-new",
    "outsavvy": "https://www.outsavvy.com/organiser/la-camionera",
    "dalstonsuperstore": "https://dalstonsuperstore.com/whats-on/",
    "oldnunshead": "https://www.theoldnunshead.co.uk/events",
}


def dump(name, url):
    print(f"\n{'=' * 60}\n{name}: {url}\n{'=' * 60}")
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        print(f"status: {res.status_code}, length: {len(res.text)}")
    except Exception as e:
        print(f"FETCH ERROR: {e}")
        return
    html = res.text

    # Look for JSON-LD event schema
    ld_blocks = re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    print(f"JSON-LD blocks found: {len(ld_blocks)}")
    for i, block in enumerate(ld_blocks[:3]):
        try:
            data = json.loads(block)
            print(f"  [{i}] type={data.get('@type') if isinstance(data, dict) else type(data)}")
            snippet = json.dumps(data)[:500]
            print(f"      {snippet}")
        except Exception as e:
            print(f"  [{i}] JSON parse error: {e}, raw snippet: {block[:200]}")

    # Look for __NEXT_DATA__ / __NUXT__ / window.__INITIAL_STATE__
    for marker in ["__NEXT_DATA__", "__NUXT__", "__INITIAL_STATE__", "window.__data"]:
        if marker in html:
            print(f"Found marker: {marker}")

    # Look for common event-related class names/keywords
    for kw in ["event", "Event", "Thursday", "Friday"]:
        count = html.count(kw)
        print(f"occurrences of '{kw}': {count}")

    # Print a snippet around first occurrence of "Thursday" or "Friday" if any
    for day in ["Thursday", "Friday"]:
        idx = html.find(day)
        if idx != -1:
            print(f"\nContext around first '{day}' (idx={idx}):")
            print(html[max(0, idx - 300):idx + 300])

    # Save a truncated copy of raw HTML for structural inspection
    print(f"\n--- First 2000 chars of raw HTML ---")
    print(html[:2000])


for name, url in SITES.items():
    dump(name, url)
