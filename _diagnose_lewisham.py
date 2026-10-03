import json
import re
import requests

NATIONALRAIL_LEWISHAM_URL = "https://www.nationalrail.co.uk/live-trains/departures/lewisham/"
_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(\{.*?\})</script>')
_NATIONALRAIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

res = requests.get(NATIONALRAIL_LEWISHAM_URL, headers=_NATIONALRAIL_HEADERS, timeout=20)
res.raise_for_status()
print(f"status: {res.status_code}, length: {len(res.text)}")

match = _NEXT_DATA_RE.search(res.text)
if not match:
    print("NO __NEXT_DATA__ MATCH FOUND")
    raise SystemExit

data = json.loads(match.group(1))
queries = data.get("props", {}).get("pageProps", {}).get("liveTrainsState", {}).get("queries", [])
print(f"queries count: {len(queries)}")
if not queries:
    print("queries is empty")
    raise SystemExit

print(f"queries[0] keys: {list(queries[0].keys())}")
state = queries[0].get("state", {})
print(f"state keys: {list(state.keys())}")
print(f"state.status (if any): {state.get('status')}")
print(f"state.error (if any): {state.get('error')}")

data_field = state.get("data")
print(f"state.data type: {type(data_field)}, value preview: {str(data_field)[:300]}")

if data_field is None:
    print("state.data IS None -- this is the root cause")
else:
    pages = data_field.get("pages", [])
    print(f"pages type: {type(pages)}, count: {len(pages) if isinstance(pages, list) else 'N/A'}")
    if pages:
        page = pages[0]
        print(f"page keys: {list(page.keys())}")
        nrcc = page.get("nrccMessages")
        services = page.get("services")
        print(f"nrccMessages type: {type(nrcc)}, value: {str(nrcc)[:300]}")
        print(f"services type: {type(services)}, value: {str(services)[:300]}")
