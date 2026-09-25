import re
import requests

URL = "https://www.hangseng.com/en-hk/rates/foreign-currency-tt-exchange-rates/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

res = requests.get(URL, headers=HEADERS, timeout=20)
html_text = res.text
print("Status:", res.status_code, "Length:", len(html_text))

# Look for likely data endpoints
patterns = [
    r'[\'"]([^\'" ]*rate[^\'" ]*\.json[^\'" ]*)[\'"]',
    r'[\'"]([^\'" ]*\.json[^\'" ]*)[\'"]',
    r'(https?://[^\'" ]*rate[^\'" ]*)',
    r'fetch\(([^)]*)\)',
    r'\.ajax\(\{[^}]*url\s*:\s*[\'"]([^\'"]+)[\'"]',
    r'data-src=[\'"]([^\'"]+)[\'"]',
]
for p in patterns:
    matches = re.findall(p, html_text)
    uniq = list(dict.fromkeys(matches))
    print(f"\nPattern {p!r}: {len(matches)} matches, {len(uniq)} unique")
    for m in uniq[:10]:
        print(" -", m)

# Look for a div/table specific to "current rate" (not the chart section) - search near "Buying" "Selling"
for kw in ["Buying", "Selling", "TT Buying", "TT Selling", "We Buy", "We Sell", "rvp_", "portlet", "ibmportal"]:
    idx = html_text.find(kw)
    print(f"\nKeyword {kw!r} found at index: {idx}")
    if idx != -1:
        print(html_text[max(0, idx-150):idx+250])

# Look at all <script src=...> tags
scripts = re.findall(r'<script[^>]*src="([^"]+)"', html_text)
print(f"\n<script src> tags: {len(scripts)}")
for s in scripts:
    print(" -", s)
