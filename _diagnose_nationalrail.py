import json
from playwright.sync_api import sync_playwright
import requests

URL = (
    "https://www.nationalrail.co.uk/journey-planner/?type=single&origin=LEW"
    "&destination=CHX&leavingType=departing&leavingDate=161126&leavingHour=08"
    "&leavingMin=10&adults=1&extraTime=0"
)

captured_request = {}
full_response_body = {}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    def on_request(request):
        if "jpservices.nationalrail.co.uk/journey-planner" in request.url and request.method == "POST":
            captured_request["url"] = request.url
            captured_request["headers"] = dict(request.headers)
            captured_request["post_data"] = request.post_data

    def on_response(response):
        if "jpservices.nationalrail.co.uk/journey-planner" in response.url:
            try:
                full_response_body["body"] = response.text()
                full_response_body["status"] = response.status
            except Exception as e:
                full_response_body["error"] = str(e)

    page.on("request", on_request)
    page.on("response", on_response)
    page.goto(URL, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(5000)
    browser.close()

print("===== Captured request to jpservices =====")
print("URL:", captured_request.get("url"))
print("HEADERS:")
for k, v in (captured_request.get("headers") or {}).items():
    print(f"  {k}: {v}")
print("POST DATA:")
print(captured_request.get("post_data"))

print("\n===== Full response body =====")
print("STATUS:", full_response_body.get("status"))
body = full_response_body.get("body", "")
print("LENGTH:", len(body))
try:
    parsed = json.loads(body)
    print("outwardJourneys count:", len(parsed.get("outwardJourneys", [])))
    for j in parsed.get("outwardJourneys", []):
        sched_dep = j.get("timetable", {}).get("scheduled", {}).get("departure")
        rt_dep = j.get("timetable", {}).get("realtime", {}).get("departure")
        print(f"  journey id={j.get('id')} status={j.get('status')} rawStatus={j.get('rawStatus')} "
              f"delayInMinutes={j.get('delayInMinutes')} scheduled_dep={sched_dep} realtime_dep={rt_dep}")
except Exception as e:
    print("Could not parse JSON:", e)
    print(body[:3000])

print("\n===== Now trying plain requests.post() with the SAME payload, NO browser/cookies =====")
if captured_request.get("post_data"):
    plain_headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Origin": "https://www.nationalrail.co.uk",
        "Referer": "https://www.nationalrail.co.uk/",
    }
    try:
        res = requests.post(
            "https://jpservices.nationalrail.co.uk/journey-planner",
            data=captured_request["post_data"],
            headers=plain_headers,
            timeout=20,
        )
        print("STATUS:", res.status_code)
        print("BODY (first 1000 chars):", res.text[:1000])
    except Exception as e:
        print("Plain requests.post failed:", e)
