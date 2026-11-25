import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

MODES = "tube,dlr,overground,elizabeth-line,tram"
url = f"https://api.tfl.gov.uk/Line/Mode/{MODES}/Status?detail=true"
res = requests.get(url, headers=HEADERS, timeout=20)
print("STATUS:", res.status_code)
data = res.json()
print("Number of lines returned:", len(data))

found_any_strike_mention = False
for line in data:
    for status in line.get("lineStatuses", []):
        reason = status.get("reason", "") or ""
        disruption = status.get("disruption") or {}
        description = disruption.get("description", "") or ""
        additional_info = disruption.get("additionalInfo", "") or ""
        combined = f"{reason} {description} {additional_info}"
        if "strike" in combined.lower() or "industrial action" in combined.lower():
            found_any_strike_mention = True
            print(f"\n=== STRIKE MENTION on {line.get('name')} ===")
            print("statusSeverityDescription:", status.get("statusSeverityDescription"))
            print("reason:", reason)
            print("disruption.category:", disruption.get("category"))
            print("disruption.categoryDescription:", disruption.get("categoryDescription"))
            print("disruption.description:", description[:1000])
            print("disruption.additionalInfo:", additional_info[:1000])
            print("validityPeriods:", disruption.get("validityPeriods"))

if not found_any_strike_mention:
    print("\nNo strike/industrial action mentions found in current Status data for these modes.")

# Also check the dedicated Disruption endpoint which sometimes carries more detail
url2 = f"https://api.tfl.gov.uk/Line/Mode/{MODES}/Disruption"
res2 = requests.get(url2, headers=HEADERS, timeout=20)
print("\n\n===== /Disruption endpoint =====")
print("STATUS:", res2.status_code)
data2 = res2.json()
print("Number of disruption entries:", len(data2))
for d in data2:
    combined = f"{d.get('description','')} {d.get('additionalInfo','')}"
    if "strike" in combined.lower() or "industrial action" in combined.lower():
        print("\n=== STRIKE MENTION ===")
        print(d)
    else:
        print("-", d.get("category"), "|", (d.get("description") or "")[:150])
