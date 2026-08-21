import os
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

LOCAL_TZ = ZoneInfo("Europe/London")

# Lewisham 經緯度 (51.4615, -0.0102)
LAT = 51.4615
LON = -0.0102


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


def send_telegram(msg):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        raise RuntimeError("TG_BOT_TOKEN / TG_CHAT_ID 未設定，請確認 repository secrets。")
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    res = requests.post(url, json=payload, timeout=10)
    if not res.ok:
        print(f"Telegram 傳送失敗: {res.status_code} {res.text}")
    res.raise_for_status()


def main():
    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d (%a)")
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
        f"• 降雨提醒: {rain_msg}\n\n"
        f"祝你有美好的一天！💪"
    )
    send_telegram(briefing)


if __name__ == "__main__":
    main()
