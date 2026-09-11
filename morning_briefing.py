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

EVENTBRITE_WLW_URL = "https://www.eventbrite.co.uk/d/united-kingdom--london/lesbian-events/"

# Citymapper 路線資訊 (Lewisham 至 Virgin Active Strand)
CITYMAPPER_GYM_URL = "https://citymapper.com/trip/signature?signature=eJx9U9Fu2jAU%2FZXIryPF145J4G2qkDqtYlNZ14eqskxswGuwmWNKJ8S%2F104gSzRpb%2FG9x%2Bcen3tyQqVwaJYAMJKPEiQPTnhtTSgRVkCoKCPD4YSElE7VdfhGS%2B%2BEkaPk3hppzSh5%2FIoCsLTWyabP4IYBBgqjFN8AgbygEWDETsX2T%2B022iSfS6%2FfVNKSoXMA%2FHJcG6neAwiHY6U2ke75hKSuvTClaoQSNtQ5pSTKLC%2BTs0lWNIMxkDyO1YaH2xcwwuMpjtWdlY2Yo6he47nu7rN82lzHGWSx4y1X79rH9r066nordnxOMWVFFH3qSwHIcGcZut0Kp83m1tlgWyhvlZBH8Se0gsaehGhAHQaEkrMHr7hubhbar3xGi4ZXVA9CV8s5eokyvXADKY12b%2Fe8tAcTO9m1cGX5Xgm%2Ftm7HO%2FV9Xi6fIkUH6oseANFL%2B9q%2Fq8gIHm6CMtbfRMzANQJtAtbO7jozB5PmiwcO%2FJKFf5ZGxoDZf7fGcEFpO4sRQOfo1d7pUvG9atXSRq1Tmwvn4TWtmvxefQ9auFO%2FD6r2wbsIWdMcJipbpWwFeZrh9SRdsbxMczllUzrJlaQC9ZZyGv4DMUlwyRItCtb%2FB5ZzoAm7e2xy73VbJJhMUlykBH5ANsvIjBafMMwwHi%2B%2BPX1Z3kWCN%2BXq9gXs%2FAF%2FCxLH"

# Citymapper 路線資訊 (平日通勤: Home 41D Eastdown Park → Canary Wharf [DLR] → Liverpool Street [Elizabeth line])
# 兩段連結內容已解碼確認：leg1 是 home -> Canary Wharf (DLR)，leg2 是 Canary Wharf -> Liverpool Street (Elizabeth line)
CITYMAPPER_OFFICE_LEG1_URL = "https://citymapper.com/trip/signature?signature=eJx9U9uO2jAQ%2FZXIryXL%2BBZiXgtSq6LtqhfxsFpZ3thACtjUMWVXiH9fO2RpoFLfMnNm5pw5Ex9RpTwaZ4JiOsiQ3nsVamdjhlBWxIyxOgZHVDnndRM%2FEcd3HApM8SCHO8AjVjIUC63amgR%2FVFb512y%2BUn6BThH45WVttXmJIMRwY5ZpzOMR6boJylapC2MB1%2FSCjxJ71TGygpUdIRklutrK2N0VIxgKSNmt062Ig9qsU9xc%2Bvmo4G0%2FMBAJCk6alzokfGYOdbNSWzmlQHmZVB%2F7WjCUcLGiW7DdbzL7lkatjNIH9RpBCtBTEbyyTaSIKe%2F2wci6dfARpb6nJC8of6Wg1RzcTlZub0NrzHvmvfdho8LC%2Ba28qO5UXIBrgXIi9T16Ou%2F013Eiipt7g%2BgbHk9M2NlwATTNX3i3vVh2wzHlRJB%2Fz0KG9P9n4cCpaFkIlMXNWXoc05mcmyZME3JKzu18XRm5M90yJNnuzbLj3a%2FzjbM6Bp31tV1Kb37v44xoZCrBvBQAUOYMzCJn5lnnpSog18ChVAZXhX5GvRMdkdLam6Z9ArN2%2BCD7%2BSWVXD2N9KMV55WAlgz3nwbDk2yqmqDdwWYPyq%2Fb9xHqM0qAFHkURMgPLMYcxkA%2FAB4DDO%2B%2Fzj9%2F%2F5Qm%2FTG%2BOe%2FIT28FUw8L"
CITYMAPPER_OFFICE_LEG2_URL = "https://citymapper.com/trip/signature?signature=eJyFUstu2zAQ%2FBWD10YJHyIp%2BVoIaAEjLZACPgQBQUu0zUYmXYpqkhr%2B93IlO36kQG%2FcneXO7OzuUK0Dmk64lORmgpo%2B6Gi9SxlCc5YyxjUp2KHa%2B9B06Yk4ueVEypzeZPgWF0QIilKh0xsD8Mz%2BNmHrfTt5iMGYiPYJ%2FBmUdY15TQU4ha1ZQavHHWpsF7Wr4WfOrxSwYhBQH0kxl%2BXASQQQLoPfKPNqI%2BCftdPhbb7WYakqTgWGCutU6n7ohvAdoRzSG98MSl90%2Bwxxd2Jg7MAgOQEo%2Bn8xVDNV6S5WgKTpdueic4rfXTt5MVpRzaDn2ujmRb9BLeNncmLQrksdUyr4PhplB78fUdXaP3ph4npmnUFPoDjq8FHUMEv0W1X73gHMjoljp%2B%2BtjksfNupymOYevr6DV6oVVMzR0zjpaV80Ly%2F3RUt%2BsS8iiRhvhMr%2FGH9ZuocZt8HWRm3NSMYI2BrM6rDM%2FjlrvWtScLDLupUK5ldvupjGhZKcFU0tMc%2BEzmWWF4xlxWJRZ0RobAqCZW0EOjPz%2BsYxE2w8hpKfH%2Fjo3WQwbzjuaEeAYioyXGSU%2FiDlNBdTIj5hMsX47v7b%2FOvDF2iSnO3GEfj%2BL2T%2BAN8%3D"

# Citymapper 路線資訊 (平日通勤替代路線: Home → Bank [DLR] → Old Street [Northern line]
# → Frank Reynolds Architects, Shepherdess Walk)。解碼確認為完整替代路線（非前兩段的延伸）。
CITYMAPPER_OFFICE_ALT_URL = "https://citymapper.com/trip/signature?signature=eJyNlNtu4jAQhl8l8u2S4kMSHO52VVZdLaKr0oqLqorceIAswWYds22FePfaCaQEtIc7PDP%2B558PT3YoFwYNA0JTznsBklsjbKGVCzFOIhcBJd1hh4SUBqrK%2FUbTJWyWYKQ7BjNRrnrBWCupVS94%2BI7clVxrI%2BvKmFzFTpkNeiG%2BwinFnPsCJdbg01%2BNUKvgDt6ULmUVfDb5srCQ2wrtXdVPkxVKwqurHLhjCQuv%2BbhDsqisULmXIITGXdspo951fmgfJREndXdCB753oTJ3%2B1CMcD%2FFPrrWsnb04sbx56q9Hw%2FS%2BjqOSOQzVmfwWlifHsNLUS3FOhsxzGLuTe9OrZCE45Yg%2BuJm9QJLEPJFvLlQxPBJa%2BtgVE7YhYzeWsiKmuEjuh7foSfvyQrT6VsbtXqT5XqrbN3wGDne%2FVEKO9dmnbVevZqrahPeVnad3aOnxv4HW9wF28xy5BIT5kB7MJyn9BIs6fO%2Fgz0TOGdHoxN0t6WcWgNgu%2Fxowv6H30Qb656r6kI8%2Fh0dgOyP%2FGpMk0xOOvBaY3VqdskwYWfPM8G8g9Fvx2E5SOK150av2xf2oT9il4xpn%2FwLMk0axIOUob2ff2OKHLINNPYY8ZQNLA6K21VY1qt8pFioRWbg1xYq65j4koQM8ucc0%2FA5wjKMaCLCFCQJY8ZBcgBM8BydgN51Pwd%2Bn8hhoxjn8ennYDoiLIhvHurtt0UTpJgmIeYhTe4pHbJ4SMgnTIYY9ye3s2%2FTGy%2FwG0zVTBDv3wGqG18e"


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

        # 找出未來 24 小時內的最低電價
        window_end = now + timedelta(hours=24)
        upcoming = [r for r in data if now <= _parse_iso(r['valid_from']) < window_end]
        if not upcoming:
            upcoming = data

        lowest_entry = min(upcoming, key=lambda x: x['value_inc_vat'])
        lowest_val = round(lowest_entry['value_inc_vat'], 2)
        lowest_time = _parse_iso(lowest_entry['valid_from']).astimezone(LOCAL_TZ).strftime("%H:%M")

        return current_rate, f"{lowest_val} p/kWh at {lowest_time}"
    except Exception as e:
        print(f"Octopus API 錯誤: {e}")
        return "擷取失敗", "擷取失敗"


def get_weather_forecast():
    """透過 Open-Meteo API 取得 Lewisham 天氣預報"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m&hourly=temperature_2m,precipitation_probability&forecast_days=1&timezone=Europe%2FLondon"
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
    except Exception as e:
        print(f"Weather API 錯誤: {e}")
        return "N/A", "N/A", "擷取失敗"


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


def check_route_disruption():
    """檢查前往 Virgin Active Strand 路線（Lewisham → Charing Cross, Southeastern 直達車）的即時路況"""
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
    """檢查平日通勤路線（Lewisham → Canary Wharf [DLR] → Liverpool Street [Elizabeth line]，
    或替代路線 Lewisham → Bank [DLR] → Old Street [Northern line]）的即時路況"""
    try:
        # 路線由使用者提供的 Citymapper 連結解碼確認：
        # leg1 = home -> Canary Wharf (DLR)，leg2 = Canary Wharf -> Liverpool Street (Elizabeth line)
        # 替代路線 = home -> Bank (DLR) -> Old Street (Northern line, 經 Moorgate)
        disruptions = _get_tfl_line_disruptions(['dlr', 'elizabeth', 'northern'])

        relevant = []
        for d in disruptions:
            if _mentions_irrelevant_office_location(d):
                print(f"忽略與本路線無關的通知: {d}")
                continue
            relevant.append(d)

        if not relevant:
            return "the route to office is clear ✅"
        details = "; ".join(relevant)
        return f"the route to office is disrupted 🔴 because {details}"
    except Exception as e:
        print(f"辦公室路線檢查失敗: {e}")
        return (
            "the route to office check failed. You can check manually here: "
            f"[Leg 1]({CITYMAPPER_OFFICE_LEG1_URL}) / [Leg 2]({CITYMAPPER_OFFICE_LEG2_URL}) / "
            f"[Alt Route]({CITYMAPPER_OFFICE_ALT_URL})"
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


def send_full_briefing(now_local, force_route_check, force_office_check):
    today = now_local.strftime("%Y-%m-%d (%a)")
    is_saturday = now_local.weekday() == 5  # 5 = Saturday
    is_weekday = now_local.weekday() < 5  # 0-4 = Mon-Fri

    curr_price, lowest_price = get_octopus_agile_rates()
    curr_temp, temp_range, rain_msg = get_weather_forecast()

    briefing = (
        f"☀️ *晨間晨報 ({today})*\n\n"
        f"⚡ *Octopus Agile 即時電價*\n"
        f"• 當前電價: `{curr_price}`\n"
        f"• 未來 24h 最低電價: `{lowest_price}`\n\n"
        f"🌤️ *Lewisham 天氣預報*\n"
        f"• 當前氣溫: `{curr_temp}`\n"
        f"• 今日氣溫區間: `{temp_range}`\n"
        f"• 降雨提醒: {rain_msg}\n"
        f"\n👭 *WLW Events Today*\n"
        f"🔗 [Check today's London WLW events]({EVENTBRITE_WLW_URL})\n"
    )

    if is_weekday or force_office_check:
        office_status = check_office_route_disruption()
        briefing += (
            f"\n🚇 *Office Route Check*\n"
            f"{office_status}\n"
            f"🔗 [Leg 1: Home → Canary Wharf]({CITYMAPPER_OFFICE_LEG1_URL}) | "
            f"[Leg 2: Canary Wharf → Liverpool Street]({CITYMAPPER_OFFICE_LEG2_URL}) | "
            f"[Alt Route: Home → Old Street]({CITYMAPPER_OFFICE_ALT_URL})\n"
        )

    if is_saturday or force_route_check:
        route_status = check_route_disruption()
        briefing += (
            f"\n🏋️ *Saturday Route Check (Virgin Active Strand)*\n"
            f"{route_status}\n\n"
            f"🔗 [Open Citymapper Route]({CITYMAPPER_GYM_URL})\n"
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
    now_local = datetime.now(LOCAL_TZ)
    mode = os.environ.get("MODE", "full").strip().lower()
    force_route_check = os.environ.get("FORCE_ROUTE_CHECK", "").lower() == "true"
    force_office_check = os.environ.get("FORCE_OFFICE_CHECK", "").lower() == "true"

    if mode == "route_only":
        send_route_only_update(now_local)
    else:
        send_full_briefing(now_local, force_route_check, force_office_check)


if __name__ == "__main__":
    main()
