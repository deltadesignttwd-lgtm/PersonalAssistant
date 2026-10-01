import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

URL = "https://www.commonpress.co.uk/upcoming-events-new"
res = requests.get(URL, headers=HEADERS, timeout=20)
html = res.text
print(f"status: {res.status_code}, length: {len(html)}")

# Wix sites often embed a warmup-data / initial-state script tag
for marker in ["wix-warmup-data", "warmupData", "initialAppData", "SITE_CONTAINER", "wixCodeAppId", "application/json"]:
    idxs = [m.start() for m in re.finditer(re.escape(marker), html)]
    print(f"'{marker}': {len(idxs)} occurrences, first idx={idxs[0] if idxs else None}")

# Dump all <script type="application/json" ...> tag ids
json_script_ids = re.findall(r'<script type="application/json"[^>]*id="([^"]*)"', html)
print(f"application/json script ids: {json_script_ids}")

# Look for wix events app widget / viewer script references
for marker in ["events", "Events App", "wix-events"]:
    print(f"marker '{marker}' count: {html.count(marker)}")

# Try Wix's public Events API used by the Events widget (common pattern)
# Wix sites expose a metaSiteId; try to find it
meta_site_id = re.search(r'"metaSiteId"\s*:\s*"([a-f0-9-]+)"', html)
site_id = re.search(r'"siteId"\s*:\s*"([a-f0-9-]+)"', html)
print(f"metaSiteId found: {meta_site_id.group(1) if meta_site_id else None}")
print(f"siteId found: {site_id.group(1) if site_id else None}")

# Save a bigger chunk around "upcoming" or similar keyword if present
for kw in ["Upcoming", "upcoming", "No upcoming", "query"]:
    idx = html.find(kw)
    if idx != -1:
        print(f"\ncontext around '{kw}' (idx={idx}):\n{html[max(0,idx-200):idx+400]}")

# Try known Wix Events public API endpoint pattern
try:
    api_res = requests.get(
        "https://www.commonpress.co.uk/_api/wix-events-web/v1/events/query",
        headers=HEADERS,
        timeout=15,
    )
    print(f"\nwix-events-web API attempt status: {api_res.status_code}")
    print(api_res.text[:500])
except Exception as e:
    print(f"wix-events-web API attempt error: {e}")
