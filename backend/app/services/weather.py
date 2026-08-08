from datetime import UTC, datetime
import httpx
from app.core.config import get_settings

async def fetch_weather(city: str, country_code: str) -> dict:
    settings = get_settings()
    if not settings.openweather_api_key:
        raise ValueError("OPENWEATHER_API_KEY is not configured")
    params = {"q": f"{city},{country_code}", "appid": settings.openweather_api_key, "units": "metric"}
    async with httpx.AsyncClient(timeout=15) as client:
        current = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params); current.raise_for_status()
        forecast = await client.get("https://api.openweathermap.org/data/2.5/forecast", params=params); forecast.raise_for_status()
    body, forecast_body = current.json(), forecast.json()
    daily = []
    seen = set()
    for slot in forecast_body.get("list", []):
        date = slot["dt_txt"][:10]
        if date not in seen:
            seen.add(date); daily.append({"date": date, "temperature": slot["main"]["temp"], "humidity": slot["main"]["humidity"], "rainfall_mm": slot.get("rain", {}).get("3h", 0), "description": slot["weather"][0]["description"]})
    return {"location": body["name"], "observed_at": datetime.now(UTC).isoformat(), "temperature": body["main"]["temp"], "humidity": body["main"]["humidity"], "pressure": body["main"]["pressure"], "wind_speed": body["wind"].get("speed", 0), "description": body["weather"][0]["description"], "forecast": daily[:7]}

def weather_advice(data: dict) -> list[str]:
    messages = []
    if data["humidity"] > 80: messages.append("High humidity increases fungal disease risk; improve canopy airflow and inspect leaves.")
    if data["wind_speed"] > 7: messages.append("Avoid pesticide spraying in strong wind to reduce drift.")
    if any(day["rainfall_mm"] > 2 for day in data.get("forecast", [])): messages.append("Rain is forecast: defer irrigation and protect harvested produce from moisture.")
    if not messages: messages.append("Conditions are suitable for planned field work; irrigate according to measured soil moisture.")
    return messages
