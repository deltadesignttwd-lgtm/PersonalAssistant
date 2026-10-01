import json
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

match = re.search(
    r'<script type="application/json" id="wix-warmup-data">(.*?)</script>',
    html,
    re.DOTALL,
)
if not match:
    print("wix-warmup-data script tag not found with that pattern")
    idx = html.find("wix-warmup-data")
    print(html[max(0, idx - 300):idx + 2000])
else:
    raw = match.group(1)
    print(f"wix-warmup-data length: {len(raw)}")
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"JSON parse error: {e}")
        print(raw[:1000])
        raise SystemExit

    def walk(obj, path=""):
        """Recursively search for keys that look event-related."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                lk = k.lower()
                if "event" in lk or "schedul" in lk:
                    print(f"KEY MATCH: {path}.{k}  (type={type(v).__name__})")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:5]):
                walk(v, f"{path}[{i}]")

    print("Top-level keys:", list(data.keys()))
    walk(data)

    # Dump raw to a file for structural inspection, print first/last chars
    print("\n--- raw snippet start ---")
    print(raw[:3000])
