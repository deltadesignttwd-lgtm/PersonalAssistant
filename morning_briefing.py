import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

LOCAL_TZ = ZoneInfo("Europe/London")

# Lewisham 經緯度 (51.4615, -0.0102)
LAT = 51.4615
LON = -0.0102

# Hang Seng Bank 的 TT 匯率頁面本身沒有把數字寫進靜態 HTML；頁面的
# clientlib-rates/ttTable.js 揭露了背後實際呼叫的公開 JSON API，直接呼叫即可，
# 不需要瀏覽器渲染。
HANGSENG_TT_RATES_PAGE_URL = "https://www.hangseng.com/en-hk/rates/foreign-currency-tt-exchange-rates/"
HANGSENG_TT_RATES_API_URL = "https://rbwm-api.hsbc.com.hk/pws-hk-hase-rates-papi-prod-proxy/v1/fxtt-exchange-rates"

# 只有在 Bank Buy 匯率達到這個門檻時，才在每日晨報中顯示這個區塊
GBP_HKD_BUY_RATE_THRESHOLD = 10.5

# Citymapper 路線資訊 (Lewisham 至 Virgin Active Strand)
CITYMAPPER_GYM_URL = "https://citymapper.com/trip/signature?signature=eJx9U9Fu2jAU%2FZXIryPF145J4G2qkDqtYlNZ14eqskxswGuwmWNKJ8S%2F104gSzRpb%2FG9x%2Bcen3tyQqVwaJYAMJKPEiQPTnhtTSgRVkCoKCPD4YSElE7VdfhGS%2B%2BEkaPk3hppzSh5%2FIoCsLTWyabP4IYBBgqjFN8AgbygEWDETsX2T%2B022iSfS6%2FfVNKSoXMA%2FHJcG6neAwiHY6U2ke75hKSuvTClaoQSNtQ5pSTKLC%2BTs0lWNIMxkDyO1YaH2xcwwuMpjtWdlY2Yo6he47nu7rN82lzHGWSx4y1X79rH9r066nordnxOMWVFFH3qSwHIcGcZut0Kp83m1tlgWyhvlZBH8Se0gsaehGhAHQaEkrMHr7hubhbar3xGi4ZXVA9CV8s5eokyvXADKY12b%2Fe8tAcTO9m1cGX5Xgm%2Ftm7HO%2FV9Xi6fIkUH6oseANFL%2B9q%2Fq8gIHm6CMtbfRMzANQJtAtbO7jozB5PmiwcO%2FJKFf5ZGxoDZf7fGcEFpO4sRQOfo1d7pUvG9atXSRq1Tmwvn4TWtmvxefQ9auFO%2FD6r2wbsIWdMcJipbpWwFeZrh9SRdsbxMczllUzrJlaQC9ZZyGv4DMUlwyRItCtb%2FB5ZzoAm7e2xy73VbJJhMUlykBH5ANsvIjBafMMwwHi%2B%2BPX1Z3kWCN%2BXq9gXs%2FAF%2FCxLH"

# Citymapper 路線資訊 (平日通勤: Home → Bank [DLR] → Old Street [Northern line]
# → Frank Reynolds Architects, Shepherdess Walk)。解碼確認為完整路線。
# 原本還有另一條經 Canary Wharf [DLR] → Liverpool Street [Elizabeth line] 的路線，
# 使用者已決定改用這條經 Bank/Old Street 的路線作為唯一常用路線，故移除前者。
CITYMAPPER_OFFICE_URL = "https://citymapper.com/trip/signature?signature=eJyNlNtu4jAQhl8l8u2S4kMSHO52VVZdLaKr0oqLqorceIAswWYds22FePfaCaQEtIc7PDP%2B558PT3YoFwYNA0JTznsBklsjbKGVCzFOIhcBJd1hh4SUBqrK%2FUbTJWyWYKQ7BjNRrnrBWCupVS94%2BI7clVxrI%2BvKmFzFTpkNeiG%2BwinFnPsCJdbg01%2BNUKvgDt6ULmUVfDb5srCQ2wrtXdVPkxVKwqurHLhjCQuv%2BbhDsqisULmXIITGXdspo951fmgfJREndXdCB753oTJ3%2B1CMcD%2FFPrrWsnb04sbx56q9Hw%2FS%2BjqOSOQzVmfwWlifHsNLUS3FOhsxzGLuTe9OrZCE45Yg%2BuJm9QJLEPJFvLlQxPBJa%2BtgVE7YhYzeWsiKmuEjuh7foSfvyQrT6VsbtXqT5XqrbN3wGDne%2FVEKO9dmnbVevZqrahPeVnad3aOnxv4HW9wF28xy5BIT5kB7MJyn9BIs6fO%2Fgz0TOGdHoxN0t6WcWgNgu%2Fxowv6H30Qb656r6kI8%2Fh0dgOyP%2FGpMk0xOOvBaY3VqdskwYWfPM8G8g9Fvx2E5SOK150av2xf2oT9il4xpn%2FwLMk0axIOUob2ff2OKHLINNPYY8ZQNLA6K21VY1qt8pFioRWbg1xYq65j4koQM8ucc0%2FA5wjKMaCLCFCQJY8ZBcgBM8BydgN51Pwd%2Bn8hhoxjn8ennYDoiLIhvHurtt0UTpJgmIeYhTe4pHbJ4SMgnTIYY9ye3s2%2FTGy%2FwG0zVTBDv3wGqG18e"

# Citymapper 路線資訊 (平日下班: Frank Reynolds Architects, Shepherdess Walk → walk to
# Old Street → Old Street [Northern line] → Bank → Bank [DLR] → Lewisham → home)。
# 解碼確認為 CITYMAPPER_OFFICE_URL 的反方向，使用同樣兩條 TfL line（Northern/DLR）。
CITYMAPPER_HOME_FROM_OFFICE_URL = "https://citymapper.com/trip/signature?signature=eJyNlF1v2yAUhv%2BKxe3ihg9%2F4Nx1aqZNi9Kp2dSLqkLMkMSLAxkmS6so%2F32AnQ%2B3Wrs7n3PgfQ%2BPOexByQ0YRQgjSgcREFvDbaWVS%2BEixS4jlXDBHpRaG9G4T5CiqyRLMpoPYngFEc4pAW6h4mvpyxO5q5olX4ODS%2F4yrFJCPrkCcWEtF17iYQ9E1ViuSr8jI6TvnMFgXHZmKc6CE82LYFQp5vZ2awEcIgp9eq1F8N%2FxeuXj5ry%2FoCQoFBhlvmQ1k0%2BV9fXbWsyskdKyMfEd73sIEngiAD5yFXSXkosdf%2FbQKLzwtYarxom6lNFbK1kVcD2AqTZ2KY0Cj74ry03fOPRq9YaVeqtsByokjgLfam7n2qzZudkpEzO%2F8VTy3bXZx%2FYUZ76wTzc0fYaLCMEtXlrg13jR8D26fYGXCFF%2ByfB0N3ocCfwvjjeTuz7C4x%2Fp0UPpP%2FEFRjdMjHvkjj2xoP8SXvImPT8HRTcG7RTMjV6fLtdJekwgSelruniYvU3XGVB0nDNw8MffmKqUbCPb%2FgjyDRm56BS3q7jWSrig41epBTPy91Y21hEJsjQrUyKKeE4xjxOZ05iTMolLkeOfPCeCYAwuOO8BF8LIJgz%2FbCk37jILF0b3rttBNAl2g%2BjHV7%2Bp90yEycu70XP34%2FKZ%2BOR%2B8yq6k89K16KJrk25rKwsbRPeDVu1qzDEWYxgDMl3REYJHiXoA0QjCIfT2%2Fsvs89e8Y80TXv69PAXRWdfxg%3D%3D"

# TfL 官方的 Central London Red Routes 即時路況頁面。這個頁面本身被 bot 驗證
# (Cloudflare 一類的 WAF) 擋下，plain requests 拿到的是 403 "Verification
# required" 頁面，無法直接 scrape；只用來當人工檢查的備用連結。
TFL_CENTRAL_LONDON_TRAFFIC_STATUS_URL = (
    "https://tfl.gov.uk/traffic/status/?dateTypeSelect=Now"
    "&corridorIds=Central%20London%20Red%20Routes"
)


def _parse_iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))


# 低於這個價格（p/kWh）的時段會在晨報中被列為「便宜時段」
OCTOPUS_CHEAP_THRESHOLD_P_PER_KWH = 20.0


def get_octopus_agile_rates():
    """取得 Lewisham（London, Region _C）Octopus Agile 官方電價"""
    url = "https://api.octopus.energy/v1/products/AGILE-24-10-01/electricity-tariffs/E-1R-AGILE-24-10-01-C/standard-unit-rates/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json().get('results', [])

        if not data:
            return "N/A", "N/A", "N/A"

        now = datetime.now(timezone.utc)

        # API 回傳順序不保證是「現在」在前，因此用時間區間找出真正的當前電價
        current_entry = next(
            (r for r in data if _parse_iso(r['valid_from']) <= now < _parse_iso(r['valid_to'])),
            None
        )
        current_rate = f"{round(current_entry['value_inc_vat'], 2)} p/kWh" if current_entry else "N/A"

        window_end = now + timedelta(hours=24)
        upcoming = sorted(
            (r for r in data if now <= _parse_iso(r['valid_from']) < window_end),
            key=lambda r: _parse_iso(r['valid_from'])
        )
        if not upcoming:
            upcoming = sorted(data, key=lambda r: _parse_iso(r['valid_from']))

        # 1. 未來 24 小時內價格最低的那一個時段（半小時 slot，不做任何合併）
        if upcoming:
            cheapest = min(upcoming, key=lambda r: r['value_inc_vat'])
            cheapest_start_local = _parse_iso(cheapest['valid_from']).astimezone(LOCAL_TZ).strftime("%H:%M")
            cheapest_end_local = _parse_iso(cheapest['valid_to']).astimezone(LOCAL_TZ).strftime("%H:%M")
            cheapest_slot = f"{cheapest_start_local} - {cheapest_end_local} ({round(cheapest['value_inc_vat'], 2)} p/kWh)"
        else:
            cheapest_slot = "N/A"

        # 2. 未來 24 小時內所有低於 OCTOPUS_CHEAP_THRESHOLD_P_PER_KWH 的時段，把首尾相接
        # 的連續半小時 slot 合併成一段區間（可能是半小時、一小時或更長）
        cheap_windows = []
        open_window = None  # (window_start, window_end, [prices])
        for r in upcoming:
            slot_start = _parse_iso(r['valid_from'])
            slot_end = _parse_iso(r['valid_to'])
            if r['value_inc_vat'] < OCTOPUS_CHEAP_THRESHOLD_P_PER_KWH:
                if open_window is not None and open_window[1] == slot_start:
                    open_window = (open_window[0], slot_end, open_window[2] + [r['value_inc_vat']])
                else:
                    if open_window is not None:
                        cheap_windows.append(open_window)
                    open_window = (slot_start, slot_end, [r['value_inc_vat']])
            elif open_window is not None:
                cheap_windows.append(open_window)
                open_window = None
        if open_window is not None:
            cheap_windows.append(open_window)

        if cheap_windows:
            cheap_windows_str = ", ".join(
                f"{start.astimezone(LOCAL_TZ).strftime('%H:%M')} - {end.astimezone(LOCAL_TZ).strftime('%H:%M')}"
                f" (avg {round(sum(prices) / len(prices), 2)} p/kWh)"
                for start, end, prices in cheap_windows
            )
        else:
            cheap_windows_str = "None"

        return current_rate, cheapest_slot, cheap_windows_str
    except Exception as e:
        print(f"Octopus API 錯誤: {e}")
        return "擷取失敗", "擷取失敗", "擷取失敗"


def get_weather_forecast(max_attempts=3):
    """透過 Open-Meteo API 取得 Lewisham 天氣預報，暫時性錯誤（如 503）會重試"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m&hourly=temperature_2m,precipitation_probability&forecast_days=1&timezone=Europe%2FLondon"
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()

            curr_temp = round(data['current']['temperature_2m'])
            hourly_temps = data['hourly']['temperature_2m']
            hourly_rain = data['hourly']['precipitation_probability']

            min_temp = round(min(hourly_temps))
            max_temp = round(max(hourly_temps))
            max_rain_prob = max(hourly_rain)

            if max_rain_prob >= 50:
                rain_summary = f"⚠️ 今天降雨機率高（最高 {max_rain_prob}%）！記得帶傘 🌧️"
            elif max_rain_prob >= 20:
                rain_summary = f"🌦️ 可能有局部短暫雨（最高 {max_rain_prob}% 機率）。"
            else:
                rain_summary = "☀️ 今天預計無明顯降雨。"

            return f"{curr_temp}°C", f"{min_temp}°C ~ {max_temp}°C", rain_summary
        except requests.exceptions.RequestException as e:
            # 網路/HTTP 錯誤（例如今天實際發生的 503）視為暫時性，重試
            last_error = e
            print(f"Weather API 錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt < max_attempts:
                time.sleep(3 * attempt)
        except Exception as e:
            # 非網路性錯誤（例如回應格式異常）不重試，直接視為失敗
            last_error = e
            break

    print(f"Weather API 最終失敗: {last_error}")
    return "N/A", "N/A", "擷取失敗"


def get_gbp_hkd_tt_rate():
    """取得 Hang Seng Bank 官方 GBP/HKD TT（電匯）匯率，失敗時回傳 None"""
    try:
        res = requests.get(HANGSENG_TT_RATES_API_URL, timeout=15)
        res.raise_for_status()
        data = res.json()
        rates = data.get("fxttExchangeRates", [])
        gbp = next((r for r in rates if r.get("ccyDisplayCode") == "GBP"), None)
        if gbp is None:
            raise RuntimeError("API 回應中找不到 GBP 匯率")

        last_update_raw = data.get("lastUpdateTime")
        last_update = _parse_iso(last_update_raw).strftime("%Y-%m-%d %H:%M HKT") if last_update_raw else "N/A"

        return {
            "buy": gbp.get("ttBuyRate"),
            "sell": gbp.get("ttSellRate"),
            "last_update": last_update,
        }
    except Exception as e:
        print(f"Hang Seng GBP/HKD 匯率擷取失敗: {e}")
        return None


def _get_tfl_line_disruptions(line_ids):
    """查詢指定 TfL line id 的即時狀態，回傳「非正常服務」狀態的結構化清單（可能為空）。
    每筆為 {"line": 路線名稱, "severity": statusSeverityDescription, "reason": reason 文字}。
    severity 直接用 TfL API 本身的結構化欄位（例如 "Severe Delays"/"Minor Delays"/
    "Part Suspended"），不用字串比對去猜測嚴重程度。"""
    ids = ",".join(line_ids)
    tfl_url = f"https://api.tfl.gov.uk/Line/{ids}/Status"
    res = requests.get(tfl_url, timeout=10)
    res.raise_for_status()
    lines = res.json()

    disruptions = []
    for line in lines:
        for status in line.get('lineStatuses', []):
            status_desc = status.get('statusSeverityDescription', '')
            if status_desc.strip().lower() not in ('good service', 'normal service'):
                reason = status.get('reason', 'Minor delays reported.')
                disruptions.append({
                    "line": line.get('name'),
                    "severity": status_desc,
                    "reason": reason,
                })
    return disruptions


# Southeastern 是一個涵蓋整個東南倫敦/肯特郡的大型營運商，Line Status API 回報的是
# 「整個公司」的狀況，而不是特定路線區段。實測發現 Bromley South（與 Lewisham→Charing
# Cross 完全無關的另一條支線）的通知會被誤判為「本路線」中斷。因此改用 reason 文字中
# 常見的 nationalrail.co.uk service-disruptions URL 解析出受影響車站，只有在明確辨識
# 出的車站「不在」本路線上時才排除；無法辨識車站（例如全線性質的通知）則保守地維持標記。
_RELEVANT_SOUTHEASTERN_STATION_SLUGS = {"lewisham", "london-bridge", "waterloo-east", "charing-cross"}


def _extract_disruption_station_slug(reason_text):
    match = re.search(r"service-disruptions/([a-z-]+)-\d{8}", reason_text)
    return match.group(1) if match else None


# nationalrail.co.uk 的即時發車看板頁面把資料以 Next.js SSR JSON 塞進
# <script id="__NEXT_DATA__">，可用純 requests 取得。頁面的 JS bundle 裡也含有一堆
# 「即使目前沒有任何中斷」也永遠存在的 UI 靜態文字（例如
# journeySummaryMicrocopy__replacementBusService），因此只檢查真正即時的
# nrccMessages（車站即時公告）與 services（實際班次清單）裡的 replacement bus 訊號，
# 避免被那些固定不變的 UI 文字誤判成永遠都在中斷。
NATIONALRAIL_LEWISHAM_URL = "https://www.nationalrail.co.uk/live-trains/departures/lewisham/"
_NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(\{.*?\})</script>')
_HTML_TAG_RE = re.compile(r"<[^>]+>")

_NATIONALRAIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


def check_lewisham_replacement_buses():
    """檢查 Lewisham 車站即時發車看板，看是否有 rail replacement bus 的即時訊號
    （車站公告或實際班次列表），代表本站目前形同關閉"""
    res = requests.get(NATIONALRAIL_LEWISHAM_URL, headers=_NATIONALRAIL_HEADERS, timeout=20)
    res.raise_for_status()

    match = _NEXT_DATA_RE.search(res.text)
    if not match:
        raise RuntimeError("在頁面中找不到 __NEXT_DATA__")
    data = json.loads(match.group(1))

    # 用 "x.get(key) or default" 而不是 "x.get(key, default)"：實測發現這個 API 在
    # 「目前沒有任何即時公告」時會回傳 "nrccMessages": null（不是省略這個欄位，也不是
    # 空陣列 []）。.get(key, default) 的 default 只有在 key 完全不存在時才會生效，key
    # 存在但值是 null 一樣會拿到 None，導致後面對 None 做 for 迴圈直接丟出
    # TypeError: 'NoneType' object is not iterable - 這幾乎每次「沒有公告」（最常見的
    # 情況）都會發生，而不是罕見的個案。整條鏈路都改用這個寫法以防其他欄位也有同樣情況。
    props = data.get("props") or {}
    page_props = props.get("pageProps") or {}
    live_trains_state = page_props.get("liveTrainsState") or {}
    queries = live_trains_state.get("queries") or []

    state = (queries[0].get("state") or {}) if queries else {}
    state_data = state.get("data") or {}
    pages = state_data.get("pages") or []
    page = pages[0] if pages else {}

    nrcc_messages = page.get("nrccMessages") or []
    services = page.get("services") or []

    notice_texts = []
    for m in nrcc_messages:
        text = _HTML_TAG_RE.sub("", m.get("message", ""))
        if "replacement" in text.lower():
            notice_texts.append(text)

    replacement_services = sum(
        1 for s in services if s.get("serviceType", {}).get("category") == "BusReplacement"
    )

    is_closed = bool(notice_texts) or replacement_services > 0
    return is_closed, notice_texts, replacement_services


# Citymapper 的 directions 頁面本身是純前端 SPA（無 SSR JSON，需執行 JS 才會有內容），
# 但實測發現該頁面背後呼叫的 citymapper.com/api/7/journeys 是一個一般公開、不需登入
# 的 JSON API：不帶任何 header 會被 Cloudflare 擋下（403），但帶上一般瀏覽器常見的
# User-Agent / Referer / Accept 標頭即可直接用 requests 取得完整的即時路線資料
# （時間、票價、各段交通方式），不需要真的啟動瀏覽器。
CITYMAPPER_HITHER_GREEN_TO_STRAND_URL = (
    "https://citymapper.com/directions?lang=en&startcoord=51.452024%2C-0.000944"
    "&endcoord=51.510131%2C-0.121783&startname=Hither+Green&endname=Virgin+Active+Strand"
    "&endaddress=Strand%2C+London%2C+UK"
)
_CITYMAPPER_JOURNEYS_API_URL = (
    "https://citymapper.com/api/7/journeys"
    "?start=51.452024%2C-0.000944"
    "&end=51.510131%2C-0.121783"
    "&eaddr=Strand%2C%20London%2C%20UK"
    "&sname=Hither%20Green"
    "&ename=Virgin%20Active%20Strand"
    "&region_id=uk-london"
    "&include_stepfree=1"
    "&include_via_microtransit=1"
    "&status_format=html"
)
_CITYMAPPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://citymapper.com/directions",
    "Accept": "application/json",
}


def get_hither_green_to_strand_route(max_attempts=3):
    """呼叫 Citymapper journeys API，回傳從 Hither Green 到 Virgin Active Strand
    的建議路線摘要文字（給 Lewisham 車站關閉時作為替代路線參考）。
    實測過偶爾會超過 20 秒逾時，因此加上重試機制"""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.get(_CITYMAPPER_JOURNEYS_API_URL, headers=_CITYMAPPER_HEADERS, timeout=25)
            res.raise_for_status()
            data = res.json()
            break
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"Citymapper journeys API 錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt < max_attempts:
                time.sleep(3 * attempt)
    else:
        raise last_error

    sections = data.get("sections", [])
    journeys = data.get("journeys", [])
    suggested = next((s for s in sections if s.get("id") == "SUGGESTED"), None)
    if not suggested or not suggested.get("journeys"):
        raise RuntimeError("Citymapper 回應中找不到建議路線")
    journey = journeys[suggested["journeys"][0]]

    duration_min = round(journey.get("duration_seconds", 0) / 60)
    price = journey.get("formatted_price", "N/A")

    steps = []
    for leg in journey.get("legs", []):
        mode = leg.get("mode")
        if mode == "walk":
            mins = round(leg.get("duration_seconds", 0) / 60)
            if mins > 0:
                steps.append(f"🚶 Walk {mins} min")
        elif mode == "transit":
            routes = leg.get("routes", [])
            route_name = routes[0].get("display_name") if routes else "Transit"
            departures = leg.get("departures", [])
            dep = departures[0] if departures else {}
            time_name = dep.get("time_name", "")
            dest = dep.get("destination_name", "")
            steps.append(f"🚆 {route_name} to {dest} ({time_name})")

    route_desc = " → ".join(steps) if steps else "Route details unavailable"
    return f"{route_desc}\nTotal: {duration_min} min, {price}"


def check_route_disruption():
    """檢查前往 Virgin Active Strand 路線（Lewisham → Charing Cross, Southeastern 直達車）的即時路況"""
    result = _check_route_disruption_impl()
    print(f"Route Check 判斷結果: {result}")
    return result


def _check_route_disruption_impl():
    try:
        is_closed, notice_texts, replacement_services = check_lewisham_replacement_buses()
    except Exception as e:
        print(f"Lewisham 車站關閉檢查失敗: {e}")
        is_closed, notice_texts, replacement_services = False, [], 0

    if is_closed:
        details = "; ".join(notice_texts) if notice_texts else f"{replacement_services} rail replacement bus service(s) found on the departure board"
        print(f"Lewisham 車站關閉詳情: {details}")
        message = "🔴 Lewisham station appears to be closed - rail replacement buses in operation.\n"
        try:
            route_summary = get_hither_green_to_strand_route()
            message += f"\n🚏 Alternative route from Hither Green:\n{route_summary}\n"
        except Exception as e:
            print(f"Hither Green → Strand 路線查詢失敗: {e}")
            message += f"\n🔗 [Check route from Hither Green]({CITYMAPPER_HITHER_GREEN_TO_STRAND_URL})\n"
        message += f"🔗 [Check live departures]({NATIONALRAIL_LEWISHAM_URL})"
        return message

    try:
        # Lewisham 有 Southeastern 直達車到 Charing Cross（步行至 Strand 約 5 分鐘），
        # 因此只檢查與此路線相關的服務。注意：'charing-cross' 不是有效的 TfL line id
        # （它是車站，不是路線），查了也不會比對到任何東西，故不使用。
        disruptions = _get_tfl_line_disruptions(['southeastern'])

        relevant = []
        for d in disruptions:
            slug = _extract_disruption_station_slug(d["reason"])
            formatted = f"{d['line']}: {d['reason']}"
            if slug and slug not in _RELEVANT_SOUTHEASTERN_STATION_SLUGS:
                print(f"忽略與本路線無關的 Southeastern 通知（車站: {slug}）: {formatted}")
                continue
            relevant.append(formatted)

        if not relevant:
            return "This route is clear ✅"
        details = "\n\n".join(relevant)
        return f"🔴 This route is disrupted because:\n{details}"
    except Exception as e:
        print(f"路線檢查失敗: {e}")
        return f"This route state check failed. You can check manually here: [Citymapper Route]({CITYMAPPER_GYM_URL})"


# DLR 有多條分支（Bank/Tower Gateway<->Lewisham、Bank<->Woolwich Arsenal、
# Stratford<->Beckton 等），Elizabeth line 則橫跨 Reading/Heathrow 到 Shenfield/Abbey
# Wood，Northern line 更是全倫敦分支最多的地鐵線（Morden/Edgware/High Barnet/Battersea
# 等多條分支、中央又分 Bank/Charing Cross 兩條路線）。三者都可能出現與本路線完全無關的
# 通知（原理同 Southeastern 的 Bromley South 案例）。
#
# 2026-10-08 的真實案例：Northern line 當天回報 "Severe delays due to an earlier
# signal failure at Stockwell."。Stockwell 在下面的排除清單裡（它在 Morden/Battersea
# 分支上），舊邏輯只因文字提到 "Stockwell" 就把整筆通知忽略掉——但 TfL 的文字完全沒有
# 寫出「範圍限定語句」（例如 "between X and Y" 或 "GOOD SERVICE on the rest of the
# line"，同一天 Elizabeth line 的通知就有這種限定語句可以對照），代表這其實是全線性質
# 的 Severe Delays，確實影響了本路線使用的 Bank 分支，導致 17:30 的下班提醒該發送卻
# 完全沒發送。Stockwell 只是事故（訊號故障）發生的地點，不代表中斷範圍僅限於該處。
#
# 新邏輯（_is_office_route_disruption_relevant()）：只有在文字「明確」寫出範圍限定
# 語句時，才進一步比對下面的排除清單去判斷是否真的不相關；完全沒有限定語句時，不管
# 有沒有提到清單上的地點名稱，一律視為可能相關（寧可多發一次通知，也不要重演這次漏發
# 的狀況）。這個規則對 dlr/elizabeth/northern 三條線、以及任何非 Good Service 的嚴重
# 程度（Minor Delays 一樣適用，不只 Severe Delays）都一致套用。
_IRRELEVANT_OFFICE_ROUTE_KEYWORDS = (
    # DLR 的其他分支，不在 Lewisham -> Canary Wharf 這段
    "woolwich arsenal", "beckton", "stratford international", "london city airport",
    "king george v", "pontoon dock", "cyprus", "gallions reach", "custom house",
    "prince regent", "royal albert", "west silvertown", "star lane", "abbey road",
    # Elizabeth line 西/東端遠離 Canary Wharf<->Liverpool Street 核心段的地點
    "reading", "heathrow", "maidenhead", "slough", "west drayton", "hayes & harlington",
    "southall", "ealing broadway", "shenfield", "romford", "ilford", "chadwell heath",
    "gidea park", "harold wood", "brentwood", "seven kings", "goodmayes", "manor park",
    # Northern line 的其他分支/路線，不在 Lewisham -> Bank -> Old Street（經 DLR + Bank
    # 分支）這段：High Barnet 分支、Edgware 分支、Mill Hill East 支線、Morden 南段、
    # Battersea 延伸、以及本路線不使用的 Charing Cross 中央路段
    "high barnet", "totteridge", "woodside park", "west finchley", "finchley central",
    "east finchley", "highgate", "archway", "tufnell park", "kentish town",
    "edgware", "burnt oak", "colindale", "hendon central", "brent cross", "golders green",
    "hampstead", "belsize park", "chalk farm", "mill hill east",
    "morden", "south wimbledon", "colliers wood", "tooting broadway", "tooting bec",
    "balham", "clapham south", "clapham common", "clapham north", "stockwell", "oval",
    "kennington", "battersea power station", "nine elms",
    "waterloo", "embankment", "leicester square", "tottenham court road",
    "warren street", "goodge street",
)


def _text_mentions_any(text, keywords):
    """用 \\b 單字邊界比對而不是純子字串比對，避免像 "bank" 吃到 "embankment"
    裡面那樣的誤判。text 必須已經是小寫，keywords 也必須已經是小寫。"""
    return any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords)


def _mentions_irrelevant_office_location(reason_text):
    return _text_mentions_any(reason_text.lower(), _IRRELEVANT_OFFICE_ROUTE_KEYWORDS)


# 本路線實際會經過的車站/地點（DLR Bank<->Lewisham 分支 + Northern line 經 Bank/
# Moorgate 往 Old Street 這段）。只要中斷通知明確提到其中之一，就一定與本路線相關——
# 即使同一句話裡也出現了 _IRRELEVANT_OFFICE_ROUTE_KEYWORDS 裡的地名（例如
# "severe delays between Kennington and Bank" 同時提到 Kennington 和 Bank：
# Kennington 在排除清單裡，但這句話明確劃定的受影響區段包含 Bank，確實影響本路線，
# 不能只因為提到 Kennington 就被排除）。
_RELEVANT_OFFICE_ROUTE_KEYWORDS = (
    "bank", "old street", "moorgate", "lewisham",
    "shadwell", "limehouse", "westferry", "west india quay", "canary wharf",
    "heron quays", "south quay", "crossharbour", "mudchute", "island gardens",
    "cutty sark", "greenwich", "deptford bridge", "elverson road",
)


def _mentions_relevant_office_location(reason_text):
    return _text_mentions_any(reason_text.lower(), _RELEVANT_OFFICE_ROUTE_KEYWORDS)


# TfL 在把中斷範圍明確限定在某個區段時，文字裡一定會有這類限定語句，例如
# "between Camden Town and Morden" 或 "GOOD SERVICE on the rest of the line"。
# 單純提到一個地點名稱不代表中斷範圍僅限於該處——它可能只是事故起因的地點
# （2026-10-08 的 Stockwell 案例），而不是中斷範圍的邊界。
_LINE_SCOPE_QUALIFIER_RE = re.compile(
    r"\bbetween\b.+?\band\b|good service\b.*\bthe rest of the line\b",
    re.IGNORECASE,
)


def _is_office_route_disruption_relevant(reason_text):
    """判斷一筆 dlr/elizabeth/northern 的中斷通知是否與本路線（Bank 分支）相關。
    1. 只要明確提到本路線實際會經過的車站（_RELEVANT_OFFICE_ROUTE_KEYWORDS），
       一律視為相關，不管句子裡還提到了什麼其他地名。
    2. 否則，只有在文字明確寫出範圍限定語句（_LINE_SCOPE_QUALIFIER_RE）時，才
       信任 _IRRELEVANT_OFFICE_ROUTE_KEYWORDS 去判斷「不相關」。
    3. 完全沒有限定語句時，不管有沒有提到排除清單上的地點名稱，一律視為相關
       （寧可多發一次通知，也不要漏掉真的有影響的中斷）。"""
    if _mentions_relevant_office_location(reason_text):
        return True
    if not _LINE_SCOPE_QUALIFIER_RE.search(reason_text):
        return True
    return not _mentions_irrelevant_office_location(reason_text)


def _format_office_route_disruptions(disruptions):
    return "; ".join(f"{d['line']}: {d['severity']} - {d['reason']}" for d in disruptions)


def check_office_route_disruption():
    """檢查平日通勤路線（Lewisham → Bank [DLR] → Old Street [Northern line]）的即時路況。
    路線正常時回傳 None，代表晨報中完全不顯示這個區塊（使用者只想在真的有中斷時才看到）。
    相關性判斷見 _is_office_route_disruption_relevant()。"""
    try:
        # 路線由使用者提供的 Citymapper 連結解碼確認：home -> Bank (DLR) -> Old Street
        # (Northern line, 經 Moorgate)。查詢的 TfL line id 維持不變（dlr/elizabeth/northern）。
        disruptions = _get_tfl_line_disruptions(['dlr', 'elizabeth', 'northern'])

        relevant = []
        for d in disruptions:
            if not _is_office_route_disruption_relevant(d["reason"]):
                print(f"忽略與本路線無關的通知: {d['line']}: {d['reason']}")
                continue
            relevant.append(d)

        if not relevant:
            return None
        details = _format_office_route_disruptions(relevant)
        return f"the route to office is disrupted 🔴 because {details}"
    except Exception as e:
        print(f"辦公室路線檢查失敗: {e}")
        return (
            "the route to office check failed. You can check manually here: "
            f"[Route]({CITYMAPPER_OFFICE_URL})"
        )


def check_home_from_office_route_disruption():
    """檢查平日下班路線（Old Street [Northern line] → Bank → Lewisham [DLR]）的即時
    路況。與 check_office_route_disruption() 方向相反，但用的是同樣兩條 TfL line
    （dlr/northern，elizabeth 一樣不會用到），所以沿用同一套相關性判斷
    （_is_office_route_disruption_relevant()）。
    路線正常時回傳 None，代表 17:30 的下班提醒完全不發送（使用者只想在真的有
    中斷時才收到通知）"""
    result = _check_home_from_office_route_disruption_impl()
    print(f"Home Route Check 判斷結果: {result}")
    return result


def _check_home_from_office_route_disruption_impl():
    try:
        disruptions = _get_tfl_line_disruptions(['dlr', 'elizabeth', 'northern'])

        relevant = []
        for d in disruptions:
            if not _is_office_route_disruption_relevant(d["reason"]):
                print(f"忽略與本路線無關的通知: {d['line']}: {d['reason']}")
                continue
            relevant.append(d)

        if not relevant:
            return None
        details = _format_office_route_disruptions(relevant)
        return f"the route home is disrupted 🔴 because {details}"
    except Exception as e:
        print(f"下班路線檢查失敗: {e}")
        return (
            "the route home check failed. You can check manually here: "
            f"[Route]({CITYMAPPER_HOME_FROM_OFFICE_URL})"
        )


# 每週日檢查這些場地/活動系列的「即將到來的星期四/星期五」活動。La Camionera 自己的
# OutSavvy organiser 清單頁（純 HTML，可直接 requests 抓取）就有完整活動清單。
_WLW_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

LA_CAMIONERA_EVENTS_URL = "https://www.outsavvy.com/organiser/la-camionera"
OLD_NUNSHEAD_EVENTS_URL = "https://www.theoldnunshead.co.uk/events"
PUB_QUIZ_EVENTS_URL = "https://www.eventbrite.com/cc/the-lesbian-pub-quiz-3867043/"
SPEED_DATING_EVENTS_URL = "https://www.eventbrite.com/cc/lesbian-speed-dating-3678189/"


def _parse_outsavvy_date(date_text):
    """解析 OutSavvy organiser 頁面的日期文字，例如
    'Thursday 8th October 2026 (+ 1 other date)' -> date(2026, 10, 8)。
    只取第一個（最近的）日期，'(+ N other dates)' 的部分忽略不處理。"""
    match = re.search(r"(\d{1,2})\w*\s+([A-Za-z]+)\s+(\d{4})", date_text)
    if not match:
        return None
    day, month_name, year = match.groups()
    try:
        return datetime.strptime(f"{day} {month_name} {year}", "%d %B %Y").date()
    except ValueError:
        return None


def _scrape_outsavvy_organiser(venue_name, url):
    """OutSavvy organiser 頁面把每個活動列成 <h5>標題</h5>，包在 <a href> 裡，
    同一個 <a> 底下有個 <span class="copy"> 顯示日期文字"""
    res = requests.get(url, headers=_WLW_HEADERS, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    events = []
    for h5 in soup.find_all("h5"):
        title = h5.get_text(strip=True)
        if not title:
            continue
        anchor = h5.find_parent("a")
        if not anchor:
            continue
        time_span = anchor.find("span", class_="copy")
        if not time_span:
            continue
        event_date = _parse_outsavvy_date(time_span.get_text(strip=True))
        if event_date is None:
            continue
        events.append((venue_name, title, event_date, anchor.get("href")))
    return events


def _scrape_old_nunshead():
    """Old Nun's Head 的 Squarespace 活動頁在每個 <article> 裡都有完整的 ISO 日期
    （<time class="event-date" datetime="2026-10-01">），但頁面會把同一個活動重複
    輸出兩次（grid/list 兩種版面），因此用連結網址去重。"""
    res = requests.get(OLD_NUNSHEAD_EVENTS_URL, headers=_WLW_HEADERS, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    events = []
    seen_hrefs = set()
    for article in soup.find_all("article"):
        link = article.find("a", class_="eventlist-title-link")
        time_el = article.find("time", class_="event-date")
        if not link or not time_el or not time_el.get("datetime"):
            continue

        href = link.get("href")
        if not href or href in seen_hrefs:
            continue

        try:
            event_date = datetime.strptime(time_el["datetime"], "%Y-%m-%d").date()
        except ValueError:
            continue

        seen_hrefs.add(href)
        full_url = href if href.startswith("http") else f"https://www.theoldnunshead.co.uk{href}"
        events.append(("Old Nun's Head", link.get_text(strip=True), event_date, full_url))
    return events


# Eventbrite 的 collection（/cc/<slug>-<id>/）頁面是這個系列活動的「所有場次」清單，
# 跟一般搜尋頁（eventbrite.co.uk/d/...，會被 AWS WAF 擋下）不同，這種頁面實測是
# 乾淨的 200、沒有 bot 驗證。頁面的 JSON-LD 裡有一個 @type=ItemList，
# itemListElement 裡列出這個系列「過去辦過」與「尚未到來」的所有場次（混在一起、
# 沒有排序），每個場次有帶時區 offset 的 startDate（例如
# "2026-10-08T19:00:00+0100"），offset 已經是倫敦當地時間的正確 BST/GMT，所以
# 直接 .date() 就是正確的本地日期，不需要再轉時區。因為後面 check_wlw_events()
# 本來就只挑出剛好等於目標星期四/五日期的場次，過去辦過的場次自然不會命中，
# 不需要額外篩選「只要未來」的邏輯。
def _scrape_eventbrite_collection(series_name, url):
    """已取消的場次標題會以 'CANCELLED' 開頭（Eventbrite 自己加的），直接排除。"""
    res = requests.get(url, headers=_WLW_HEADERS, timeout=20)
    res.raise_for_status()

    item_list = None
    for block in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', res.text, re.DOTALL):
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        if parsed.get("@type") == "ItemList":
            item_list = parsed
            break
    if item_list is None:
        raise RuntimeError("在頁面中找不到 ItemList JSON-LD")

    events = []
    for item in item_list.get("itemListElement", []):
        event = (item or {}).get("item") or {}
        title = event.get("name") or ""
        if title.upper().startswith("CANCELLED"):
            continue
        start = event.get("startDate")
        href = event.get("url")
        if not start or not href:
            continue
        try:
            event_date = datetime.fromisoformat(start).date()
        except ValueError:
            continue
        events.append((series_name, title, event_date, href))
    return events


def check_wlw_events(reference_date):
    """檢查這些場地/活動系列（La Camionera、Old Nun's Head、The Lesbian Pub Quiz、
    Lesbian Speed Dating）在
    「即將到來的星期四」與「即將到來的星期五」有哪些活動。
    「即將到來」是相對於 reference_date 算的（晨報呼叫時傳入 now_local.date()），
    這樣 SIMULATED_NOW 測試才能正確模擬「某天跑出來的結果」，而不是永遠用真實的
    系統現在時間去算。沒有任何活動時回傳 None（晨報中完全不顯示這個區塊）；
    只要有任何一個來源抓取成功就以該來源結果為準，只有在四個來源「全部」失敗時
    才回傳備用訊息。"""
    result = _check_wlw_events_impl(reference_date)
    print(f"WLW Events Check 判斷結果: {result}")
    return result


def _check_wlw_events_impl(today):
    thursday = today + timedelta(days=(3 - today.weekday()) % 7)
    friday = today + timedelta(days=(4 - today.weekday()) % 7)

    scrapers = [
        lambda: _scrape_outsavvy_organiser("La Camionera", LA_CAMIONERA_EVENTS_URL),
        _scrape_old_nunshead,
        lambda: _scrape_eventbrite_collection("The Lesbian Pub Quiz", PUB_QUIZ_EVENTS_URL),
        lambda: _scrape_eventbrite_collection("Lesbian Speed Dating", SPEED_DATING_EVENTS_URL),
    ]

    all_events = []
    failures = 0
    for scraper in scrapers:
        try:
            found = scraper()
            print(f"WLW 來源抓到 {len(found)} 個活動")
            all_events.extend(found)
        except Exception as e:
            failures += 1
            print(f"WLW 活動來源抓取失敗: {e}")

    if failures == len(scrapers):
        return (
            "Couldn't fetch this week's events. Check manually: "
            f"[La Camionera]({LA_CAMIONERA_EVENTS_URL}) | "
            f"[Old Nun's Head]({OLD_NUNSHEAD_EVENTS_URL}) | "
            f"[The Lesbian Pub Quiz]({PUB_QUIZ_EVENTS_URL}) | "
            f"[Lesbian Speed Dating]({SPEED_DATING_EVENTS_URL})"
        )

    matches = [e for e in all_events if e[2] in (thursday, friday)]
    if not matches:
        return None

    # 每個有活動的日子自成一段，段落之間用兩行 "---" 分隔（只有兩天都有活動時才會
    # 出現分隔線；只有一天有活動就只有一段，沒有分隔線）。
    day_sections = []
    for day_date, day_name in ((thursday, "Thursday"), (friday, "Friday")):
        day_matches = sorted(e for e in matches if e[2] == day_date)
        if not day_matches:
            continue
        section_lines = [f"*{day_name} {day_date.strftime('%-d %B')}*"]
        for venue, title, _, href in day_matches:
            section_lines.append(f"[{title}]({href}) — {venue}")
        day_sections.append("\n".join(section_lines))
    return "\n---\n---\n".join(day_sections)


# TfL 的 Road Disruption API（/Road/all/Disruption）不需要任何 API key，回傳倫敦
# 所有道路的即時中斷清單，其中 category 為 "Planned events" 的項目涵蓋示威/遊行
# (Demonstration/March)、演唱會 (Concert)、拍片 (Filming)、體育賽事 (Sporting) 等
# 計畫性道路事件，資料結構清楚（corridorIds、location、comments、起止時間），不用
# 像 tfl.gov.uk/traffic/status 網頁那樣被 bot 驗證擋下（該網頁 plain requests 拿到
# 的是 403 "Verification required"，無法直接 scrape，見
# TFL_CENTRAL_LONDON_TRAFFIC_STATUS_URL）。
#
# 已知限制：實測這個 API 似乎只會在事件「已經開始」(startDateTime <= 查詢當下) 才會
# 出現在清單裡——2026-10-08 查過當天示威時，全部 126 筆目前的中斷裡沒有一筆
# startDateTime 是兩小時以上之後的「真正未來」時段。這代表這個檢查比較像是「現在路上
# 在發生什麼」，不保證前一晚或清晨就能提早看到當天稍晚才開始的活動；但這仍然比完全沒有
# 這個檢查好，而且不無法排除 TfL 真的會提早幾天公佈大型計畫性活動（只是目前這組樣本沒
# 觀察到），所以還是把它接到 Friday 晚報跟 Saturday 早報，實際跑幾週後再看資料準不准。
TFL_ROAD_DISRUPTION_API_URL = "https://api.tfl.gov.uk/Road/all/Disruption"


def _get_planned_road_events():
    """查詢 TfL Road Disruption API，回傳 category 為 "Planned events" 的原始
    中斷清單（可能為空）。相關性篩選交給呼叫端（_is_planned_event_relevant()）。"""
    res = requests.get(TFL_ROAD_DISRUPTION_API_URL, timeout=20)
    res.raise_for_status()
    data = res.json()
    return [d for d in data if d.get("category") == "Planned events"]


# Saturday gym 路線走的是 Lewisham (Southeastern) -> Charing Cross -> 步行到
# Strand (Virgin Active Strand)。倫敦市中心的大型示威/遊行常會直接經過或封閉這些
# 路/地標，即使活動本身不是在 Strand 上，路障/改道也常波及代替巴士的行駛路線——
# 2026-10-10 的真實案例：示威從 Victoria Embankment 經 Westminster Bridge、York
# Road、Waterloo Bridge、Strand 到 Trafalgar Square/Whitehall，代替巴士因此被迫
# 中途改道。
_RELEVANT_PLANNED_EVENT_KEYWORDS = (
    "strand", "trafalgar square", "whitehall", "charing cross",
    "northumberland avenue", "embankment", "waterloo bridge",
    "westminster bridge", "aldwych", "the mall", "pall mall",
    "cockspur street", "villiers street", "savoy",
)


def _is_planned_event_relevant(event):
    text = f"{event.get('location', '')} {event.get('comments', '')}".lower()
    return _text_mentions_any(text, _RELEVANT_PLANNED_EVENT_KEYWORDS)


def _format_event_time(start, end):
    try:
        start_local = _parse_iso(start).astimezone(LOCAL_TZ).strftime("%H:%M")
        end_local = _parse_iso(end).astimezone(LOCAL_TZ).strftime("%H:%M")
        return f"{start_local} - {end_local}"
    except (ValueError, AttributeError):
        return f"{start} - {end}"


def check_planned_events():
    """檢查與 Saturday gym 路線（Lewisham -> Charing Cross -> 步行到 Strand）相關
    的計畫性道路事件（示威/遊行、演唱會、拍片、體育賽事）。沒有相關事件時回傳
    None。已知限制見 TFL_ROAD_DISRUPTION_API_URL 上方的說明。"""
    result = _check_planned_events_impl()
    print(f"Planned Events Check 判斷結果: {result}")
    return result


def _check_planned_events_impl():
    try:
        events = _get_planned_road_events()
    except Exception as e:
        print(f"Planned events 查詢失敗: {e}")
        return (
            "couldn't check for planned road events (demonstrations/closures). "
            f"Check manually: [TfL Traffic Status]({TFL_CENTRAL_LONDON_TRAFFIC_STATUS_URL})"
        )

    relevant = [e for e in events if _is_planned_event_relevant(e)]
    if not relevant:
        return None

    sections = []
    for e in relevant:
        sub = e.get("subCategory", "Planned event")
        loc = e.get("location", "")
        time_range = _format_event_time(e.get("startDateTime"), e.get("endDateTime"))
        comment = e.get("comments", "")
        sections.append(f"*{sub}* ({time_range})\n{loc}\n{comment}")
    return "\n\n".join(sections)


def send_telegram(msg, max_attempts=3):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        raise RuntimeError("TG_BOT_TOKEN / TG_CHAT_ID 未設定，請確認 repository secrets。")
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.post(url, json=payload, timeout=20)
            if not res.ok:
                print(f"Telegram 傳送失敗: {res.status_code} {res.text}")
            res.raise_for_status()
            return
        except requests.exceptions.RequestException as e:
            print(f"Telegram 傳送錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt == max_attempts:
                raise
            time.sleep(3 * attempt)


# 讓使用者可以主動在 Telegram 發 /briefing 跟機器人要一份晨報，而不是只能被動等
# 07:00 的排程。GitHub Actions 的 runner 每次執行都是全新環境，不會記得「上次看到
# 哪個 update_id」，所以用這個檔案把 offset 存回 repo（只有在真的收到新訊息時才會
# 變動/commit，平常每次輪詢沒有新訊息的情況下完全不會產生任何 git 動作）。
TELEGRAM_OFFSET_FILE = "telegram_offset.json"

# 使用者可以發送的指令文字（大小寫、前後空白不計）。
_BRIEFING_COMMANDS = {"/briefing", "briefing"}
_WLW_COMMANDS = {"/wlw", "wlw"}


def _load_telegram_offset():
    try:
        with open(TELEGRAM_OFFSET_FILE) as f:
            return json.load(f).get("last_update_id", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def _save_telegram_offset(update_id):
    with open(TELEGRAM_OFFSET_FILE, "w") as f:
        json.dump({"last_update_id": update_id}, f)
        f.write("\n")


def _get_telegram_updates(offset):
    """呼叫 Telegram getUpdates，offset 設為「上次看過的 update_id + 1」。Telegram
    看到這個 offset 就會把更早的 update 都標記為已確認，之後不會再回傳同一筆，
    不需要我們自己額外呼叫任何「確認已讀」的 API。timeout=0 代表短輪詢（立刻回應
    目前已有的更新，不等待新訊息進來），適合 GitHub Actions 這種跑一次就結束的
    環境，不適合用長輪詢（會讓 job 卡著等）。"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getUpdates"
    res = requests.get(url, params={"offset": offset, "timeout": 0}, timeout=15)
    res.raise_for_status()
    data = res.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates 回應異常: {data}")
    return data.get("result", [])


def send_wlw_events_update(now_local):
    """被 /wlw 指令觸發的「只要 WLW 活動區塊」版本。跟 Sunday 晨報裡的區塊共用同一個
    check_wlw_events()，但行為上有一個關鍵差異：Sunday 晨報裡 check_wlw_events()
    回傳 None 時整個區塊直接不出現在訊息裡（因為那是附加在其他內容後面的一個小節，
    沒有內容就不需要特別說明）；但 /wlw 是使用者主動問的，回傳 None 時如果完全不
    回應，使用者會以為指令沒有被處理到/壞掉了，所以這裡改成明確回傳「目前沒有符合
    的活動」訊息，一定會有某種回覆。"""
    wlw_events = check_wlw_events(now_local.date())
    if wlw_events is None:
        msg = "🎀 *Upcoming Thu/Fri Events*\n沒有找到即將到來的星期四/星期五活動。"
    else:
        msg = f"🎀 *Upcoming Thu/Fri Events*\n{wlw_events}"
    send_telegram(msg)


def poll_telegram_commands(now_local):
    """輪詢 Telegram，檢查使用者是否主動發送 /briefing 或 /wlw 指令；若有，立即
    觸發對應的回覆（/briefing 觸發跟 07:00 排程內容一樣的完整晨報，依照「今天」
    實際星期幾顯示對應區塊；/wlw 只回傳 WLW 活動區塊，見 send_wlw_events_update()
    說明它跟 Sunday 晨報裡那個區塊的行為差異）。只處理來自 TG_CHAT_ID 本人的訊息，
    其他來源（例如別人誤發訊息給這個 bot）一律忽略，不會觸發任何動作也不會被當成
    「已處理」而推進 offset 之外的行為影響。"""
    last_offset = _load_telegram_offset()
    updates = _get_telegram_updates(last_offset + 1 if last_offset else 0)

    if not updates:
        print("沒有新的 Telegram 訊息")
        return

    highest_update_id = last_offset
    triggered = False
    for update in updates:
        highest_update_id = max(highest_update_id, update.get("update_id", highest_update_id))
        message = update.get("message") or {}
        chat_id = str((message.get("chat") or {}).get("id", ""))
        text = (message.get("text") or "").strip().lower()

        if chat_id != str(TG_CHAT_ID):
            print(f"忽略來自非本人 chat_id 的訊息: {chat_id}")
            continue

        if text in _BRIEFING_COMMANDS:
            print(f"收到 on-demand 晨報指令: {text!r}")
            send_full_briefing(now_local, False, False, False)
            triggered = True
        elif text in _WLW_COMMANDS:
            print(f"收到 on-demand WLW 活動指令: {text!r}")
            send_wlw_events_update(now_local)
            triggered = True
        else:
            print(f"收到不認識的訊息，忽略: {text!r}")

    _save_telegram_offset(highest_update_id)
    print(f"已處理到 update_id={highest_update_id}" + ("（已觸發指令回應）" if triggered else ""))


def send_full_briefing(now_local, force_route_check, force_office_check, force_wlw_check):
    today = now_local.strftime("%Y-%m-%d (%a)")
    is_saturday = now_local.weekday() == 5  # 5 = Saturday
    is_sunday = now_local.weekday() == 6  # 6 = Sunday
    is_weekday = now_local.weekday() < 5  # 0-4 = Mon-Fri

    curr_price, cheapest_slot, cheap_windows = get_octopus_agile_rates()
    curr_temp, temp_range, rain_msg = get_weather_forecast()
    gbp_hkd_rate = get_gbp_hkd_tt_rate()

    briefing = (
        f"☀️ *晨間晨報 ({today})*\n\n"
        f"⚡ *Octopus Agile 即時電價*\n"
        f"• 當前電價: `{curr_price}`\n"
        f"• 未來 24h 最低價時段: `{cheapest_slot}`\n"
        f"• 未來 24h 低於 {OCTOPUS_CHEAP_THRESHOLD_P_PER_KWH}p/kWh 時段: `{cheap_windows}`\n\n"
        f"🌤️ *Lewisham 天氣預報*\n"
        f"• 當前氣溫: `{curr_temp}`\n"
        f"• 今日氣溫區間: `{temp_range}`\n"
        f"• 降雨提醒: {rain_msg}\n"
    )

    if gbp_hkd_rate is not None:
        try:
            meets_buy_threshold = float(gbp_hkd_rate['buy']) >= GBP_HKD_BUY_RATE_THRESHOLD
        except (TypeError, ValueError):
            meets_buy_threshold = False

        if meets_buy_threshold:
            briefing += (
                f"\n💷 *GBP/HKD TT Rate (Hang Seng)*\n"
                f"• Bank Buy: `{gbp_hkd_rate['buy']}`\n"
                f"• Bank Sell: `{gbp_hkd_rate['sell']}`\n"
                f"🕐 Last updated: {gbp_hkd_rate['last_update']}\n"
            )
    else:
        briefing += (
            f"\n💷 *GBP/HKD TT Rate (Hang Seng)*\n"
            f"Couldn't fetch the rate this time. Check manually: [Hang Seng TT Rates]({HANGSENG_TT_RATES_PAGE_URL})\n"
        )

    if is_weekday or force_office_check:
        office_status = check_office_route_disruption()
        if office_status is not None:
            briefing += (
                f"\n🚇 *Office Route Check*\n"
                f"{office_status}\n"
                f"🔗 [Route: Home → Old Street]({CITYMAPPER_OFFICE_URL})\n"
            )

    if is_saturday or is_sunday or force_route_check:
        route_status = check_route_disruption()
        day_label = "Saturday" if is_saturday else "Sunday" if is_sunday else "Weekend"
        briefing += (
            f"\n🏋️ *{day_label} Route Check (Virgin Active Strand)*\n"
            f"{route_status}\n\n"
            f"🔗 [Open Citymapper Route]({CITYMAPPER_GYM_URL})\n"
        )

    if is_saturday or force_route_check:
        planned_events = check_planned_events()
        if planned_events is not None:
            briefing += (
                f"\n🚧 *Planned Road Events Near Route*\n"
                f"{planned_events}\n"
            )

    if is_sunday or force_wlw_check:
        wlw_events = check_wlw_events(now_local.date())
        if wlw_events is not None:
            briefing += (
                f"\n🎀 *Upcoming Thu/Fri Events*\n"
                f"{wlw_events}\n"
            )

    briefing += "\n祝你有美好的一天！💪"
    send_telegram(briefing)


def send_route_only_update(now_local):
    """Saturday/Sunday 10:30-11:15 高頻路線提醒，只回報路況，不含天氣/電價。
    跟 7am 的 Saturday/Sunday Route Check 一樣沒有 day-of-week 判斷，完全由
    cron-job.org 何時呼叫這個 workflow 決定"""
    route_status = check_route_disruption()
    msg = (
        f"🕐 *Route Check ({now_local.strftime('%H:%M')})*\n"
        f"{route_status}\n\n"
        f"🔗 [Open Citymapper Route]({CITYMAPPER_GYM_URL})"
    )
    send_telegram(msg)


def send_evening_update(now_local):
    """平日 17:30 下班路線提醒。核心是 Office → Home 的路況，路線正常時這部分完全
    不產生內容（使用者只想在真的有中斷時才收到通知），這點與 route_only 模式
    （Saturday 高頻提醒，無論路況如何都會發送）不同。
    週五額外檢查 Saturday gym 路線附近週末計畫性道路事件（示威/演唱會等）——這是
    提早示警，即使當下路線正常也會獨立發送，不像路線檢查那樣只在有中斷時才發。
    兩部分都沒有內容時完全不發送任何訊息。"""
    home_route_status = check_home_from_office_route_disruption()
    is_friday = now_local.weekday() == 4  # 4 = Friday

    msg_parts = []
    if home_route_status is not None:
        msg_parts.append(
            f"🏠 *Office → Home Route Check*\n"
            f"{home_route_status}\n\n"
            f"🔗 [Open Citymapper Route]({CITYMAPPER_HOME_FROM_OFFICE_URL})"
        )

    if is_friday:
        planned_events = check_planned_events()
        if planned_events is not None:
            msg_parts.append(
                f"🚧 *Planned Road Events This Weekend (Saturday gym route)*\n"
                f"{planned_events}"
            )

    if not msg_parts:
        return
    send_telegram("\n\n".join(msg_parts))


def main():
    # 手動測試用：可透過 SIMULATED_NOW（ISO 格式，例如 2026-09-29T07:00:00）
    # 模擬「現在」是哪一天/幾點，藉此測試平日/週末專屬區塊在正確條件下的內容，
    # 不受實際執行當天是星期幾影響。留空則使用真實現在時間。
    simulated_now = os.environ.get("SIMULATED_NOW", "").strip()
    if simulated_now:
        now_local = datetime.fromisoformat(simulated_now).replace(tzinfo=LOCAL_TZ)
    else:
        now_local = datetime.now(LOCAL_TZ)
    mode = os.environ.get("MODE", "full").strip().lower()
    force_route_check = os.environ.get("FORCE_ROUTE_CHECK", "").lower() == "true"
    force_office_check = os.environ.get("FORCE_OFFICE_CHECK", "").lower() == "true"
    force_wlw_check = os.environ.get("FORCE_WLW_CHECK", "").lower() == "true"

    if mode == "route_only":
        send_route_only_update(now_local)
    elif mode == "evening":
        send_evening_update(now_local)
    elif mode == "poll_commands":
        poll_telegram_commands(now_local)
    else:
        send_full_briefing(now_local, force_route_check, force_office_check, force_wlw_check)


if __name__ == "__main__":
    main()
