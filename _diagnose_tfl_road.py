import requests

print("===== /Road/all (raw) =====")
res = requests.get("https://api.tfl.gov.uk/Road/all", timeout=20)
print("status:", res.status_code)
print("body[:1000]:", res.text[:1000])

print("\n===== /Road/a406 (known real road id from TfL docs) =====")
res = requests.get("https://api.tfl.gov.uk/Road/a406", timeout=20)
print("status:", res.status_code)
print("body[:500]:", res.text[:500])

print("\n===== /Road/a406/Disruption =====")
res = requests.get("https://api.tfl.gov.uk/Road/a406/Disruption", timeout=20)
print("status:", res.status_code)
print("body[:1000]:", res.text[:1000])

print("\n===== /Road/all/Disruption (all roads' disruptions) =====")
res = requests.get("https://api.tfl.gov.uk/Road/all/Disruption", timeout=25)
print("status:", res.status_code)
body = res.text
print("len:", len(body))
print("body[:1500]:", body[:1500])

print("\n===== searching /Road/all/Disruption for 'red route' / 'central london' mentions =====")
if "red route" in body.lower():
    idx = body.lower().find("red route")
    print("FOUND 'red route' context:", body[max(0,idx-200):idx+200])
if "central london" in body.lower():
    idx = body.lower().find("central london")
    print("FOUND 'central london' context:", body[max(0,idx-200):idx+200])
