import re
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

URLS = {
    "pub_quiz": "https://www.eventbrite.com/cc/the-lesbian-pub-quiz-3867043/",
    "speed_dating": "https://www.eventbrite.com/cc/lesbian-speed-dating-3678189/",
}

for name, url in URLS.items():
    print(f"\n{'=' * 60}\n{name}: {url}\n{'=' * 60}")
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        print(f"status: {res.status_code}, length: {len(res.text)}")
    except Exception as e:
        print(f"FETCH ERROR: {e}")
        continue

    html = res.text
    for marker in ["captcha", "Human Verification", "awswaf", "challenge", "__NEXT_DATA__", "application/ld+json"]:
        print(f"'{marker}' present: {marker in html}")

    ld_blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
    print(f"JSON-LD blocks: {len(ld_blocks)}")
    for i, block in enumerate(ld_blocks[:3]):
        print(f"  [{i}] {block[:400]}")

    next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if next_data:
        print(f"__NEXT_DATA__ length: {len(next_data.group(1))}")
        print(next_data.group(1)[:500])

    print("\n--- first 1500 chars ---")
    print(html[:1500])
