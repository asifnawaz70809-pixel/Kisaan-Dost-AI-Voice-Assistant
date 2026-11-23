import re
import json
import socket
import requests
import streamlit as st
from datetime import datetime

_orig_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = lambda host, port, family=0, type=0, proto=0, flags=0: _orig_getaddrinfo(
    host, port, family, type, proto, flags
)


class SafeDict(dict):
    def __missing__(self, key):
        return self.get("message") or self.get("title") or self.get("day_name") or ""


PK_CITY_COORDS = {
    "karak": (33.1163, 71.0935, "Karak", "Khyber Pakhtunkhwa"),
    "peshawar": (34.0151, 71.5249, "Peshawar", "Khyber Pakhtunkhwa"),
    "kohat": (33.5889, 71.4429, "Kohat", "Khyber Pakhtunkhwa"),
    "bannu": (32.9889, 70.6056, "Bannu", "Khyber Pakhtunkhwa"),
    "mardan": (34.1986, 72.0404, "Mardan", "Khyber Pakhtunkhwa"),
    "swat": (35.2227, 72.4258, "Swat", "Khyber Pakhtunkhwa"),
    "islamabad": (33.6844, 73.0479, "Islamabad", "Islamabad"),
    "rawalpindi": (33.5651, 73.0169, "Rawalpindi", "Punjab"),
    "lahore": (31.5204, 74.3587, "Lahore", "Punjab"),
    "faisalabad": (31.4504, 73.1350, "Faisalabad", "Punjab"),
    "multan": (30.1575, 71.5249, "Multan", "Punjab"),
    "bahawalpur": (29.3956, 71.6836, "Bahawalpur", "Punjab"),
    "sargodha": (32.0836, 72.6711, "Sargodha", "Punjab"),
    "gujranwala": (32.1877, 74.1945, "Gujranwala", "Punjab"),
    "sahiwal": (30.6682, 73.1114, "Sahiwal", "Punjab"),
    "karachi": (24.8607, 67.0011, "Karachi", "Sindh"),
    "hyderabad": (25.3960, 68.3578, "Hyderabad", "Sindh"),
    "sukkur": (27.7052, 68.8574, "Sukkur", "Sindh"),
    "quetta": (30.1798, 66.9750, "Quetta", "Balochistan"),
}

URDU_DAYS = {
    "Monday": "Peer",
    "Tuesday": "Mangal",
    "Wednesday": "Budh",
    "Thursday": "Jumerat",
    "Friday": "Jummah",
    "Saturday": "Hafta",
    "Sunday": "Itwar",
}

WMO_CONDITIONS = {
    0: ("Clear", "Saaf Aasman", "\u2600\ufe0f"),
    1: ("Mostly Clear", "Zyada Tar Saaf", "\U0001f324\ufe0f"),
    2: ("Partly Cloudy", "Halkay Badal", "\u26c5"),
    3: ("Overcast", "Ghanay Badal", "\u2601\ufe0f"),
    45: ("Foggy", "Dhund", "\U0001f32b\ufe0f"),
    48: ("Dense Fog", "Gehri Dhund", "\U0001f32b\ufe0f"),
    51: ("Light Drizzle", "Halki Boonda Bandi", "\U0001f326\ufe0f"),
    53: ("Moderate Drizzle", "Boonda Bandi", "\U0001f326\ufe0f"),
    61: ("Slight Rain", "Halki Barish", "\U0001f327\ufe0f"),
    63: ("Moderate Rain", "Barish", "\U0001f327\ufe0f"),
    65: ("Heavy Rain", "Tez Barish", "\u26c8\ufe0f"),
    80: ("Rain Showers", "Barish Ke Jhonkay", "\U0001f327\ufe0f"),
    95: ("Thunderstorm", "Aandhi Aur Bijli", "\u26c8\ufe0f"),
}


def _map_text_condition(desc: str):
    d = (desc or "").lower()
    if "thunder" in d:
        return ("Thunderstorm", "Aandhi Aur Bijli", "\u26c8\ufe0f")
    if "heavy rain" in d:
        return ("Heavy Rain", "Tez Barish", "\u26c8\ufe0f")
    if "rain" in d or "shower" in d or "drizzle" in d:
        return ("Rain", "Barish", "\U0001f327\ufe0f")
    if "fog" in d or "mist" in d or "haze" in d or "smoke" in d:
        return ("Haze / Fog", "Dhund / Gard", "\U0001f32b\ufe0f")
    if "overcast" in d:
        return ("Overcast", "Ghanay Badal", "\u2601\ufe0f")
    if "partly" in d or "cloud" in d:
        return ("Partly Cloudy", "Halkay Badal", "\u26c5")
    return ("Clear", "Saaf Aasman", "\u2600\ufe0f")


def _fetch_msn_bing_weather(lat: float, lon: float, city_name: str):
    """
    Fetches live MSN / Bing Weather API data (same Foreca/Weather.com commercial feed
    used by Google & Windows Weather).
    """
    try:
        url = "https://api.msn.com/weather/overview"
        params = {
            "apikey": "OkWqH0GAh1X2171222414436",
            "version": "1.0",
            "lat": lat,
            "lon": lon,
            "units": "C",
            "locale": "en-us",
            "appId": "9e21380c-ff19-4c78-b4ea-19558e93a5d3",
        }
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=6,
        )
        if r.status_code == 200:
            data = r.json()
            cur = (((data.get("responses") or [{}])[0].get("weather") or [{}])[0]).get("current") or {}
            if cur.get("temp") is not None:
                return {
                    "temp": int(round(float(cur["temp"]))),
                    "feels_like": int(round(float(cur.get("feels", cur["temp"])))),
                    "humidity": int(round(float(cur.get("rh", 41)))),
                    "wind_kmh": int(round(float(cur.get("windSpd", 3)))),
                    "condition": str(cur.get("cap", "Clear")),
                }
    except Exception:
        pass
    return None


def _fetch_metno_weather(lat: float, lon: float):
    """
    Secondary precision meteorological feed (Norwegian Met Institute / ECMWF)
    with exact nearest-hour observation.
    """
    try:
        r = requests.get(
            "https://api.met.no/weatherapi/locationforecast/2.0/compact",
            params={"lat": round(lat, 4), "lon": round(lon, 4)},
            headers={"User-Agent": "KisaanDostFYP/1.0 github.com/asifnawaz"},
            timeout=6,
        )
        if r.status_code == 200:
            ts = r.json().get("properties", {}).get("timeseries") or []
            if ts:
                inst = ts[0].get("data", {}).get("instant", {}).get("details", {})
                sym = ts[0].get("data", {}).get("next_1_hours", {}).get("summary", {}).get("symbol_code", "clearsky")
                t_val = inst.get("air_temperature")
                if t_val is not None:
                    return {
                        "temp": int(round(float(t_val))),
                        "feels_like": int(round(float(t_val))),
                        "humidity": int(round(float(inst.get("relative_humidity", 41)))),
                        "wind_kmh": int(round(float(inst.get("wind_speed", 1.0)) * 3.6)),
                        "condition": sym.replace("_", " ").title(),
                    }
    except Exception:
        pass
    return None


def _resolve_city(city_name: str):
    clean = (city_name or "Karak").strip()
    key = clean.lower().split(",")[0].strip()
    if key in PK_CITY_COORDS:
        return PK_CITY_COORDS[key]

    try:
        res = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": key, "count": 5, "language": "en", "format": "json"},
            timeout=6,
        ).json()
        results = res.get("results") or []
        pk_matches = [r for r in results if str(r.get("country_code", "")).upper() == "PK"]
        chosen = pk_matches[0] if pk_matches else (results[0] if results else None)
        if chosen:
            return (
                float(chosen["latitude"]),
                float(chosen["longitude"]),
                chosen.get("name", clean.title()),
                chosen.get("admin1", "Pakistan"),
            )
    except Exception:
        pass
    return (33.1163, 71.0935, clean.title(), "Pakistan")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_weather_bundle(city_name: str = "Karak", api_key: str = "") -> dict:
    try:
        lat, lon, clean_city, admin1 = _resolve_city(city_name)

        # Primary: Commercial MSN/Foreca feed (matches Google Weather) -> Secondary: Met.no -> Fallback: Open-Meteo
        live_obs = _fetch_msn_bing_weather(lat, lon, clean_city) or _fetch_metno_weather(lat, lon)

        om_res = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,surface_pressure",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
                "wind_speed_unit": "kmh",
                "timezone": "Asia/Karachi",
                "forecast_days": 5,
            },
            timeout=8,
        ).json()

        cur = om_res.get("current", {})
        daily = om_res.get("daily", {})

        om_temp = int(round(float(cur.get("temperature_2m", 18))))
        om_feels = int(round(float(cur.get("apparent_temperature", om_temp))))
        om_hum = int(round(float(cur.get("relative_humidity_2m", 41))))
        om_wind = int(round(float(cur.get("wind_speed_10m", 3))))
        pressure = int(round(float(cur.get("surface_pressure", 1013))))
        wcode = int(cur.get("weather_code", 0))
        cond_en, cond_ur, emoji = WMO_CONDITIONS.get(wcode, ("Clear", "Saaf Aasman", "\u2600\ufe0f"))

        if live_obs:
            temp_c = live_obs["temp"]
            feels_like = live_obs["feels_like"]
            humidity = live_obs["humidity"]
            wind_kmh = live_obs["wind_kmh"]
            if live_obs.get("condition"):
                cond_en, cond_ur, emoji = _map_text_condition(live_obs["condition"])
        else:
            temp_c = om_temp
            feels_like = om_feels
            humidity = om_hum
            wind_kmh = om_wind

        rain_mm = float(cur.get("rain", 0) or cur.get("precipitation", 0))
        dates = daily.get("time") or []
        max_t = daily.get("temperature_2m_max") or []
        min_t = daily.get("temperature_2m_min") or []
        rain_p = daily.get("precipitation_probability_max") or []
        wind_m = daily.get("wind_speed_10m_max") or []
        wcodes = daily.get("weather_code") or []

        rain_prob_today = int(rain_p[0] or 0) if rain_p else 0
        temp_max_today = int(round(float(max_t[0]))) if max_t else temp_c
        temp_min_today = int(round(float(min_t[0]))) if min_t else temp_c

        forecast_days = []
        for i in range(len(dates)):
            c_en, c_ur, ico = WMO_CONDITIONS.get(int(wcodes[i]), ("Partly Cloudy", "Halkay Badal", "\U0001f324\ufe0f"))
            t_hi = int(round(float(max_t[i])))
            t_lo = int(round(float(min_t[i])))
            rp = int(rain_p[i] or 0)
            wm = int(round(float(wind_m[i] or 0)))
            try:
                dt_obj = datetime.strptime(dates[i], "%Y-%m-%d")
                eng_day = dt_obj.strftime("%A")
                day_label = "Aaj" if i == 0 else ("Kal" if i == 1 else URDU_DAYS.get(eng_day, eng_day))
                short_date = dt_obj.strftime("%d %b")
            except Exception:
                day_label = dates[i]
                short_date = dates[i]

            forecast_days.append(SafeDict({
                "date": short_date,
                "day_name": day_label,
                "max_temp": t_hi,
                "min_temp": t_lo,
                "temp_max": t_hi,
                "temp_min": t_lo,
                "rain_prob": rp,
                "wind_kmh": wm,
                "condition": c_en,
                "urdu_condition": c_ur,
                "emoji": ico,
            }))

        if rain_mm > 0.2 or rain_prob_today >= 50 or "Rain" in cond_en or "Thunder" in cond_en:
            level = "danger"
            badge = "\u26a0\ufe0f SPRAY BAND RAKHEIN"
            action_tag = "DO NOT SPRAY"
            headline = f"Barish ka imkaan ({rain_prob_today}%) hai - aaj spray bilkul na karein!"
            tips = [
                "Barish ki wajah se spray ki hui dawai patton se dhul kar zaya ho jayegi.",
                "Mausam saaf hone aur patton ke khushk hone tak intezar karein.",
                "Kheton mein izafi pani ki nikasi (drainage) ka intezam rakhein.",
            ]
            safe_to_spray = False
        elif wind_kmh > 18:
            level = "warning"
            badge = "\U0001f4a8 TEZ HAWA ALERT"
            action_tag = "AVOID SPRAY"
            headline = f"Hawa tez ({wind_kmh} km/h) chal rahi hai - spray mein ehtiyat karein."
            tips = [
                "Tez hawa mein spray ki dawai ur kar zaya hoti hai aur saath wali fasal ko nuqsan deti hai.",
                "Subah sawere ya shaam ko jab hawa kam ho tab 100-120 liter pani fi acre ke sath spray karein.",
                "Nai lagai gayi faslon ko halka pani lagayein taake nami barqarar rahe.",
            ]
            safe_to_spray = False
        else:
            level = "safe"
            badge = "\u2705 SPRAY KE LIYE BEHTAREEN"
            action_tag = "SAFE TO SPRAY"
            headline = "Mausam saaf aur hawa munasib hai - aap aaj spray aur khaad daal sakte hain."
            tips = [
                "Subah 7 se 10 baje ya shaam 4 baje ke baad 100-120 liter pani fi acre (5-6 tanks) ke sath spray karein.",
                "Urea ya DAP khaad daalne ke baad halka pani lagana fasal ke liye mufeed rahega.",
                "Fasal ke nichlay patton ka muaina karte rahein taake kisi bhi bimari ka waqt par ilaj ho sake.",
            ]
            safe_to_spray = True

        current_block = SafeDict({
            "city": clean_city,
            "country": "Pakistan",
            "temp": temp_c,
            "feels_like": feels_like,
            "max_temp": temp_max_today,
            "min_temp": temp_min_today,
            "humidity": humidity,
            "wind_kmh": wind_kmh,
            "rain_prob": rain_prob_today,
            "pressure": pressure,
            "visibility": 10,
            "condition": cond_en,
            "urdu_condition": cond_ur,
            "emoji": emoji,
        })

        advice_block = SafeDict({
            "level": level,
            "badge": badge,
            "action_tag": action_tag,
            "headline": headline,
            "message": headline,
            "tips": tips,
            "safe_to_spray": safe_to_spray,
        })

        return SafeDict({
            "success": True,
            "city": clean_city,
            "country": "Pakistan",
            "region": f"{clean_city}, {admin1}",
            "current": current_block,
            "forecast": forecast_days,
            "advice": advice_block,
        })
    except Exception as e:
        return SafeDict({
            "success": False,
            "error": f"Live weather fetch error: {str(e)}",
            "city": city_name,
            "country": "Pakistan",
        })


get_weather = fetch_weather_bundle
fetch_weather = fetch_weather_bundle
get_live_weather = fetch_weather_bundle
