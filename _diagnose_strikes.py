from playwright.sync_api import sync_playwright

URL = "https://tfl.gov.uk/status-updates/strikes"

captured = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    def on_response(response):
        url = response.url
        if url.split("?")[0].endswith((".js", ".css", ".woff", ".woff2", ".png", ".svg", ".jpg", ".ico")):
            return
        ctype = response.headers.get("content-type", "")
        body_snippet = ""
        if "json" in ctype.lower():
            try:
                body_snippet = response.text()[:500]
            except Exception as e:
                body_snippet = f"<could not read body: {e}>"
        captured.append((response.request.method, url, response.status, ctype, body_snippet))

    page.on("response", on_response)
    try:
        page.goto(URL, wait_until="networkidle", timeout=45000)
    except Exception as e:
        print("goto/networkidle issue (continuing anyway):", e)
    page.wait_for_timeout(5000)

    print("Page title:", page.title())
    print("Final URL:", page.url)

    body_text = page.inner_text("body")
    print("\n===== Page body text (first 3000 chars) =====")
    print(body_text[:3000])

    print(f"\n===== Captured {len(captured)} non-static responses =====")
    for method, url, status, ctype, body in captured:
        print(f"{method} {status} [{ctype}] {url}")
        if body:
            print("  BODY:", body.replace("\n", " ")[:500])

    browser.close()
