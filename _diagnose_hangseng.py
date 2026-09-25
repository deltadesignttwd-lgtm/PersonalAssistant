import requests

URL = "https://www.hangseng.com/en-hk/rates/foreign-currency-tt-exchange-rates/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

print("=== Plain requests.get (no headers) ===")
try:
    res = requests.get(URL, timeout=15)
    print("Status:", res.status_code)
    print("Length:", len(res.text))
    print(res.text[:1500])
except Exception as e:
    print("Error:", e)

print("\n=== requests.get with browser-like headers ===")
try:
    res = requests.get(URL, headers=HEADERS, timeout=15)
    print("Status:", res.status_code)
    print("Length:", len(res.text))
    lower = res.text.lower()
    print("Contains 'captcha':", "captcha" in lower)
    print("Contains 'gbp':", "gbp" in lower)
    print("Contains 'pound':", "pound" in lower)
    print("Contains 'access denied':", "access denied" in lower)
    print("Contains 'human verification':", "human verification" in lower)
    print("Contains '<table':", "<table" in lower)
    print("Contains 'json':", "application/json" in lower)

    print("\n--- First 3000 chars ---")
    print(res.text[:3000])

    # find GBP occurrences with context
    idx = 0
    count = 0
    text = res.text
    lower_text = text.lower()
    while count < 5:
        pos = lower_text.find("gbp", idx)
        if pos == -1:
            break
        print(f"\n--- GBP occurrence at {pos} ---")
        print(text[max(0, pos-200):pos+300])
        idx = pos + 1
        count += 1
except Exception as e:
    print("Error:", e)
