import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

candidates = [
    "https://www.outsavvy.com/organiser/the-common-press",
    "https://www.outsavvy.com/organiser/common-press",
    "https://www.outsavvy.com/organiser/the-common-press-cic",
    "https://www.outsavvy.com/organiser/commonpress",
]
for url in candidates:
    try:
        res = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        print(f"{url} -> status {res.status_code}, final_url={res.url}, len={len(res.text)}, 'Thursday' count={res.text.count('Thursday')}")
    except Exception as e:
        print(f"{url} -> ERROR {e}")

# Also try the responsive-calendar.min.js to find its AJAX endpoint
try:
    js_res = requests.get("https://www.outsavvy.com/js/responsive-calendar.min.js", headers=HEADERS, timeout=15)
    print(f"\nresponsive-calendar.min.js status: {js_res.status_code}, length: {len(js_res.text)}")
    # search for ajax/url patterns
    urls_in_js = re.findall(r'["\'](/[a-zA-Z0-9_/\-\.]*(?:ajax|calendar|event)[a-zA-Z0-9_/\-\.]*)["\']', js_res.text, re.IGNORECASE)
    print("candidate endpoint paths found in JS:", set(urls_in_js))
except Exception as e:
    print(f"JS fetch error: {e}")

# Try a direct AJAX guess based on common OutSavvy calendar patterns
for path in [
    "/calendar/1953/events",
    "/calendar/ajax/1953",
    "/ajax/calendar/1953",
    "/organiser/1953/events",
]:
    url = "https://www.outsavvy.com" + path
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"{url} -> {res.status_code}, len={len(res.text)}")
    except Exception as e:
        print(f"{url} -> ERROR {e}")
