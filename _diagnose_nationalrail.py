from playwright.sync_api import sync_playwright

URL = (
    "https://www.nationalrail.co.uk/journey-planner/?type=single&origin=LEW"
    "&destination=CHX&leavingType=departing&leavingDate=161126&leavingHour=08"
    "&leavingMin=10&adults=1&extraTime=0"
)

STATIC_EXT = (".js", ".css", ".woff", ".woff2", ".png", ".svg", ".jpg", ".ico")

captured = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    def on_response(response):
        url = response.url
        if any(url.split("?")[0].endswith(ext) for ext in STATIC_EXT):
            return
        if "nationalrail" not in url and "ojp" not in url:
            return
        ctype = response.headers.get("content-type", "")
        body_snippet = ""
        if "json" in ctype.lower():
            try:
                body_snippet = response.text()[:800]
            except Exception as e:
                body_snippet = f"<could not read body: {e}>"
        captured.append((response.request.method, url, response.status, ctype, body_snippet))

    page.on("response", on_response)
    try:
        page.goto(URL, wait_until="networkidle", timeout=45000)
    except Exception as e:
        print("goto/networkidle issue (continuing anyway):", e)
    page.wait_for_timeout(6000)

    print(f"Page title: {page.title()}")
    print(f"Captured {len(captured)} non-static nationalrail/ojp responses:\n")
    for method, url, status, ctype, body in captured:
        print(f"{method} {status} [{ctype}] {url}")
        if body:
            print("  BODY SNIPPET:", body.replace('\n', ' ')[:800])
        print()

    browser.close()
