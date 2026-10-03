import re
import json
import requests
from datetime import datetime

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
    res = requests.get(url, headers=HEADERS, timeout=20)
    html = res.text

    ld_blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
    item_list = None
    for block in ld_blocks:
        data = json.loads(block)
        if data.get("@type") == "ItemList":
            item_list = data
            break

    if not item_list:
        print("NO ItemList FOUND")
        continue

    items = item_list.get("itemListElement", [])
    print(f"itemListElement count: {len(items)}")
    for it in items:
        event = it.get("item", {})
        name_ = event.get("name")
        url_ = event.get("url")
        start = event.get("startDate")
        end = event.get("endDate")
        try:
            parsed = datetime.fromisoformat(start)
            weekday = parsed.strftime("%A")
        except Exception as e:
            weekday = f"PARSE ERROR: {e}"
        print(f"- name={name_!r} start={start!r} weekday={weekday} url={url_!r}")
