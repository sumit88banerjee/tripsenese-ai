import os
import time
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

CITY_COORDS = {
    "Jaipur": {"latitude": 26.9124, "longitude": 75.7873, "timezone": "Asia/Kolkata"},
    "Mumbai": {"latitude": 19.0760, "longitude": 72.8777, "timezone": "Asia/Kolkata"},
}

RISK_RANK = {"Low": 0, "Medium": 1, "High": 2}


def env_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def cache_is_fresh(cache_path: str, max_age_hours: int) -> bool:
    path = Path(cache_path)
    if not path.exists() or max_age_hours <= 0:
        return False
    return (time.time() - path.stat().st_mtime) < max_age_hours * 3600


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_forecast(city: str) -> dict:
    coords = CITY_COORDS[city]
    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "timezone": coords["timezone"],
        "forecast_days": 2,
        "current": "temperature_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,wind_gusts_10m",
        "hourly": "temperature_2m,apparent_temperature,precipitation,rain,showers,precipitation_probability,weather_code,wind_speed_10m,wind_gusts_10m,visibility",
    }
    response = requests.get(FORECAST_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_air_quality(city: str) -> dict:
    coords = CITY_COORDS[city]
    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "timezone": coords["timezone"],
        "forecast_days": 2,
        "hourly": "us_aqi,pm10,pm2_5,uv_index,uv_index_clear_sky",
    }
    response = requests.get(AIR_QUALITY_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def safe_values(values, n):
    return [(0 if v is None else v) for v in (values or [])[:n]]


def risk_from_threshold(value, medium, high, reverse=False):
    if value is None:
        return "Low"
    if reverse:
        if value <= high:
            return "High"
        if value <= medium:
            return "Medium"
        return "Low"
    if value >= high:
        return "High"
    if value >= medium:
        return "Medium"
    return "Low"


def max_risk(*risks):
    return max(risks, key=lambda r: RISK_RANK.get(r, 0))


def weather_code_storm_risk(codes):
    severe_codes = {95, 96, 99}
    if any(int(code or 0) in severe_codes for code in codes):
        return "High"
    return "Low"


def build_travel_advice(city, overall, rain, heat, wind, aq, uv, visibility):
    advice = []
    if rain == "High":
        advice.append("Avoid outdoor sightseeing, beaches, seafront walks, low-lying roads and long road transfers.")
    elif rain == "Medium":
        advice.append("Keep rain backup options and prefer nearby indoor places.")
    if heat == "High":
        advice.append("Avoid afternoon outdoor sightseeing; plan museums, malls and restaurants from 12 PM to 4 PM.")
    elif heat == "Medium":
        advice.append("Prefer morning and evening sightseeing; carry water and sun protection.")
    if wind == "High":
        advice.append("Avoid exposed viewpoints, boating, beaches and sea-facing walks.")
    elif wind == "Medium":
        advice.append("Use caution for open-air and elevated places.")
    if aq == "High":
        advice.append("Air quality is poor; reduce outdoor walking and prefer indoor activities.")
    elif aq == "Medium":
        advice.append("Sensitive travellers should reduce long outdoor exposure.")
    if uv == "High":
        advice.append("UV is high; use sunscreen, hat and avoid peak sun hours.")
    elif uv == "Medium":
        advice.append("Use basic sun protection for outdoor plans.")
    if visibility == "High":
        advice.append("Visibility is poor; avoid long drives and viewpoints.")
    elif visibility == "Medium":
        advice.append("Check visibility before long drives or viewpoints.")
    if not advice:
        return "No major weather, air quality, UV or visibility risk detected."
    return " ".join(advice)


def summarize_weather_risk(city: str, forecast: dict, air_quality: dict) -> dict:
    lookahead_hours = env_int("WEATHER_LOOKAHEAD_HOURS", 12)
    hourly = forecast.get("hourly", {})
    aq_hourly = air_quality.get("hourly", {})

    precipitation = safe_values(hourly.get("precipitation"), lookahead_hours)
    rain = safe_values(hourly.get("rain"), lookahead_hours)
    showers = safe_values(hourly.get("showers"), lookahead_hours)
    rain_probability = safe_values(hourly.get("precipitation_probability"), lookahead_hours)
    apparent_temp = safe_values(hourly.get("apparent_temperature"), lookahead_hours)
    wind_gusts = safe_values(hourly.get("wind_gusts_10m"), lookahead_hours)
    wind_speed = safe_values(hourly.get("wind_speed_10m"), lookahead_hours)
    visibility = safe_values(hourly.get("visibility"), lookahead_hours)
    weather_codes = safe_values(hourly.get("weather_code"), lookahead_hours)

    us_aqi = safe_values(aq_hourly.get("us_aqi"), lookahead_hours)
    pm25 = safe_values(aq_hourly.get("pm2_5"), lookahead_hours)
    pm10 = safe_values(aq_hourly.get("pm10"), lookahead_hours)
    uv_index = safe_values(aq_hourly.get("uv_index"), lookahead_hours)

    rain_mm = max(sum(precipitation), sum(rain) + sum(showers))
    max_rain_probability = max(rain_probability, default=0)
    max_apparent_temp = max(apparent_temp, default=0)
    max_wind_gust = max(wind_gusts or wind_speed, default=0)
    min_visibility = min([v for v in visibility if v is not None], default=99999)
    max_us_aqi = max(us_aqi, default=0)
    max_pm25 = max(pm25, default=0)
    max_pm10 = max(pm10, default=0)
    max_uv = max(uv_index, default=0)

    rain_risk = max_risk(
        risk_from_threshold(rain_mm, env_float("RAIN_MM_12H_MEDIUM", 10), env_float("RAIN_MM_12H_HIGH", 30)),
        risk_from_threshold(max_rain_probability, env_float("RAIN_PROB_MEDIUM", 60), env_float("RAIN_PROB_HIGH", 80)),
    )
    heat_risk = risk_from_threshold(max_apparent_temp, env_float("TEMP_C_MEDIUM", 35), env_float("TEMP_C_HIGH", 40))
    wind_risk = max_risk(
        risk_from_threshold(max_wind_gust, env_float("WIND_KMPH_MEDIUM", 35), env_float("WIND_KMPH_HIGH", 50)),
        weather_code_storm_risk(weather_codes),
    )
    air_quality_risk = max_risk(
        risk_from_threshold(max_us_aqi, env_float("US_AQI_MEDIUM", 101), env_float("US_AQI_HIGH", 151)),
        risk_from_threshold(max_pm25, env_float("PM25_MEDIUM", 35), env_float("PM25_HIGH", 55)),
    )
    uv_risk = risk_from_threshold(max_uv, env_float("UV_INDEX_MEDIUM", 6), env_float("UV_INDEX_HIGH", 8))
    visibility_risk = risk_from_threshold(min_visibility, env_float("VISIBILITY_M_MEDIUM", 3000), env_float("VISIBILITY_M_HIGH", 1000), reverse=True)

    overall = max_risk(rain_risk, heat_risk, wind_risk, air_quality_risk, uv_risk, visibility_risk)
    risk_labels = []
    for label, risk in [("Heavy rain", rain_risk), ("Heat", heat_risk), ("Wind/storm", wind_risk), ("Air quality", air_quality_risk), ("UV", uv_risk), ("Poor visibility", visibility_risk)]:
        if risk in ["Medium", "High"]:
            risk_labels.append(f"{label} ({risk})")
    advice = build_travel_advice(city, overall, rain_risk, heat_risk, wind_risk, air_quality_risk, uv_risk, visibility_risk)

    return {
        "city": city,
        "weather_risk_level": overall,
        "primary_weather_risk": ", ".join(risk_labels) if risk_labels else "None",
        "lookahead_hours": lookahead_hours,
        "rain_risk_level": rain_risk,
        "heat_risk_level": heat_risk,
        "wind_risk_level": wind_risk,
        "air_quality_risk_level": air_quality_risk,
        "uv_risk_level": uv_risk,
        "visibility_risk_level": visibility_risk,
        "rain_mm_next_window": round(float(rain_mm), 2),
        "max_rain_probability": int(max_rain_probability),
        "max_apparent_temperature_c": round(float(max_apparent_temp), 2),
        "max_wind_gust_kmph": round(float(max_wind_gust), 2),
        "max_us_aqi": int(max_us_aqi),
        "max_pm25": round(float(max_pm25), 2),
        "max_pm10": round(float(max_pm10), 2),
        "max_uv_index": round(float(max_uv), 2),
        "min_visibility_m": int(min_visibility),
        "travel_advice": advice,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def get_weather_summary(city: str) -> dict:
    cache_hours = env_int("WEATHER_CACHE_HOURS", 3)
    slug = city.lower().replace(" ", "_")
    forecast_cache = f"data/raw/weather/{slug}_forecast_open_meteo.json"
    aq_cache = f"data/raw/weather/{slug}_air_quality_open_meteo.json"

    if cache_is_fresh(forecast_cache, cache_hours):
        forecast = load_json(forecast_cache)
    else:
        forecast = fetch_forecast(city)
        save_json(forecast_cache, forecast)

    if cache_is_fresh(aq_cache, cache_hours):
        air_quality = load_json(aq_cache)
    else:
        air_quality = fetch_air_quality(city)
        save_json(aq_cache, air_quality)

    return summarize_weather_risk(city, forecast, air_quality)


def build_weather_summary_for_cities(cities: list[str]) -> pd.DataFrame:
    rows = []
    for city in cities:
        print(f"Building advanced weather risk for {city}")
        rows.append(get_weather_summary(city))
    return pd.DataFrame(rows)
