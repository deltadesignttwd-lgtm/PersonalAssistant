import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta, timezone
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


def _parse_iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))


def get_octopus_agile_rates():
    """取得 Lewisham（London, Region _C）Octopus Agile 官方電價"""
    url = "https://api.octopus.energy/v1/products/AGILE-24-10-01/electricity-tariffs/E-1R-AGILE-24-10-01-C/standard-unit-rates/"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json().get('results', [])

        if not data:
            return "N/A", "N/A"

        now = datetime.now(timezone.utc)

        # API 回傳順序不保證是「現在」在前，因此用時間區間找出真正的當前電價
        current_entry = next(
            (r for r in data if _parse_iso(r['valid_from']) <= now < _parse_iso(r['valid_to'])),
            None
        )
        current_rate = f"{round(current_entry['value_inc_vat'], 2)} p/kWh" if current_entry else "N/A"

        # 找出未來 24 小時內「最低電價的 3 小時區段」：先找出價格最低的 1 小時
        # (2 個連續半小時 slot 平均價格最低的一段)，再往前推 2 小時形成 3 小時
        # 區段，讓使用者知道提前多久開始用電最划算
        window_end = now + timedelta(hours=24)
        upcoming = sorted(
            (r for r in data if now <= _parse_iso(r['valid_from']) < window_end),
            key=lambda r: _parse_iso(r['valid_from'])
        )
        if not upcoming:
            upcoming = sorted(data, key=lambda r: _parse_iso(r['valid_from']))

        best_avg = None
        best_hour_start = None
        for i in range(len(upcoming) - 1):
            slot_a, slot_b = upcoming[i], upcoming[i + 1]
            # 確保兩個 slot 首尾相接，避免資料缺漏時誤判成連續的 1 小時
            if _parse_iso(slot_a['valid_to']) != _parse_iso(slot_b['valid_from']):
                continue
            avg = (slot_a['value_inc_vat'] + slot_b['value_inc_vat']) / 2
            if best_avg is None or avg < best_avg:
                best_avg = avg
                best_hour_start = _parse_iso(slot_a['valid_from'])

        if best_hour_start is not None:
            window_start_local = (best_hour_start - timedelta(hours=2)).astimezone(LOCAL_TZ).strftime("%H:%M")
            window_end_local = (best_hour_start + timedelta(hours=1)).astimezone(LOCAL_TZ).strftime("%H:%M")
            lowest_window = f"{window_start_local} - {window_end_local} (cheapest hour avg {round(best_avg, 2)} p/kWh)"
        else:
            lowest_window = "N/A"

        return current_rate, lowest_window
    except Exception as e:
        print(f"Octopus API 錯誤: {e}")
        return "擷取失敗", "擷取失敗"


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
    """查詢指定 TfL line id 的即時狀態，回傳「非正常服務」的說明清單（可能為空）"""
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
                disruptions.append(f"{line.get('name')}: {reason}")
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

    queries = data.get("props", {}).get("pageProps", {}).get("liveTrainsState", {}).get("queries", [])
    pages = queries[0].get("state", {}).get("data", {}).get("pages", []) if queries else []
    page = pages[0] if pages else {}

    nrcc_messages = page.get("nrccMessages", [])
    services = page.get("services", [])

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
            slug = _extract_disruption_station_slug(d)
            if slug and slug not in _RELEVANT_SOUTHEASTERN_STATION_SLUGS:
                print(f"忽略與本路線無關的 Southeastern 通知（車站: {slug}）: {d}")
                continue
            relevant.append(d)

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
# 通知（原理同 Southeastern 的 Bromley South 案例）。TfL 對自家路線（非 National Rail
# 委外營運商）回報的 reason 通常是英文描述而非 nationalrail.co.uk 連結，因此改用關鍵字
# 比對：只有在明確提到已知「不相關」分支/地點時才排除，無法辨識地點則保守地維持標記。
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


def _mentions_irrelevant_office_location(reason_text):
    text = reason_text.lower()
    return any(kw in text for kw in _IRRELEVANT_OFFICE_ROUTE_KEYWORDS)


def check_office_route_disruption():
    """檢查平日通勤路線（Lewisham → Bank [DLR] → Old Street [Northern line]）的即時路況。
    路線正常時回傳 None，代表晨報中完全不顯示這個區塊（使用者只想在真的有中斷時才看到）"""
    try:
        # 路線由使用者提供的 Citymapper 連結解碼確認：home -> Bank (DLR) -> Old Street
        # (Northern line, 經 Moorgate)。查詢的 TfL line id 維持不變（dlr/elizabeth/northern）。
        disruptions = _get_tfl_line_disruptions(['dlr', 'elizabeth', 'northern'])

        relevant = []
        for d in disruptions:
            if _mentions_irrelevant_office_location(d):
                print(f"忽略與本路線無關的通知: {d}")
                continue
            relevant.append(d)

        if not relevant:
            return None
        details = "; ".join(relevant)
        return f"the route to office is disrupted 🔴 because {details}"
    except Exception as e:
        print(f"辦公室路線檢查失敗: {e}")
        return (
            "the route to office check failed. You can check manually here: "
            f"[Route]({CITYMAPPER_OFFICE_URL})"
        )


# 每週日檢查這四個場地的「即將到來的星期四/星期五」活動。The Common Press 和
# La Camionera 的「活動」頁面本身是前端渲染（Wix 的 Events app、Citymapper 風格
# 的純 SPA），但實測發現兩者的活動清單實際上都是嵌入 OutSavvy 的活動資料：
# The Common Press 頁面裡的日曆小工具其實是 outsavvy.com/calendar/1953（透過瀏覽器
# network capture 找到的），而 OutSavvy 本身也有該場地自己的 organiser 清單頁
# （純 HTML，可直接 requests 抓取），比起解析日曆小工具更穩定好讀。
_WLW_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

COMMONPRESS_EVENTS_URL = "https://www.outsavvy.com/organiser/the-common-press"
LA_CAMIONERA_EVENTS_URL = "https://www.outsavvy.com/organiser/la-camionera"
DALSTON_SUPERSTORE_EVENTS_URL = "https://dalstonsuperstore.com/whats-on/"
OLD_NUNSHEAD_EVENTS_URL = "https://www.theoldnunshead.co.uk/events"


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


def _scrape_dalston_superstore():
    """Dalston Superstore 的活動清單只給「幾號」+「星期幾文字」，沒有月份/年份，
    但清單本身是依時間順序排列、從今天開始。因此用「日期數字變小就代表跨月」來
    推算月份/年份，而不用另外解析月份標題。"""
    res = requests.get(DALSTON_SUPERSTORE_EVENTS_URL, headers=_WLW_HEADERS, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    today = datetime.now(LOCAL_TZ).date()
    month, year = today.month, today.year
    prev_day = 0

    events = []
    seen_hrefs = set()
    for li in soup.find_all("li", class_="event-thumbnail"):
        day_el = li.find("h3", class_="events__event-thumbnail__date")
        title_el = li.find("h2", class_="event-thumbnail__title")
        anchor = li.find("a")
        if not (day_el and title_el and anchor):
            continue

        href = anchor.get("href")
        if not href or href in seen_hrefs:
            continue

        try:
            day = int(day_el.get_text(strip=True))
        except ValueError:
            continue

        if day < prev_day:
            month += 1
            if month > 12:
                month = 1
                year += 1
        prev_day = day

        try:
            event_date = date(year, month, day)
        except ValueError:
            continue

        seen_hrefs.add(href)
        events.append(("Dalston Superstore", title_el.get_text(strip=True), event_date, href))
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


def check_wlw_events():
    """檢查四個場地（The Common Press、La Camionera、Dalston Superstore、
    Old Nun's Head）在「即將到來的星期四」與「即將到來的星期五」有哪些活動。
    沒有任何活動時回傳 None（晨報中完全不顯示這個區塊）；只要有任何一個來源
    抓取成功就以該來源結果為準，只有在四個來源「全部」失敗時才回傳備用訊息。"""
    result = _check_wlw_events_impl()
    print(f"WLW Events Check 判斷結果: {result}")
    return result


def _check_wlw_events_impl():
    today = datetime.now(LOCAL_TZ).date()
    thursday = today + timedelta(days=(3 - today.weekday()) % 7)
    friday = today + timedelta(days=(4 - today.weekday()) % 7)

    scrapers = [
        lambda: _scrape_outsavvy_organiser("The Common Press", COMMONPRESS_EVENTS_URL),
        lambda: _scrape_outsavvy_organiser("La Camionera", LA_CAMIONERA_EVENTS_URL),
        _scrape_dalston_superstore,
        _scrape_old_nunshead,
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
            f"[The Common Press]({COMMONPRESS_EVENTS_URL}) | "
            f"[La Camionera]({LA_CAMIONERA_EVENTS_URL}) | "
            f"[Dalston Superstore]({DALSTON_SUPERSTORE_EVENTS_URL}) | "
            f"[Old Nun's Head]({OLD_NUNSHEAD_EVENTS_URL})"
        )

    matches = [e for e in all_events if e[2] in (thursday, friday)]
    if not matches:
        return None

    lines = []
    for day_date, day_name in ((thursday, "Thursday"), (friday, "Friday")):
        day_matches = sorted(e for e in matches if e[2] == day_date)
        if not day_matches:
            continue
        lines.append(f"*{day_name} {day_date.strftime('%-d %B')}*")
        for venue, title, _, href in day_matches:
            lines.append(f"• [{title}]({href}) - {venue}")
    return "\n".join(lines)


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


def send_full_briefing(now_local, force_route_check, force_office_check, force_wlw_check):
    today = now_local.strftime("%Y-%m-%d (%a)")
    is_saturday = now_local.weekday() == 5  # 5 = Saturday
    is_sunday = now_local.weekday() == 6  # 6 = Sunday
    is_weekday = now_local.weekday() < 5  # 0-4 = Mon-Fri

    curr_price, lowest_price = get_octopus_agile_rates()
    curr_temp, temp_range, rain_msg = get_weather_forecast()
    gbp_hkd_rate = get_gbp_hkd_tt_rate()

    briefing = (
        f"☀️ *晨間晨報 ({today})*\n\n"
        f"⚡ *Octopus Agile 即時電價*\n"
        f"• 當前電價: `{curr_price}`\n"
        f"• 未來 24h 最低電價 3 小時區段: `{lowest_price}`\n\n"
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

    if is_saturday or force_route_check:
        route_status = check_route_disruption()
        briefing += (
            f"\n🏋️ *Saturday Route Check (Virgin Active Strand)*\n"
            f"{route_status}\n\n"
            f"🔗 [Open Citymapper Route]({CITYMAPPER_GYM_URL})\n"
        )

    if is_sunday or force_wlw_check:
        wlw_events = check_wlw_events()
        if wlw_events is not None:
            briefing += (
                f"\n🎀 *Upcoming Thu/Fri Events*\n"
                f"{wlw_events}\n"
            )

    briefing += "\n祝你有美好的一天！💪"
    send_telegram(briefing)


def send_route_only_update(now_local):
    """Saturday 10:30-11:15 高頻路線提醒，只回報路況，不含天氣/電價"""
    route_status = check_route_disruption()
    msg = (
        f"🕐 *Route Check ({now_local.strftime('%H:%M')})*\n"
        f"{route_status}\n\n"
        f"🔗 [Open Citymapper Route]({CITYMAPPER_GYM_URL})"
    )
    send_telegram(msg)


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
    else:
        send_full_briefing(now_local, force_route_check, force_office_check, force_wlw_check)


if __name__ == "__main__":
    main()
