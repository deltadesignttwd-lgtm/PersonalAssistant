import json
import os
import re
import time
import requests
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

# Citymapper 路線資訊 (平日通勤: Home → Bank [DLR] → Old Street [Northern line]
# → Frank Reynolds Architects, Shepherdess Walk)。解碼確認為完整路線。
# 原本還有另一條經 Canary Wharf [DLR] → Liverpool Street [Elizabeth line] 的路線，
# 使用者已決定改用這條經 Bank/Old Street 的路線作為唯一常用路線，故移除前者。
CITYMAPPER_OFFICE_URL = "https://citymapper.com/trip/signature?signature=eJyNlNtu4jAQhl8l8u2S4kMSHO52VVZdLaKr0oqLqorceIAswWYds22FePfaCaQEtIc7PDP%2B558PT3YoFwYNA0JTznsBklsjbKGVCzFOIhcBJd1hh4SUBqrK%2FUbTJWyWYKQ7BjNRrnrBWCupVS94%2BI7clVxrI%2BvKmFzFTpkNeiG%2BwinFnPsCJdbg01%2BNUKvgDt6ULmUVfDb5srCQ2wrtXdVPkxVKwqurHLhjCQuv%2BbhDsqisULmXIITGXdspo951fmgfJREndXdCB753oTJ3%2B1CMcD%2FFPrrWsnb04sbx56q9Hw%2FS%2BjqOSOQzVmfwWlifHsNLUS3FOhsxzGLuTe9OrZCE45Yg%2BuJm9QJLEPJFvLlQxPBJa%2BtgVE7YhYzeWsiKmuEjuh7foSfvyQrT6VsbtXqT5XqrbN3wGDne%2FVEKO9dmnbVevZqrahPeVnad3aOnxv4HW9wF28xy5BIT5kB7MJyn9BIs6fO%2Fgz0TOGdHoxN0t6WcWgNgu%2Fxowv6H30Qb656r6kI8%2Fh0dgOyP%2FGpMk0xOOvBaY3VqdskwYWfPM8G8g9Fvx2E5SOK150av2xf2oT9il4xpn%2FwLMk0axIOUob2ff2OKHLINNPYY8ZQNLA6K21VY1qt8pFioRWbg1xYq65j4koQM8ucc0%2FA5wjKMaCLCFCQJY8ZBcgBM8BydgN51Pwd%2Bn8hhoxjn8ennYDoiLIhvHurtt0UTpJgmIeYhTe4pHbJ4SMgnTIYY9ye3s2%2FTGy%2FwG0zVTBDv3wGqG18e"

# Citymapper 路線資訊 (平日下班: Frank Reynolds Architects, Shepherdess Walk → walk to
# Old Street → Old Street [Northern line] → Bank → Bank [DLR] → Lewisham → home)。
# 解碼確認為 CITYMAPPER_OFFICE_URL 的反方向，使用同樣兩條 TfL line（Northern/DLR）。
CITYMAPPER_HOME_FROM_OFFICE_URL = "https://citymapper.com/trip/signature?signature=eJyNlF1v2yAUhv%2BKxe3ihg9%2F4Nx1aqZNi9Kp2dSLqkLMkMSLAxkmS6so%2F32AnQ%2B3Wrs7n3PgfQ%2BPOexByQ0YRQgjSgcREFvDbaWVS%2BEixS4jlXDBHpRaG9G4T5CiqyRLMpoPYngFEc4pAW6h4mvpyxO5q5olX4ODS%2F4yrFJCPrkCcWEtF17iYQ9E1ViuSr8jI6TvnMFgXHZmKc6CE82LYFQp5vZ2awEcIgp9eq1F8N%2FxeuXj5ry%2FoCQoFBhlvmQ1k0%2BV9fXbWsyskdKyMfEd73sIEngiAD5yFXSXkosdf%2FbQKLzwtYarxom6lNFbK1kVcD2AqTZ2KY0Cj74ry03fOPRq9YaVeqtsByokjgLfam7n2qzZudkpEzO%2F8VTy3bXZx%2FYUZ76wTzc0fYaLCMEtXlrg13jR8D26fYGXCFF%2ByfB0N3ocCfwvjjeTuz7C4x%2Fp0UPpP%2FEFRjdMjHvkjj2xoP8SXvImPT8HRTcG7RTMjV6fLtdJekwgSelruniYvU3XGVB0nDNw8MffmKqUbCPb%2FgjyDRm56BS3q7jWSrig41epBTPy91Y21hEJsjQrUyKKeE4xjxOZ05iTMolLkeOfPCeCYAwuOO8BF8LIJgz%2FbCk37jILF0b3rttBNAl2g%2BjHV7%2Bp90yEycu70XP34%2FKZ%2BOR%2B8yq6k89K16KJrk25rKwsbRPeDVu1qzDEWYxgDMl3REYJHiXoA0QjCIfT2%2Fsvs89e8Y80TXv69PAXRWdfxg%3D%3D"

def _parse_iso(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))


def _get_weather_forecast_open_meteo(max_attempts=3):
    """透過 Open-Meteo API 取得 Lewisham 天氣預報（主要來源），暫時性錯誤（如 503/
    逾時）會重試。重試後仍失敗則直接 raise，交給 get_weather_forecast() 改用備援
    來源，而不是在這裡就回傳 N/A。"""
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
            # 網路/HTTP 錯誤（例如 503 或逾時）視為暫時性，重試
            last_error = e
            print(f"Weather API 錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt < max_attempts:
                time.sleep(3 * attempt)
        except Exception as e:
            # 非網路性錯誤（例如回應格式異常）不重試，直接視為失敗
            last_error = e
            break

    raise last_error


# MET Norway（挪威氣象局）的 Locationforecast API 作為 Open-Meteo 的備援來源：全球
# 範圍（含 Lewisham）、免費、不需要 API key，但依官方使用條款必須帶上能辨識來源應用
# 的 User-Agent（不是驗證/擋爬蟲用途，純粹是他們的規範）。這組資料沒有像 Open-Meteo
# 一樣的「降雨機率」百分比欄位（實測 probability_of_precipitation 經常缺漏），因此
# 改用 next_1_hours.details.precipitation_amount（未來 24h 內任一小時的最大降雨量，
# 單位 mm）搭配固定門檻來判斷，標註「備援資料來源」避免跟主要來源的措辭混淆。
METNO_FORECAST_API_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
_METNO_HEADERS = {
    "User-Agent": "PersonalAssistant (github.com/deltadesignttwd-lgtm/PersonalAssistant)",
}


def _get_weather_forecast_metno(max_attempts=3):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.get(
                METNO_FORECAST_API_URL, params={"lat": LAT, "lon": LON},
                headers=_METNO_HEADERS, timeout=10,
            )
            res.raise_for_status()
            data = res.json()
            break
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"MET Norway weather API 錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt < max_attempts:
                time.sleep(3 * attempt)
    else:
        raise last_error

    timeseries = data.get("properties", {}).get("timeseries", [])
    if not timeseries:
        raise RuntimeError("MET Norway 回應中沒有 timeseries 資料")

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=24)

    curr_temp = None
    temps = []
    max_precip_mm = 0.0
    for entry in timeseries:
        entry_time = _parse_iso(entry["time"])
        if entry_time > window_end:
            continue
        details = entry.get("data", {}).get("instant", {}).get("details", {})
        if "air_temperature" in details:
            temps.append(details["air_temperature"])
            if curr_temp is None:
                curr_temp = details["air_temperature"]
        next_hour_details = entry.get("data", {}).get("next_1_hours", {}).get("details", {})
        if "precipitation_amount" in next_hour_details:
            max_precip_mm = max(max_precip_mm, next_hour_details["precipitation_amount"])

    if curr_temp is None or not temps:
        raise RuntimeError("MET Norway 回應中找不到溫度資料")

    if max_precip_mm >= 1.0:
        rain_summary = f"⚠️ 今天可能有降雨（備援資料來源，預估單小時最大降雨量 {max_precip_mm:.1f}mm）！記得帶傘 🌧️"
    elif max_precip_mm > 0:
        rain_summary = f"🌦️ 可能有局部短暫雨（備援資料來源，預估單小時最大降雨量 {max_precip_mm:.1f}mm）。"
    else:
        rain_summary = "☀️ 今天預計無明顯降雨（備援資料來源）。"

    return f"{round(curr_temp)}°C", f"{round(min(temps))}°C ~ {round(max(temps))}°C", rain_summary


def get_weather_forecast():
    """取得 Lewisham 天氣預報：主要來源 Open-Meteo，重試 3 次後仍失敗則改用
    MET Norway 作為備援（兩者都免費、不需要 API key）。2026-11-15 跟 2026-11-17
    都遇到 Open-Meteo 連續 3 次、每次 10 秒逾時仍失敗的情況 —— 不是單次偶發的
    網路問題，而是那段時間 Open-Meteo 本身真的連不上/太慢，單靠加重試次數並不會
    解決，所以改成有獨立備援來源。兩個來源都失敗才回傳 N/A/擷取失敗。"""
    try:
        return _get_weather_forecast_open_meteo()
    except Exception as e:
        print(f"Open-Meteo 天氣查詢最終失敗，改用備援來源 MET Norway: {e}")

    try:
        return _get_weather_forecast_metno()
    except Exception as e:
        print(f"MET Norway 備援天氣查詢也失敗: {e}")
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


def _get_tfl_line_disruptions(line_ids, max_attempts=3):
    """查詢指定 TfL line id 的即時狀態，回傳「非正常服務」狀態的結構化清單（可能為空）。
    每筆為 {"line": 路線名稱, "severity": statusSeverityDescription, "reason": reason 文字}。
    severity 直接用 TfL API 本身的結構化欄位（例如 "Severe Delays"/"Minor Delays"/
    "Part Suspended"），不用字串比對去猜測嚴重程度。
    實測在 2026-11-05 17:30 的下班檢查遇到 TfL API 10 秒逾時（Read timed out），導致
    整個下班路線檢查被判定為失敗並發出錯誤訊息。加上跟 get_hither_green_to_strand_route()
    一樣的重試機制，讓單次逾時不會直接讓檢查失敗。"""
    ids = ",".join(line_ids)
    tfl_url = f"https://api.tfl.gov.uk/Line/{ids}/Status"
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.get(tfl_url, timeout=10)
            res.raise_for_status()
            lines = res.json()
            break
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"TfL line status API 錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt < max_attempts:
                time.sleep(3 * attempt)
    else:
        raise last_error

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


# 原本想監控官方的 tfl.gov.uk/status-updates/strikes 頁面，但該頁面被 Cloudflare
# Turnstile 互動式驗證完全擋死——plain requests 直接拿到 403，連真的 headless 瀏覽器
# 都卡在「Verification required」驗證頁面逾時，無法繞過（跟其他頁面遇到的「純 JS
# 運算挑戰」不同，這是真的需要人互動的驗證）。改成直接查 api.tfl.gov.uk（這個
# subdomain 沒有被同一套 WAF 擋），用 /Line/Mode/{modes}/Status（而不是像
# _get_tfl_line_disruptions() 那樣查特定 line id，因為罷工可能影響任何一條線，不只
# office 通勤用到的那幾條），篩選出 reason/disruption 文字裡提到 "strike"/
# "industrial action" 的項目。
# 已知限制（目前無法驗證，誠實記錄）：寫這段程式的當下沒有真的在排的罷工，所以沒辦法
# 實測 TfL 到底會提前幾天把罷工資訊放進這個 API——有可能跟 Road Disruption API
# 一樣只在「已經開始」才會出現，而不是真的提前一天就能看到。只能等下次真的有罷工公告
# 時，看實際跑出來的結果才能確定。
TFL_STRIKE_CHECK_MODES = "tube,dlr,overground,elizabeth-line,tram"
_STRIKE_KEYWORDS = ("strike", "industrial action")


def _get_strike_disruptions(modes=TFL_STRIKE_CHECK_MODES, max_attempts=3):
    """查詢 TfL Line Status API（依 mode，涵蓋 tube/DLR/Overground/Elizabeth line/
    Tram 全部路線），回傳 reason/disruption 文字中提到罷工關鍵字的項目（可能為空）。
    每筆為 {"line", "reason", "validity_periods"}，validity_periods 是 TfL 原始的
    disruption.validityPeriods（可能為空清單——不保證每次都有結構化日期）。"""
    url = f"https://api.tfl.gov.uk/Line/Mode/{modes}/Status?detail=true"
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.get(url, timeout=15)
            res.raise_for_status()
            lines = res.json()
            break
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"TfL strike check API 錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt < max_attempts:
                time.sleep(3 * attempt)
    else:
        raise last_error

    strikes = []
    for line in lines:
        for status in line.get("lineStatuses", []):
            reason = status.get("reason") or ""
            disruption = status.get("disruption") or {}
            description = disruption.get("description") or ""
            additional_info = disruption.get("additionalInfo") or ""
            combined = f"{reason} {description} {additional_info}".lower()
            if _text_mentions_any(combined, _STRIKE_KEYWORDS):
                strikes.append({
                    "line": line.get("name"),
                    "reason": reason or description or additional_info,
                    "validity_periods": disruption.get("validityPeriods") or [],
                })
    return strikes


def _strike_covers_date(validity_periods, target_date):
    for period in validity_periods:
        from_str = period.get("fromDate")
        to_str = period.get("toDate")
        if not from_str or not to_str:
            continue
        try:
            from_date = _parse_iso(from_str).astimezone(LOCAL_TZ).date()
            to_date = _parse_iso(to_str).astimezone(LOCAL_TZ).date()
        except ValueError:
            continue
        if from_date <= target_date <= to_date:
            return True
    return False


def check_tube_strikes(now_local):
    """檢查明天是否有地鐵/DLR/Overground/Elizabeth line/Tram 的罷工。沒有時回傳
    None（跟其他檢查一樣「沒事就不提」）。查詢失敗時也回傳 None 而不是錯誤訊息——
    這是額外的安全提醒，查不到就等下一次排程再試，不值得為了這個額外發一則「查詢
    失敗」的訊息。"""
    result = _check_tube_strikes_impl(now_local)
    print(f"Strike Check 判斷結果: {result}")
    return result


def _check_tube_strikes_impl(now_local):
    tomorrow = now_local.date() + timedelta(days=1)
    try:
        strikes = _get_strike_disruptions()
    except Exception as e:
        print(f"罷工檢查失敗: {e}")
        return None

    relevant = []
    for s in strikes:
        periods = s["validity_periods"]
        # 沒有結構化日期時保守地視為相關（寧可多提醒一次，也不要漏掉真正的罷工——
        # 這跟其他檢查「查不到就不提」的預設不同，因為這是安全性較高的提醒）。
        if not periods or _strike_covers_date(periods, tomorrow):
            relevant.append(s)

    if not relevant:
        return None
    return "\n\n".join(f"{s['line']}: {s['reason']}" for s in relevant)


# nationalrail.co.uk 的 journey planner 頁面本身是 Next.js SPA（初次載入的 HTML 裡沒有
# 實際班次資料，要等前端 JS 執行後才呼叫 API 取得），但實測發現它背後真正呼叫的
# jpservices.nationalrail.co.uk/journey-planner 是一個一般公開、不需登入、也沒有任何
# bot 驗證/Cloudflare 擋下的 JSON API：直接用 requests.post() 帶同樣的查詢參數，就能
# 拿到跟官網一樣的即時資料（scheduled/realtime 時間、delayInMinutes、rawStatus、
# serviceBulletins），完全不需要啟動瀏覽器。
NATIONALRAIL_JOURNEY_API_URL = "https://jpservices.nationalrail.co.uk/journey-planner"
NATIONALRAIL_JOURNEY_PLANNER_URL = (
    "https://www.nationalrail.co.uk/journey-planner/?type=single&origin=LEW&destination=CHX"
)

MORNING_TRAIN_ORIGIN_CRS = "LEW"
MORNING_TRAIN_DESTINATION_CRS = "CHX"
MORNING_TRAIN_DEPARTURE_HOUR = 8
MORNING_TRAIN_DEPARTURE_MINUTE = 10

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


def _query_nationalrail_journeys(origin_crs, destination_crs, departure_local, max_attempts=3):
    """呼叫 jpservices.nationalrail.co.uk/journey-planner，取得指定出發時間附近的即時
    班次清單（實測一次會回傳目標時間前後共約 10 班，不是只有剛好那一班）。
    departure_local 需帶時區資訊（LOCAL_TZ），函式內部自己轉成 API 要求的 UTC ISO 格式。"""
    departure_utc = departure_local.astimezone(timezone.utc)
    payload = {
        "origin": {"crs": origin_crs, "group": False},
        "destination": {"crs": destination_crs, "group": False},
        "outwardTime": {"travelTime": departure_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "type": "DEPART"},
        "fareRequestDetails": {"passengers": {"adult": 1, "child": 0}, "fareClass": "ANY", "railcards": []},
        "directTrains": False,
        "reducedTransferTime": False,
        "onlySearchForSleeper": False,
        "overtakenTrains": True,
        "useAlternativeServices": False,
        "increasedInterchange": "ZERO",
    }
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.post(NATIONALRAIL_JOURNEY_API_URL, json=payload, timeout=15)
            res.raise_for_status()
            return res.json().get("outwardJourneys", [])
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"National Rail journey API 錯誤（第 {attempt}/{max_attempts} 次嘗試）: {e}")
            if attempt < max_attempts:
                time.sleep(3 * attempt)
    raise last_error


def _find_matching_journey(journeys, departure_local):
    """從回傳的班次清單中找出 scheduled departure 剛好等於目標時間的那一班。"""
    target_utc = departure_local.astimezone(timezone.utc).replace(second=0, microsecond=0)
    for journey in journeys:
        scheduled = journey.get("timetable", {}).get("scheduled", {}).get("departure")
        if not scheduled:
            continue
        try:
            scheduled_dt = _parse_iso(scheduled)
        except ValueError:
            continue
        if scheduled_dt == target_utc:
            return journey
    return None


def check_morning_train_status(now_local):
    """檢查週一到週五 {MORNING_TRAIN_DEPARTURE_HOUR}:{MORNING_TRAIN_DEPARTURE_MINUTE}
    這一班特定列車（Lewisham → Charing Cross, Southeastern）的即時狀態——跟
    check_office_route_disruption() 查整條 TfL line 狀態不同，這裡直接查這一班車實際
    的即時資料（delay、取消、相關 service bulletin）。列車正常時回傳 None，跟其他
    平日通勤檢查一樣「沒事就不提」。"""
    result = _check_morning_train_status_impl(now_local)
    print(f"Morning Train Check 判斷結果: {result}")
    return result


def _check_morning_train_status_impl(now_local):
    departure_local = now_local.replace(
        hour=MORNING_TRAIN_DEPARTURE_HOUR, minute=MORNING_TRAIN_DEPARTURE_MINUTE,
        second=0, microsecond=0,
    )
    try:
        journeys = _query_nationalrail_journeys(
            MORNING_TRAIN_ORIGIN_CRS, MORNING_TRAIN_DESTINATION_CRS, departure_local
        )
    except Exception as e:
        print(f"Morning Train 查詢失敗: {e}")
        return (
            "couldn't check this train. Check manually: "
            f"[National Rail]({NATIONALRAIL_JOURNEY_PLANNER_URL})"
        )

    journey = _find_matching_journey(journeys, departure_local)
    if journey is None:
        return (
            "couldn't find this train in today's results. Check manually: "
            f"[National Rail]({NATIONALRAIL_JOURNEY_PLANNER_URL})"
        )

    delay = journey.get("delayInMinutes") or 0
    raw_status = (journey.get("rawStatus") or "").upper()
    # 2026-11-16 bug: rawStatus 的「正常」值不是只有 "NORMAL" 一種（例如這天看到的是
    # "ONTIME"，delay 仍是 0），用允許清單去猜「正常」的字串會漏掉沒見過的正常值，
    # 跟 2026-10-08 Stockwell 那次誤判同一種錯誤。改成只信任真正可靠的訊號：
    # delayInMinutes 本身，加上明確的取消關鍵字（取消有時 delayInMinutes 會是 0）。
    is_disrupted = delay > 0 or "CANCEL" in raw_status
    if not is_disrupted:
        return None

    status_bits = [f"status: {raw_status or 'unknown'}"]
    if delay:
        status_bits.append(f"delay: {delay} min")
    realtime_dep = journey.get("timetable", {}).get("realtime", {}).get("departure")
    if realtime_dep:
        try:
            status_bits.append(f"now expected {_parse_iso(realtime_dep).astimezone(LOCAL_TZ).strftime('%H:%M')}")
        except ValueError:
            pass

    message = "🔴 " + ", ".join(status_bits)
    bulletins = [
        b.get("description", "") for b in journey.get("serviceBulletins", [])
        if b.get("category") != "Accessibility" and b.get("description")
    ]
    if bulletins:
        message += "\n" + "\n".join(bulletins)
    return message


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


def poll_telegram_commands(now_local):
    """輪詢 Telegram，檢查使用者是否主動發送 /briefing 指令；若有，立即觸發跟
    07:00 排程內容一樣的完整晨報回覆，依照「今天」實際星期幾顯示對應區塊。只處理
    來自 TG_CHAT_ID 本人的訊息，其他來源（例如別人誤發訊息給這個 bot）一律忽略，
    不會觸發任何動作也不會被當成「已處理」而推進 offset 之外的行為影響。"""
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
            send_full_briefing(now_local, False)
            triggered = True
        else:
            print(f"收到不認識的訊息，忽略: {text!r}")

    _save_telegram_offset(highest_update_id)
    print(f"已處理到 update_id={highest_update_id}" + ("（已觸發指令回應）" if triggered else ""))


def send_full_briefing(now_local, force_office_check):
    today = now_local.strftime("%Y-%m-%d (%a)")
    is_weekday = now_local.weekday() < 5  # 0-4 = Mon-Fri

    curr_temp, temp_range, rain_msg = get_weather_forecast()
    gbp_hkd_rate = get_gbp_hkd_tt_rate()

    briefing = (
        f"☀️ *晨間晨報 ({today})*\n\n"
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

        train_status = check_morning_train_status(now_local)
        if train_status is not None:
            departure_label = f"{MORNING_TRAIN_DEPARTURE_HOUR:02d}:{MORNING_TRAIN_DEPARTURE_MINUTE:02d}"
            briefing += (
                f"\n🚆 *{departure_label} Lewisham → Charing Cross*\n"
                f"{train_status}\n"
                f"🔗 [National Rail]({NATIONALRAIL_JOURNEY_PLANNER_URL})\n"
            )

    # 罷工提醒跟平日/週末無關，每天都檢查——罷工也可能發生在週末。
    strike_status = check_tube_strikes(now_local)
    if strike_status is not None:
        briefing += (
            f"\n🚨 *Strike Alert (tomorrow)*\n"
            f"{strike_status}\n"
        )

    briefing += "\n祝你有美好的一天！💪"
    send_telegram(briefing)


def send_evening_update(now_local):
    """平日 17:30 下班路線提醒。核心是 Office → Home 的路況，路線正常時完全不產生
    內容（使用者只想在真的有中斷時才收到通知）。額外獨立檢查明天是否有罷工——跟路況
    檢查不同，這個不需要「有問題才提」，只要明天真的有罷工就會發送，即使下班路線本身
    正常。兩者都沒有內容時完全不發送任何訊息。"""
    home_route_status = check_home_from_office_route_disruption()
    strike_status = check_tube_strikes(now_local)

    msg_parts = []
    if home_route_status is not None:
        msg_parts.append(
            f"🏠 *Office → Home Route Check*\n"
            f"{home_route_status}\n\n"
            f"🔗 [Open Citymapper Route]({CITYMAPPER_HOME_FROM_OFFICE_URL})"
        )
    if strike_status is not None:
        msg_parts.append(
            f"🚨 *Strike Alert (tomorrow)*\n"
            f"{strike_status}"
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
    force_office_check = os.environ.get("FORCE_OFFICE_CHECK", "").lower() == "true"

    if mode == "evening":
        send_evening_update(now_local)
    elif mode == "poll_commands":
        poll_telegram_commands(now_local)
    else:
        send_full_briefing(now_local, force_office_check)


if __name__ == "__main__":
    main()
