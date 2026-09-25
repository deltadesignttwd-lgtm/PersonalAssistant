import requests

URL = "https://rbwm-api.hsbc.com.hk/pws-hk-hase-rates-papi-prod-proxy/v1/fxtt-exchange-rates"

print("=== Plain GET, no special headers ===")
try:
    res = requests.get(URL, timeout=15)
    print("Status:", res.status_code)
    print("Length:", len(res.text))
    print(res.text[:2000])
except Exception as e:
    print("Error:", e)

print("\n=== GET with headers matching the site's own JS ===")
headers = {
    "X-HSBC-Locale": "en_HK",
    "X-HSBC-Src-Device-Id": "",
    "X-HSBC-Src-UserAgent": "",
    "X-HSBC-Channel-Id": "PWS",
    "X-HSBC-Chnl-CountryCode": "HK",
    "Accept-Language": "en-HK",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.hangseng.com/en-hk/rates/foreign-currency-tt-exchange-rates/",
}
try:
    res = requests.get(URL, headers=headers, timeout=15)
    print("Status:", res.status_code)
    print("Length:", len(res.text))
    print(res.text[:3000])
    try:
        data = res.json()
        print("\nTop-level keys:", list(data.keys()))
        rates = data.get("fxttExchangeRates", [])
        print("Number of rate entries:", len(rates))
        gbp = [r for r in rates if r.get("ccyDisplayCode") == "GBP"]
        print("\nGBP entry:", gbp)
    except Exception as e:
        print("JSON parse error:", e)
except Exception as e:
    print("Error:", e)
