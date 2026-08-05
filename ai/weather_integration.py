"""Weather integration helper (Day 55 scaffold).

Provides a small wrapper that returns a short forecast series. If
`OPENWEATHER_API_KEY` is present in the environment, it will attempt
to fetch from OpenWeather (current/demo behavior otherwise).
"""
import os
from typing import List, Dict, Any
import datetime

try:
    import requests
except Exception:
    requests = None


def _demo_forecast(lat: float, lon: float) -> List[Dict[str, Any]]:
    now = datetime.datetime.utcnow()
    return [
        {"dt": (now + datetime.timedelta(hours=i)).isoformat(), "temp_c": 15 + i, "precip_mm": 0.0 if i % 3 else 1.2}
        for i in range(0, 12)
    ]


def get_forecast(lat: float, lon: float) -> List[Dict[str, Any]]:
    """Return a short forecast list for the given coordinates.

    Falls back to demo data when no provider or on error.
    """
    key = os.environ.get('OPENWEATHER_API_KEY')
    if key and requests:
        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={key}&units=metric"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            # Map to simple structure
            out = []
            for item in data.get('list', [])[:12]:
                out.append({
                    'dt': item.get('dt_txt') or item.get('dt'),
                    'temp_c': item.get('main', {}).get('temp'),
                    'precip_mm': sum([p.get('3h', 0) for p in [item.get('rain', {}), item.get('snow', {})] if p]) or 0.0,
                })
            return out
        except Exception:
            return _demo_forecast(lat, lon)

    return _demo_forecast(lat, lon)
