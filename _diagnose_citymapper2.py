import json
import re
from playwright.sync_api import sync_playwright

URL = (
    "https://citymapper.com/directions?lang=en&startcoord=51.452024%2C-0.000944"
    "&endcoord=51.510131%2C-0.121783&startname=Hither+Green&endname=Virgin+Active+Strand"
    "&endaddress=Strand%2C+London%2C+UK"
)

STATIC_EXT_RE = re.compile(r"\.(js|css|png|jpg|jpeg|svg|woff2?|ico|gif|webp)(\?|$)")

interesting_responses = []


def on_response(response):
    url = response.url
    if "citymapper.com" not in url and "citymapper" not in url:
        return
    if STATIC_EXT_RE.search(url):
        return
    try:
        ctype = response.headers.get("content-type", "")
    except Exception:
        ctype = ""
    interesting_responses.append((response.status, ctype, url))


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("response", on_response)

    page.goto(URL, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(5000)  # give client-side JS extra time to fetch route data

    print(f"Captured {len(interesting_responses)} non-static citymapper responses:\n")
    for status, ctype, url in interesting_responses:
        print(f"[{status}] {ctype} -> {url}")

    print("\n--- Attempting to fetch JSON bodies for likely candidates ---")
    for status, ctype, url in interesting_responses:
        if "json" in ctype.lower():
            print(f"\nURL: {url}")
            try:
                resp = page.request.get(url)
                body = resp.text()
                print(body[:1500])
            except Exception as e:
                print(f"(failed to re-fetch: {e})")

    print("\n--- Page visible text (first 4000 chars) ---")
    body_text = page.inner_text("body")
    print(body_text[:4000])

    print("\n--- Page title ---")
    print(page.title())

    browser.close()
