import requests
from datetime import datetime, timezone

res = requests.get("https://api.tfl.gov.uk/Road/all/Disruption", timeout=30)
data = res.json()
now = datetime.now(timezone.utc)
print("fetched at (UTC):", now.isoformat())
print("total disruptions:", len(data))

statuses = sorted(set(d.get("status", "") for d in data))
print("distinct status values:", statuses)

# For every disruption, print how far in the future/past startDateTime and endDateTime are
future_end = []
for d in data:
    e = d.get("endDateTime")
    if not e:
        continue
    try:
        edt = datetime.fromisoformat(e.replace("Z", "+00:00"))
    except ValueError:
        continue
    if edt > now:
        future_end.append((edt, d.get("startDateTime"), d.get("status"), d.get("category"), d.get("subCategory"), d.get("location")))

future_end.sort()
print(f"\n{len(future_end)} disruptions whose END time is still in the future (i.e. ongoing or scheduled to continue):")
for edt, start, status, cat, sub, loc in future_end[:20]:
    print(f"  end={edt.isoformat()} start={start} status={status} cat={cat}/{sub} loc={loc}")

# Specifically: does any entry have a startDateTime MORE than a few hours in the future?
# (i.e. genuinely not-yet-started, which would prove forward-looking visibility works)
print("\nEntries with startDateTime > now + 2 hours (would prove true advance notice):")
found_any = False
for d in data:
    s = d.get("startDateTime")
    if not s:
        continue
    try:
        sdt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        continue
    if (sdt - now).total_seconds() > 7200:
        found_any = True
        print(f"  start={sdt.isoformat()} status={d.get('status')} cat={d.get('category')}/{d.get('subCategory')} loc={d.get('location')}")
if not found_any:
    print("  NONE - every disruption currently in the feed has already started (or starts within 2h).")
