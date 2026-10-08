"""Weather + agro-advisory.

Default provider is Open-Meteo because it needs no API key, which keeps the
one-command demo honest. WeatherAPI and OpenWeather are drop-in alternatives.
A deterministic seasonal model backs everything up when the network is down.
"""
import logging
import math
from datetime import date, datetime, timedelta

import httpx

from app.core.config import settings
from app.core.redis_client import get_redis

log = logging.getLogger(__name__)

CODE_MAP = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers", 81: "Rain showers",
    82: "Violent rain showers", 95: "Thunderstorm", 96: "Thunderstorm with hail",
    99: "Thunderstorm with hail",
}


def _synthetic(lat: float, lon: float) -> dict:
    """Seasonal climatology fallback - deterministic, never random."""
    today = date.today()
    doy = today.timetuple().tm_yday
    base = 27 + 6 * math.sin((doy - 100) / 365 * 2 * math.pi) - (abs(lat) - 17) * 0.35
    monsoon = 1 if 152 <= doy <= 273 else 0
    days = []
    for i in range(7):
        tmax = round(base + 4 - monsoon * 3 + (i % 3), 1)
        tmin = round(tmax - 9.5, 1)
        rain = round(max(0.0, (monsoon * 9) + (3 - abs(3 - i)) * monsoon * 2.5 - 1.5), 1)
        days.append(
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "tmax": tmax,
                "tmin": tmin,
                "rain_mm": rain,
                "rain_chance": min(95, int(rain * 8) + monsoon * 25),
                "humidity": 70 if monsoon else 45,
                "wind_kph": 9.0,
                "condition": "Rain" if rain > 2 else "Partly cloudy",
            }
        )
    return {
        "source": "seasonal-climatology (offline fallback)",
        "current": {
            "temp_c": days[0]["tmax"] - 2,
            "humidity": days[0]["humidity"],
            "wind_kph": days[0]["wind_kph"],
            "condition": days[0]["condition"],
            "rain_mm": days[0]["rain_mm"],
        },
        "daily": days,
    }


async def _open_meteo(lat: float, lon: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code,wind_speed_10m_max,relative_humidity_2m_mean",
        "forecast_days": 7,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url, params=params)
        r.raise_for_status()
        d = r.json()
    cur, dl = d["current"], d["daily"]
    days = [
        {
            "date": dl["time"][i],
            "tmax": dl["temperature_2m_max"][i],
            "tmin": dl["temperature_2m_min"][i],
            "rain_mm": dl["precipitation_sum"][i] or 0,
            "rain_chance": dl["precipitation_probability_max"][i] or 0,
            "humidity": (dl.get("relative_humidity_2m_mean") or [60] * 7)[i] or 60,
            "wind_kph": dl["wind_speed_10m_max"][i],
            "condition": CODE_MAP.get(dl["weather_code"][i], "Unknown"),
        }
        for i in range(len(dl["time"]))
    ]
    return {
        "source": "open-meteo",
        "current": {
            "temp_c": cur["temperature_2m"],
            "humidity": cur["relative_humidity_2m"],
            "wind_kph": cur["wind_speed_10m"],
            "condition": CODE_MAP.get(cur["weather_code"], "Unknown"),
            "rain_mm": cur["precipitation"],
        },
        "daily": days,
    }


def build_advisory(w: dict) -> list[dict]:
    """Turn a forecast into field decisions. This is the part farmers actually use."""
    days = w["daily"]
    out: list[dict] = []
    rain48 = sum(d["rain_mm"] for d in days[:2])
    rain7 = sum(d["rain_mm"] for d in days)
    tmax = max(d["tmax"] for d in days[:3])
    tmin = min(d["tmin"] for d in days[:3])
    wind = max(d["wind_kph"] for d in days[:2])
    humid = sum(d["humidity"] for d in days[:3]) / 3

    if rain48 >= 20:
        out.append({"kind": "irrigation", "level": "high", "title": "Skip irrigation",
                    "text": f"{rain48:.0f} mm of rain expected in 48 hours. Hold irrigation and check field drainage."})
    elif rain7 < 5 and tmax > 33:
        out.append({"kind": "irrigation", "level": "medium", "title": "Irrigate soon",
                    "text": "Dry and hot week ahead. Irrigate at the next critical stage and mulch to cut evaporation."})

    if rain48 >= 5 or wind > 15:
        out.append({"kind": "spray", "level": "high", "title": "Do not spray now",
                    "text": "Rain or wind in the next two days will wash off or drift the spray. Wait for a dry, calm morning."})
    else:
        clear = next((d["date"] for d in days if d["rain_mm"] < 1 and d["wind_kph"] < 12), None)
        if clear:
            out.append({"kind": "spray", "level": "low", "title": "Good spray window",
                        "text": f"{clear}: dry and calm. Spray between 6-9 am or after 4 pm."})

    if rain7 >= 25:
        out.append({"kind": "sowing", "level": "low", "title": "Sowing window opening",
                    "text": f"{rain7:.0f} mm expected this week - enough to wet the profile for sowing."})

    if humid > 80 and 20 <= tmax <= 30:
        out.append({"kind": "disease", "level": "high", "title": "Fungal disease risk",
                    "text": "Warm and very humid: blast, blight and downy mildew spread fast. Scout daily and spray preventively."})

    if tmin <= 4:
        out.append({"kind": "frost", "level": "high", "title": "Frost warning",
                    "text": "Night temperature near freezing. Irrigate in the evening and light smoke on the windward side."})
    if tmax >= 40:
        out.append({"kind": "heat", "level": "high", "title": "Heat stress",
                    "text": "Above 40 C. Give a light irrigation and spray 2% potassium nitrate at flowering."})

    if rain48 >= 10:
        out.append({"kind": "fertiliser", "level": "medium", "title": "Delay top dressing",
                    "text": "Urea applied before heavy rain is lost to runoff and leaching. Apply after the rain stops."})
    return out


async def forecast(lat: float, lon: float) -> dict:
    key = f"weather:{round(lat, 2)}:{round(lon, 2)}"
    r = get_redis()
    try:
        cached = await r.get(key)
        if cached:
            import json
            return json.loads(cached)
    except Exception:
        cached = None

    try:
        if settings.WEATHER_PROVIDER == "open-meteo":
            data = await _open_meteo(lat, lon)
        elif settings.WEATHER_PROVIDER == "weatherapi" and settings.WEATHERAPI_KEY:
            async with httpx.AsyncClient(timeout=15) as c:
                r2 = await c.get(
                    "https://api.weatherapi.com/v1/forecast.json",
                    params={"key": settings.WEATHERAPI_KEY, "q": f"{lat},{lon}", "days": 7, "aqi": "no"},
                )
                r2.raise_for_status()
                j = r2.json()
            data = {
                "source": "weatherapi",
                "current": {
                    "temp_c": j["current"]["temp_c"],
                    "humidity": j["current"]["humidity"],
                    "wind_kph": j["current"]["wind_kph"],
                    "condition": j["current"]["condition"]["text"],
                    "rain_mm": j["current"]["precip_mm"],
                },
                "daily": [
                    {
                        "date": d["date"],
                        "tmax": d["day"]["maxtemp_c"],
                        "tmin": d["day"]["mintemp_c"],
                        "rain_mm": d["day"]["totalprecip_mm"],
                        "rain_chance": d["day"]["daily_chance_of_rain"],
                        "humidity": d["day"]["avghumidity"],
                        "wind_kph": d["day"]["maxwind_kph"],
                        "condition": d["day"]["condition"]["text"],
                    }
                    for d in j["forecast"]["forecastday"]
                ],
            }
        else:
            data = _synthetic(lat, lon)
    except Exception as exc:
        log.warning("weather provider failed (%s); using climatology", exc)
        data = _synthetic(lat, lon)

    data["advisory"] = build_advisory(data)
    data["fetched_at"] = datetime.utcnow().isoformat()
    try:
        import json
        await r.setex(key, 1800, json.dumps(data))
    except Exception:
        pass
    return data
