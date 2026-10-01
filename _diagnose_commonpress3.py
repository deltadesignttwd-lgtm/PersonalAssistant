from playwright.sync_api import sync_playwright

URL = "https://www.commonpress.co.uk/upcoming-events-new"

captured = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    def on_response(response):
        url = response.url
        if any(kw in url.lower() for kw in ["event", "calendar", "query", "wixapis"]):
            captured.append((response.request.method, url, response.status))

    page.on("response", on_response)
    page.goto(URL, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(5000)

    print(f"Captured {len(captured)} relevant responses:\n")
    for method, url, status in captured:
        print(f"{method} {status} {url}")

    # Also dump visible text content to see if events rendered client-side
    print("\n--- page text content (first 3000 chars containing 'event' context) ---")
    body_text = page.inner_text("body")
    idx = body_text.lower().find("upcoming")
    if idx != -1:
        print(body_text[max(0, idx - 200):idx + 3000])
    else:
        print(body_text[:3000])

    browser.close()
