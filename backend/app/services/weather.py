from datetime import UTC, datetime
import httpx
from app.core.config import get_settings

OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _weather_description(code: int | None) -> str:
    descriptions = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Freezing rain",
        67: "Heavy freezing rain", 71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
        82: "Violent rain showers", 85: "Snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Weather conditions available")


async def _fetch_open_meteo(city: str, country_code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        place_response = await client.get(OPEN_METEO_GEOCODING_URL, params={"name": city, "countryCode": country_code.upper(), "count": 1, "language": "en", "format": "json"})
        place_response.raise_for_status()
        places = place_response.json().get("results", [])
        if not places:
            raise ValueError("City not found. Check the city and country code.")
        place = places[0]
        response = await client.get(OPEN_METEO_FORECAST_URL, params={
            "latitude": place["latitude"], "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,weather_code",
            "hourly": "relative_humidity_2m",
            "daily": "temperature_2m_mean,precipitation_sum,weather_code",
            "wind_speed_unit": "ms", "timezone": "auto", "forecast_days": 7,
        })
        response.raise_for_status()
    body = response.json()
    current, daily_body, hourly_body = body["current"], body["daily"], body["hourly"]
    daily = []
    for index, date in enumerate(daily_body.get("time", [])):
        humidity_samples = [value for hour, value in zip(hourly_body["time"], hourly_body["relative_humidity_2m"]) if hour.startswith(date) and value is not None]
        daily.append({
            "date": date,
            "temperature": daily_body["temperature_2m_mean"][index],
            "humidity": round(sum(humidity_samples) / len(humidity_samples)) if humidity_samples else current["relative_humidity_2m"],
            "rainfall_mm": daily_body["precipitation_sum"][index] or 0,
            "description": _weather_description(daily_body["weather_code"][index]),
        })
    location_parts = [place.get("name"), place.get("admin1"), place.get("country")]
    return {
        "location": ", ".join(dict.fromkeys(part for part in location_parts if part)),
        "observed_at": current.get("time", datetime.now(UTC).isoformat()),
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "pressure": current["pressure_msl"],
        "wind_speed": current["wind_speed_10m"],
        "description": _weather_description(current.get("weather_code")),
        "forecast": daily,
        "provider": "Open-Meteo",
        "attribution_url": "https://open-meteo.com/",
    }


async def fetch_weather(city: str, country_code: str) -> dict:
    settings = get_settings()
    if not settings.openweather_api_key:
        return await _fetch_open_meteo(city, country_code)
    params = {"q": f"{city},{country_code}", "appid": settings.openweather_api_key, "units": "metric"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            current = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params); current.raise_for_status()
            forecast = await client.get("https://api.openweathermap.org/data/2.5/forecast", params=params); forecast.raise_for_status()
    except httpx.HTTPError:
        return await _fetch_open_meteo(city, country_code)
    body, forecast_body = current.json(), forecast.json()
    daily = []
    seen = set()
    for slot in forecast_body.get("list", []):
        date = slot["dt_txt"][:10]
        if date not in seen:
            seen.add(date); daily.append({"date": date, "temperature": slot["main"]["temp"], "humidity": slot["main"]["humidity"], "rainfall_mm": slot.get("rain", {}).get("3h", 0), "description": slot["weather"][0]["description"]})
    return {"location": body["name"], "observed_at": datetime.now(UTC).isoformat(), "temperature": body["main"]["temp"], "humidity": body["main"]["humidity"], "pressure": body["main"]["pressure"], "wind_speed": body["wind"].get("speed", 0), "description": body["weather"][0]["description"], "forecast": daily[:7], "provider": "OpenWeather", "attribution_url": "https://openweathermap.org/"}

def weather_advice(data: dict) -> list[str]:
    messages = []
    if data["humidity"] > 80: messages.append("High humidity increases fungal disease risk; improve canopy airflow and inspect leaves.")
    if data["wind_speed"] > 7: messages.append("Avoid pesticide spraying in strong wind to reduce drift.")
    if any(day["rainfall_mm"] > 2 for day in data.get("forecast", [])): messages.append("Rain is forecast: defer irrigation and protect harvested produce from moisture.")
    if not messages: messages.append("Conditions are suitable for planned field work; irrigate according to measured soil moisture.")
    return messages
