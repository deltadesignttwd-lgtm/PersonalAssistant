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

# Print all <table ...> ... </table> blocks (may be more than one)
tables = re.findall(r'<table.*?</table>', html_text, re.S)
print(f"\nNumber of <table> blocks: {len(tables)}")
for i, t in enumerate(tables):
    print(f"\n=== table {i} (length {len(t)}) ===")
    print(t[:3000])

# Find <form ...> blocks to see action/method and inspect the currency select's context
forms = re.findall(r'<form[^>]*>', html_text)
print(f"\nForm tags found: {len(forms)}")
for f in forms:
    print(" -", f)

# Look at what's "selected" in the currency dropdown (default currency shown)
select_blocks = re.findall(r'<select[^>]*id="[^"]*"[^>]*>.*?</select>', html_text, re.S)
print(f"\nNumber of <select> blocks: {len(select_blocks)}")
for sb in select_blocks[:3]:
    print("---")
    print(sb[:1500])

# Check for query-string patterns like ?cur= or ?ccy= in any links/scripts
qs_matches = re.findall(r'[?&](cur|ccy|currency)=[A-Za-z]{3}', html_text)
print("\nQuery-string currency param matches:", qs_matches[:10])
