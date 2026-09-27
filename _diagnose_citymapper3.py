import requests

URL = (
    "https://citymapper.com/api/7/journeys"
    "?start=51.452024%2C-0.000944"
    "&end=51.510131%2C-0.121783"
    "&eaddr=Strand%2C%20London%2C%20UK"
    "&sname=Hither%20Green"
    "&ename=Virgin%20Active%20Strand"
    "&region_id=uk-london"
    "&include_stepfree=1"
    "&include_via_microtransit=1"
    "&status_format=html"
)

# Test with no special headers at all first
print("=== Attempt 1: plain requests, minimal headers ===")
res = requests.get(URL, timeout=20)
print("STATUS:", res.status_code)
print("CONTENT-TYPE:", res.headers.get("content-type"))
print(res.text[:1000])

print("\n\n=== Attempt 2: with browser-like headers ===")
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://citymapper.com/directions",
    "Accept": "application/json",
}
res2 = requests.get(URL, headers=headers, timeout=20)
print("STATUS:", res2.status_code)
print("CONTENT-TYPE:", res2.headers.get("content-type"))
try:
    data = res2.json()
    print("Parsed JSON OK. Top-level keys:", list(data.keys()))
    print("Number of journeys:", len(data.get("journeys", [])))
    print("Sections:", data.get("sections"))
    if data.get("journeys"):
        j = data["journeys"][0]
        print("\nFirst journey keys:", list(j.keys()))
        print("First journey summary:", {k: j[k] for k in j if k not in ("legs", "shared")})
        for leg in j.get("legs", []):
            leg_summary = {k: leg[k] for k in leg if k not in ("shape", "path", "stops")}
            print("  Leg:", leg_summary)
except Exception as e:
    print("Failed to parse JSON:", e)
    print(res2.text[:1500])
