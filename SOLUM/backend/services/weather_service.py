import json
import time
import hashlib
from datetime import datetime, timezone
import httpx
from backend.config import settings

_CACHE = {}

def get_cached(key: str, ttl: int = settings.CACHE_DEFAULT_TTL):
    if key in _CACHE:
        timestamp, data = _CACHE[key]
        if time.monotonic() - timestamp < ttl:
            return dict(data, cached=True)
    return None

def set_cached(key: str, data: dict):
    if len(_CACHE) > 200:
        _CACHE.clear()
    _CACHE[key] = (time.monotonic(), data)

async def get_weather(lat: float, lon: float) -> dict:
    cache_key = f"weather_{round(lat, 3)}_{round(lon, 3)}"
    cached_val = get_cached(cache_key)
    if cached_val:
        return cached_val

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max,weather_code",
        "forecast_days": 7,
        "timezone": "auto"
    }

    url = "https://api.open-meteo.com/v1/forecast"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        raw_bytes = response.content
        data = response.json()

    if "daily" not in data or "current" not in data:
        raise ValueError("Incomplete forecast data returned by provider")

    data["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    data["receipt_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    data["cached"] = False

    set_cached(cache_key, data)
    return data
