from playwright.sync_api import sync_playwright

URL = "https://www.eventbrite.co.uk/d/united-kingdom--london/lesbian-events/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1366, "height": 900},
    )
    page = context.new_page()
    print("Navigating...")
    resp = page.goto(URL, wait_until="domcontentloaded", timeout=30000)
    print("Initial status:", resp.status if resp else None)

    # Give any WAF JS challenge time to run and redirect/reload
    page.wait_for_timeout(8000)
    print("URL after wait:", page.url)
    print("Title:", page.title())

    html = page.content()
    print("HTML length:", len(html))
    print("Contains 'captcha':", "captcha" in html.lower())
    print("Contains 'search-event-card':", "search-event-card" in html.lower())
    print("Contains 'eventbrite-testid':", "eventbrite-testid" in html.lower())

    # Dump a chunk of the body for inspection
    print("\n--- First 3000 chars of HTML ---")
    print(html[:3000])

    # Try to find likely event card elements generically
    for sel in [
        "[data-testid='search-event-card']",
        "[class*='event-card']",
        "article",
        "li[class*='search-result']",
    ]:
        count = page.locator(sel).count()
        print(f"Selector {sel!r}: {count} matches")

    browser.close()
