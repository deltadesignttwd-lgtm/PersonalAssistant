import requests
import json

res = requests.get("https://api.tfl.gov.uk/Road/all/Disruption", timeout=30)
print("status:", res.status_code, "len:", len(res.text))
data = res.json()
print("total disruptions:", len(data))

categories = sorted(set(d.get("category", "") for d in data))
subcategories = sorted(set(d.get("subCategory", "") for d in data))
print("\nDistinct categories:", categories)
print("\nDistinct subCategories:", subcategories)

keywords = ["demonstration", "march", "procession", "protest", "parade", "rally", "ceremonial"]
print("\n===== Entries matching event keywords =====")
matches = []
for d in data:
    text = f"{d.get('comments','')} {d.get('currentUpdate','')}".lower()
    if any(kw in text for kw in keywords):
        matches.append(d)

print(f"found {len(matches)} matching entries\n")
for d in matches[:10]:
    print("---")
    print("id:", d.get("id"))
    print("category/subCategory:", d.get("category"), "/", d.get("subCategory"))
    print("severity:", d.get("severity"), "status:", d.get("status"), "levelOfInterest:", d.get("levelOfInterest"))
    print("corridorIds:", d.get("corridorIds"))
    print("location:", d.get("location"))
    print("startDateTime:", d.get("startDateTime"), "endDateTime:", d.get("endDateTime"))
    print("comments:", d.get("comments", "")[:400])
    print()

# How far in the future do startDateTime values go? (for Friday-evening lookahead feasibility)
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
future_starts = []
for d in data:
    s = d.get("startDateTime")
    if not s:
        continue
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        continue
    if dt > now:
        future_starts.append((dt, d.get("id"), d.get("category"), d.get("location")))
future_starts.sort()
print(f"\n===== {len(future_starts)} disruptions with a FUTURE startDateTime (planned ahead) =====")
for dt, id_, cat, loc in future_starts[:15]:
    print(dt.isoformat(), id_, cat, loc)
