import json
import requests

LAT = 51.4615
LON = -0.0102

HEADERS = {
    "User-Agent": "PersonalAssistant-diagnostic/1.0 github.com/deltadesignttwd-lgtm/PersonalAssistant",
}

url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}"
res = requests.get(url, headers=HEADERS, timeout=15)
print("STATUS:", res.status_code)
print("HEADERS:", dict(res.headers))
data = res.json()
timeseries = data.get("properties", {}).get("timeseries", [])
print("Number of timeseries entries:", len(timeseries))
print("\nFirst entry (current):")
print(json.dumps(timeseries[0], indent=2))
print("\nSecond entry:")
print(json.dumps(timeseries[1], indent=2))

print("\n===== Deriving today's min/max temp and max precipitation prob/amount over next ~24h =====")
import datetime
now = datetime.datetime.now(datetime.timezone.utc)
window_end = now + datetime.timedelta(hours=24)
temps = []
precip_amounts = []
precip_probs = []
for entry in timeseries:
    t = datetime.datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
    if t > window_end:
        continue
    details = entry.get("data", {}).get("instant", {}).get("details", {})
    if "air_temperature" in details:
        temps.append(details["air_temperature"])
    next1 = entry.get("data", {}).get("next_1_hours", {})
    if next1:
        d = next1.get("details", {})
        if "precipitation_amount" in d:
            precip_amounts.append(d["precipitation_amount"])
        prob = d.get("probability_of_precipitation")
        if prob is not None:
            precip_probs.append(prob)

print("temps count:", len(temps), "min:", min(temps) if temps else None, "max:", max(temps) if temps else None)
print("precip_amounts (next_1_hours) count:", len(precip_amounts), "max:", max(precip_amounts) if precip_amounts else None)
print("precip_probs count:", len(precip_probs), "max:", max(precip_probs) if precip_probs else None)
