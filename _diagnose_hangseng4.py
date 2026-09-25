import re
import requests

BASE = "https://www.hangseng.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

JS_URLS = [
    "/etc.clientlibs/hase/clientlibs/clientlib-rates/ttTable.min.45642877ee37172234be3099194698d2.js",
    "/etc.clientlibs/hase/clientlibs/pws/common/rwd-services/clientlib-rwd-service-api.min.dc8c3424ceda1eef5682d97e385d9dd6.js",
    "/etc.clientlibs/hase/clientlibs/clientlib-commonApiUrl.min.394dddf44ff2f8951c6f93f6b3adbddb.js",
]

for path in JS_URLS:
    url = BASE + path
    print(f"\n=== {url} ===")
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        print("Status:", res.status_code, "Length:", len(res.text))
        text = res.text
        # Look for URL-like strings, especially api/rates paths
        api_matches = re.findall(r'[\'"](/[a-zA-Z0-9_\-./]*(?:api|rate|tt)[a-zA-Z0-9_\-./]*)[\'"]', text, re.I)
        uniq = list(dict.fromkeys(api_matches))
        print(f"Potential API/rate paths ({len(uniq)}):")
        for m in uniq[:20]:
            print(" -", m)
        print("\n--- First 2000 chars ---")
        print(text[:2000])
    except Exception as e:
        print("Error:", e)
